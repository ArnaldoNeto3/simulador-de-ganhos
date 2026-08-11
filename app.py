# Importa o Streamlit, que é o "motor" que transforma este código em um site/aplicativo no celular.
import streamlit as st
# Importa o Pandas, usado para criar e manipular a nossa tabela de dados (como se fosse um Excel interno).
import pandas as pd
# Importa a ferramenta para pegar a data e a hora exatas do momento em que você salva a corrida.
from datetime import datetime
# Importa o JSON, que serve para "traduzir" nossa tabela em um texto simples para enviar pela internet.
import json
# Importa a ferramenta do Upstash para conectar nosso app ao banco de dados na nuvem.
from upstash_redis import Redis

# --- CONFIGURAÇÃO DA PÁGINA ---
# Define o nome que aparece na aba do navegador e o ícone de carrinho.
st.set_page_config(page_title='Simulador de Ganhos', page_icon='🚗')
# Cria o título grande e principal que aparece no topo da tela do aplicativo.
st.title('🚗 Simulador de Ganhos')

# --- CONEXÃO COM O BANCO DE DADOS (UPSTASH) ---
# O @st.cache_resource avisa ao Streamlit para conectar no banco de dados só uma vez e memorizar, para o app não ficar lento.
@st.cache_resource
def get_database():
    # Aqui ele usa as senhas que escondemos lá no "Secrets" para acessar o seu banco de dados no Upstash.
    return Redis(url=st.secrets["UPSTASH_URL"], token=st.secrets["UPSTASH_TOKEN"])

# Chama a função acima e guarda a conexão pronta na variável "db".
db = get_database()

# --- ESTRUTURA DA TABELA ---
# Cria uma lista com os nomes exatos de todas as colunas que a nossa tabela vai ter.
colunas = [
    'Data', 'Valor', 'Coleta_km', 'Entrega_km', 'Km_Total', 'Tempo_min', 
    'Gasolina', 'Consumo', 'Observacao', 'Combustivel', 'Gasto_Total', 
    'Lucro', 'Receita_km', 'Custo_km', 'Lucro_km', 'Ganho_hora', 'Margem', 'Classificacao'
]

# --- TENTATIVA DE RESGATE DOS DADOS (LEITURA) ---
# O bloco "try" manda o código tentar fazer algo. Se der erro, ele pula para o "except" em vez de quebrar o app.
try:
    # Pede ao banco de dados (db) para pegar o texto guardado com o nome "historico_corridas".
    dados_salvos = db.get("historico_corridas")
    # Verifica se os dados existem e não estão vazios.
    if dados_salvos and dados_salvos != "[]":
        # Se tem dados, desempacota o JSON e transforma de volta na nossa tabela do Pandas (df).
        df = pd.DataFrame(json.loads(dados_salvos))
    else:
        # Se não tem nada salvo, cria uma tabela (df) nova e vazia, só com o nome das colunas.
        df = pd.DataFrame(columns=colunas)
except:
    # Se der qualquer erro na comunicação com a nuvem, ele cria uma tabela vazia por segurança.
    df = pd.DataFrame(columns=colunas)

# --- BARRA LATERAL (CONFIGURAÇÕES GLOBAIS) ---
# Tudo que está dentro do "with st.sidebar:" vai aparecer no menu lateral (ou na setinha no topo do celular).
with st.sidebar:
    st.header('Configurações')
    # Cria a caixinha numérica do Consumo. Inicia com 12.0 e permite valores de 1 a 50.
    consumo = st.number_input('Consumo (km/L)', 1.0, 50.0, 12.0)
    # Cria a caixinha numérica da Gasolina. Inicia com 6.20 e permite valores de 0 a 20.
    gasolina = st.number_input('Gasolina (R$/L)', 0.0, 20.0, 6.20)

# --- CORPO PRINCIPAL (DADOS DA CORRIDA) ---
# Cria um subtítulo na tela principal.
st.subheader("Nova Corrida")

# Divide a tela em duas colunas (col1 e col2) para as caixinhas ficarem lado a lado e ocuparem menos espaço.
col1, col2 = st.columns(2)

# Tudo dentro deste bloco vai para a coluna da esquerda.
with col1:
    # Caixinha do valor da corrida. Vem vazia (value=None) para você digitar mais rápido.
    valor = st.number_input('Valor (R$)', min_value=0.0, value=None, placeholder="Ex: 25.50")
    # Caixinha da distância até a coleta.
    coleta = st.number_input('Km até coleta', min_value=0.0, value=None, placeholder="Ex: 2.5")

# Tudo dentro deste bloco vai para a coluna da direita.
with col2:
    # Caixinha da distância da entrega.
    entrega = st.number_input('Km entrega', min_value=0.0, value=None, placeholder="Ex: 10.0")
    # Caixinha do tempo estimado.
    tempo = st.number_input('Tempo (min)', min_value=1, value=None, placeholder="Ex: 30")

# Caixinha de texto livre para anotações.
obs = st.text_input('Observação (Opcional)')

# --- LÓGICA DO BOTÃO E CÁLCULOS ---
# Cria o botão e checa se ele foi clicado. O "use_container_width=True" faz ele esticar na tela toda.
if st.button('Analisar e Salvar', use_container_width=True):
    
    # Trava de segurança: verifica se você esqueceu de preencher alguma caixinha essencial.
    if valor is None or coleta is None or entrega is None or tempo is None:
        # Mostra um aviso amarelo pedindo para preencher.
        st.warning("⚠️ Preencha os campos de Valor, Coleta, Entrega e Tempo antes de analisar.")
    else:
        # A MATEMÁTICA COMEÇA AQUI:
        # Soma a quilometragem total.
        km = coleta + entrega
        # Calcula o gasto dividindo km pelo consumo e multiplicando pelo preço da gasolina.
        comb = (km / consumo) * gasolina
        # Neste app, o gasto total é só o combustível.
        gasto = comb 
        # Acha o lucro subtraindo o gasto do valor pago.
        lucro = valor - gasto
        
        # MÉTRICAS AVANÇADAS:
        # Calcula receita por km (se o km for maior que zero para não dar erro de divisão).
        rec_km = valor / km if km else 0
        # Calcula custo por km.
        cus_km = gasto / km if km else 0
        # Calcula lucro puro por km. Essa é a métrica principal de decisão.
        luc_km = lucro / km if km else 0
        # Calcula ganho por hora (transforma os minutos em fração de hora).
        ganho_h = lucro / (tempo / 60) if tempo else 0
        # Calcula a margem de lucro em porcentagem.
        margem = (lucro / valor * 100) if valor else 0
        
        # CLASSIFICAÇÃO (VEREDITO):
        # A estrutura if/elif/else funciona como um filtro. Ele para na primeira condição que for verdadeira.
        if luc_km >= 1.8: c = '🟢 Excelente'
        elif luc_km >= 1.5: c = '🟢 Muito boa'
        elif luc_km >= 1.2: c = '🟡 Boa'
        elif luc_km >= 0.9: c = '🟠 Regular'
        else: c = '🔴 Não compensa'
        
        # Mostra uma faixa verde na tela com o veredito final.
        st.success(f"Veredito: {c}")
        
        # EXIBIÇÃO VISUAL (PAINÉIS):
        # Cria três coluninhas para exibir os números em destaque.
        resumo1, resumo2, resumo3 = st.columns(3)
        resumo1.metric("Lucro Líquido", f"R$ {lucro:.2f}")  # O :.2f força a mostrar sempre 2 casas decimais (ex: 15.50).
        resumo2.metric("Lucro/Km", f"R$ {luc_km:.2f}")
        resumo3.metric("Ganho/Hora", f"R$ {ganho_h:.2f}")
        
        # EMPACOTAMENTE DOS DADOS (DICIONÁRIO):
        # Cria um "pacote" organizando cada resultado que calculamos debaixo do nome da sua respectiva coluna.
        nova = {
            'Data': datetime.now().strftime('%d/%m/%Y %H:%M'), # Pega hora exata e formata bonito.
            'Valor': valor, 'Coleta_km': coleta, 'Entrega_km': entrega, 
            'Km_Total': km, 'Tempo_min': tempo, 'Gasolina': gasolina, 
            'Consumo': consumo, 'Observacao': obs, 'Combustivel': round(comb, 2), # O round(x, 2) arredonda para 2 casas.
            'Gasto_Total': round(gasto, 2), 'Lucro': round(lucro, 2), 
            'Receita_km': round(rec_km, 2), 'Custo_km': round(cus_km, 2), 
            'Lucro_km': round(luc_km, 2), 'Ganho_hora': round(ganho_h, 2), 
            'Margem': round(margem, 1), 'Classificacao': c
        }
        
        # SALVAMENTO NA NUVEM:
        # Pega a tabela existente (df) e cola esse pacote novo (nova) embaixo dela.
        df = pd.concat([df, pd.DataFrame([nova])], ignore_index=True)
        # Traduz a tabela atualizada para texto JSON e salva por cima do arquivo velho lá no banco de dados.
        db.set("historico_corridas", df.to_json(orient='records'))
        
        # Avisa que deu tudo certo!
        st.success("✅ Salvo no histórico!")

# --- EXIBIÇÃO DO HISTÓRICO ---
# Desenha uma linha na tela para separar os assuntos.
st.divider()
# Subtítulo para a área de histórico.
st.subheader('Histórico')
# Mostra a tabela de dados completa na tela do celular/computador.
st.dataframe(df, use_container_width=True)

# Cria duas colunas para os botões de ação final.
col1, col2 = st.columns(2)

with col1:
    # Se a tabela NÃO estiver vazia...
    if not df.empty:
        # Cria um botão especial que pega a tabela, transforma em CSV (Excel) e baixa para o seu celular.
        st.download_button(
            label='📥 Baixar Backup', 
            data=df.to_csv(index=False).encode('utf-8'), 
            file_name='backup_corridas.csv',
            mime='text/csv',
            use_container_width=True
        )

with col2:
    # Botão de perigo para limpar tudo.
    if st.button('🗑 Limpar Tudo', use_container_width=True):
        # Ele substitui a tabela atual por uma tabela vazia.
        df = pd.DataFrame(columns=colunas)
        # Salva essa tabela vazia (em JSON) lá no Upstash, apagando os dados velhos.
        db.set("historico_corridas", df.to_json(orient='records'))
        # Manda o aplicativo atualizar a página sozinho (F5) para a tabela sumir da tela.
        st.rerun()