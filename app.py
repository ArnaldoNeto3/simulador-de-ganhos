import streamlit as st
import pandas as pd
from datetime import datetime
import json
from upstash_redis import Redis

# Configuração da página
st.set_page_config(page_title='Simulador de Ganhos', page_icon='🚗')
st.title('🚗 Simulador de Ganhos')

# --- CONEXÃO COM O BANCO DE DADOS (UPSTASH) ---
@st.cache_resource
def get_database():
    return Redis(url=st.secrets["UPSTASH_URL"], token=st.secrets["UPSTASH_TOKEN"])

db = get_database()

# Estrutura padrão das colunas
colunas = [
    'Data', 'Valor', 'Coleta_km', 'Entrega_km', 'Km_Total', 'Tempo_min', 
    'Gasolina', 'Consumo', 'Observacao', 'Combustivel', 'Gasto_Total', 
    'Lucro', 'Receita_km', 'Custo_km', 'Lucro_km', 'Ganho_hora', 'Margem', 'Classificacao'
]

# Tenta ler os dados salvos na nuvem
try:
    dados_salvos = db.get("historico_corridas")
    if dados_salvos and dados_salvos != "[]":
        df = pd.DataFrame(json.loads(dados_salvos))
    else:
        df = pd.DataFrame(columns=colunas)
except:
    df = pd.DataFrame(columns=colunas)

# --- BARRA LATERAL (CONFIGURAÇÕES GLOBAIS) ---
with st.sidebar:
    st.header('Configurações')
    consumo = st.number_input('Consumo (km/L)', 1.0, 50.0, 12.0)
    gasolina = st.number_input('Gasolina (R$/L)', 0.0, 20.0, 6.20)

# --- CORPO PRINCIPAL (DADOS DA CORRIDA) ---
st.subheader("Nova Corrida")

col1, col2 = st.columns(2)

with col1:
    valor = st.number_input('Valor (R$)', min_value=0.0, value=None, placeholder="Ex: 25.50")
    coleta = st.number_input('Km até coleta', min_value=0.0, value=None, placeholder="Ex: 2.5")

with col2:
    entrega = st.number_input('Km entrega', min_value=0.0, value=None, placeholder="Ex: 10.0")
    tempo = st.number_input('Tempo (min)', min_value=1, value=None, placeholder="Ex: 30")

obs = st.text_input('Observação (Opcional)')

if st.button('Analisar e Salvar', use_container_width=True):
    
    if valor is None or coleta is None or entrega is None or tempo is None:
        st.warning("⚠️ Preencha os campos de Valor, Coleta, Entrega e Tempo antes de analisar.")
    else:
        km = coleta + entrega
        comb = (km / consumo) * gasolina
        gasto = comb 
        lucro = valor - gasto
        
        rec_km = valor / km if km else 0
        cus_km = gasto / km if km else 0
        luc_km = lucro / km if km else 0
        ganho_h = lucro / (tempo / 60) if tempo else 0
        margem = (lucro / valor * 100) if valor else 0
        
        if luc_km >= 1.8: c = '🟢 Excelente'
        elif luc_km >= 1.5: c = '🟢 Muito boa'
        elif luc_km >= 1.2: c = '🟡 Boa'
        elif luc_km >= 0.9: c = '🟠 Regular'
        else: c = '🔴 Não compensa'
        
        st.success(f"Veredito: {c}")
        
        resumo1, resumo2, resumo3 = st.columns(3)
        resumo1.metric("Lucro Líquido", f"R$ {lucro:.2f}")
        resumo2.metric("Lucro/Km", f"R$ {luc_km:.2f}")
        resumo3.metric("Ganho/Hora", f"R$ {ganho_h:.2f}")
        
        nova = {
            'Data': datetime.now().strftime('%d/%m/%Y %H:%M'), 
            'Valor': valor, 'Coleta_km': coleta, 'Entrega_km': entrega, 
            'Km_Total': km, 'Tempo_min': tempo, 'Gasolina': gasolina, 
            'Consumo': consumo, 'Observacao': obs, 'Combustivel': round(comb, 2), 
            'Gasto_Total': round(gasto, 2), 'Lucro': round(lucro, 2), 
            'Receita_km': round(rec_km, 2), 'Custo_km': round(cus_km, 2), 
            'Lucro_km': round(luc_km, 2), 'Ganho_hora': round(ganho_h, 2), 
            'Margem': round(margem, 1), 'Classificacao': c
        }
        
        df = pd.concat([df, pd.DataFrame([nova])], ignore_index=True)
        db.set("historico_corridas", df.to_json(orient='records'))
        
        st.success("✅ Salvo no histórico!")

# --- EXIBIÇÃO DO HISTÓRICO ---
st.divider()
st.subheader('Histórico')
st.dataframe(df, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    if not df.empty:
        st.download_button(
            label='📥 Baixar Backup', 
            data=df.to_csv(index=False).encode('utf-8'), 
            file_name='backup_corridas.csv',
            mime='text/csv',
            use_container_width=True
        )

with col2:
    if st.button('🗑 Limpar Tudo', use_container_width=True):
        df = pd.DataFrame(columns=colunas)
        db.set("historico_corridas", df.to_json(orient='records'))
        st.rerun()