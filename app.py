import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Kelp Safe Vault - Security Dashboard", layout="wide")

st.title("🛡️ Kelp Safe Vault - Security Dashboard")
st.markdown("Monitoramento em tempo real do contrato SafeVault.")

# Dados de exemplo (Fallback garantido)
SAMPLE_DATA = [
    {
        "timestamp": "2026-04-23T23:30:00",
        "block": 10719283,
        "tx_hash": "0xc0b040895e5ccd63c31f6a7201f1679819d8e48d04c14991f20496a226b402c5",
        "risk_score": 0.0,
        "reasons": [],
        "action_taken": "ALERTED"
    },
    {
        "timestamp": "2026-04-23T23:32:00",
        "block": 10719285,
        "tx_hash": "0x543e917c9bdfd6c6e224e91c3737d5b324db129f798f5542a676b837e0b42704",
        "risk_score": 0.6,
        "reasons": ["Withdraw pattern detected"],
        "action_taken": "ALERTED"
    }
]

alerts = SAMPLE_DATA

# Tenta ler arquivo externo se existir (na raiz)
alerts_file = "critical_alerts.json"
if os.path.exists(alerts_file):
    try:
        with open(alerts_file, "r") as f:
            content = f.read().strip()
            if content:
                if content.startswith('['):
                    loaded = json.loads(content)
                    if isinstance(loaded, list) and len(loaded) > 0:
                        alerts = loaded
    except Exception as e:
        st.warning(f"Erro ao ler arquivo de dados: {e}. Usando dados de exemplo.")

# Métricas
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total de Alertas", len(alerts))
with col2:
    critical_count = sum(1 for a in alerts if a.get('risk_score', 0) > 0.8)
    st.metric("Críticos (Risk > 0.8)", critical_count)
with col3:
    st.metric("Status do Contrato", "PAUSED" if critical_count > 0 else "ACTIVE")

# Gráfico e Tabela
if alerts:
    df = pd.DataFrame(alerts)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    st.subheader("📈 Evolução do Risco")
    st.line_chart(df.set_index('timestamp')['risk_score'])

    st.subheader("🚨 Últimos Alertas")
    st.dataframe(df[['timestamp', 'tx_hash', 'risk_score', 'reasons', 'action_taken']].sort_values(by='timestamp', ascending=False))
else:
    st.info("Nenhum alerta registrado ainda. O agente está monitorando...")

if st.button("Atualizar Dados"):
    st.rerun()

st.markdown("---")
st.caption("Desenvolvido para kelp-safe-vault.")
