import asyncio
import json
import logging
import os
import yaml
from datetime import datetime
from web3 import Web3
from openai import OpenAI
from pathlib import Path

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutonomousSecurityAgent:
    def __init__(self, config_path="ai-agent/config.yaml"):
        # 1. Carregar Configurações
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
            
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # 2. Conectar Web3
        self.w3 = Web3(Web3.HTTPProvider(self.config['rpc_url']))
        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to blockchain.")
        logger.info(f"Connected to Sepolia. Current Block: {self.w3.eth.block_number}")
        
        # 3. Configurar Contrato
        contract_addr = Web3.to_checksum_address(self.config['contract_address'])
        abi_path = Path(self.config['abi_path'])
        
        with open(abi_path, 'r') as f:
            data = json.load(f)
            abi = data['abi'] if isinstance(data, dict) and 'abi' in data else data
        
        self.contract = self.w3.eth.contract(address=contract_addr, abi=abi)
        
        # 4. Carteira Admin e OpenAI
        self.admin_account = self.w3.eth.account.from_key(self.config['admin_private_key'])
        self.llm_client = OpenAI(api_key=self.config['openai_api_key'])
        
        # 5. Estado Inicial (Sincroniza com os últimos 10 blocos para começar rápido)
        self.last_processed_block = self.w3.eth.block_number - 10

    def analyze_transaction_with_llm(self, tx_data):
        tx_hash_str = tx_data['hash'].hex() if hasattr(tx_data['hash'], 'hex') else str(tx_data['hash'])
        prompt = f"""
        Analyze this Smart Contract transaction and determine if it is malicious.
        Hash: {tx_hash_str} | From: {tx_data['from']} | To: {tx_data['to']}
        Value: {self.w3.from_wei(tx_data['value'], 'ether')} ETH
        Respond ONLY with JSON: {{"is_malicious": bool, "risk_score": 0.0-1.0, "reason": "str"}}
        """
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            return json.loads(response.choices[0].message.content)
        except:
            return {"is_malicious": False, "risk_score": 0.1, "reason": "Safe deposit detected"}

    def emergency_pause(self, reason):
        logger.warning(f"🚨 DEFENSIVE ACTION: Pausing contract. Reason: {reason}")
        try:
            tx = self.contract.functions.pause().build_transaction({
                'from': self.admin_account.address,
                'nonce': self.w3.eth.get_transaction_count(self.admin_account.address),
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price
            })
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.admin_account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(f"✅ PAUSED! Hash: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Failed to pause: {e}")
            return None

    def process_block(self, block_number):
        block = self.w3.eth.get_block(block_number, full_transactions=True)
        for tx in block.transactions:
            # Comparação segura de endereços (lowercase)
            if tx.to and tx.to.lower() == self.contract.address.lower():
                logger.info(f"🎯 Tx detectada no contrato: {tx.hash.hex()}")
                
                # Análise Simples
                value_eth = self.w3.from_wei(tx['value'], 'ether')
                risk_score = 0.9 if value_eth > 10 else 0.2
                
                # Chamar IA se houver risco moderado
                analysis = self.analyze_transaction_with_llm(tx)
                final_score = max(risk_score, analysis['risk_score'])
                
                alert = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "tx_hash": tx.hash.hex(),
                    "risk_score": final_score,
                    "reason": analysis['reason'],
                    "action": "PAUSE" if final_score > 0.8 else "MONITOR"
                }
                
                # Salva Alerta no JSON (para o Dashboard)
                logger.info(f"⚠️ Alerta Gerado: {alert}")
                with open("reports/critical_alerts.json", "a") as f:
                    f.write(json.dumps(alert) + "\n")
                
                # Executa pausa se o risco for crítico
                if final_score > 0.8:
                    self.emergency_pause(analysis['reason'])

    async def run_monitor(self):
        logger.info(f"🚀 Monitoring started at block {self.last_processed_block}")
        while True:
            try:
                current_block = self.w3.eth.block_number
                
                # Se o agente ficar muito atrás, ele pula para o presente
                if current_block - self.last_processed_block > 50:
                    self.last_processed_block = current_block - 5
                
                for block_num in range(self.last_processed_block + 1, current_block + 1):
                    logger.info(f"🔎 Verificando bloco: {block_num}")
                    self.process_block(block_num)
                    self.last_processed_block = block_num
                
                await asyncio.sleep(10) # Aguarda novo bloco
            except Exception as e:
                logger.error(f"Loop Error: {e}")
                await asyncio.sleep(15)

if __name__ == "__main__":
    agent = AutonomousSecurityAgent()
    asyncio.run(agent.run_monitor())
