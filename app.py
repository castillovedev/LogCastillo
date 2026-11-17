import streamlit as st
import pandas as pd
import sqlite3
import os
from atualizar_gmail import verificar_gmail

st.set_page_config(page_title="Portal de Consulta de Logística", page_icon="📦", layout="centered")

@st.cache_resource(ttl=600)  # sincroniza no máximo a cada 10 minutos
def sincronizar():
    return verificar_gmail()

ok, msg_sync = sincronizar()

DB_PATH = 'logistica.db'

# --- FUNÇÃO DE CONSULTA AO BANCO ---
def consultar_banco(cotacao_busca: str) -> pd.DataFrame:
    """Consulta o banco de dados SQLite filtrando pela Cotação."""
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM pedidos_logistica WHERE CAST(Cotação AS TEXT) = ?"
    df = pd.read_sql_query(query, conn, params=(cotacao_busca,))
    conn.close()
    return df

# --- TELA PRINCIPAL (CONSULTA DOS VENDEDORES) ---
st.title("📦 Consulta de Logística e Entregas")
st.markdown("Digite o número da **Cotação** para verificar o status atualizado do pedido.")

cotacao_busca = st.text_input("Número da Cotação:").strip()

if st.button("Buscar Status", type="primary"):
    if cotacao_busca:
        if not os.path.exists(DB_PATH):
            st.error("O banco de dados ainda não foi criado. Aguarde a sincronização automática do e-mail.")
        else:
            try:
                resultado = consultar_banco(cotacao_busca)
                
                if not resultado.empty:
                    def tratar_valor(linha, coluna, is_data=False):
                        valor = linha.get(coluna)
                        if pd.isna(valor) or valor is None:
                            return "Não informado"
                        if is_data and isinstance(valor, pd.Timestamp):
                            return valor.strftime('%d/%m/%Y')
                        return str(valor)

                    # Montagem da mensagem formatada
                    mensagem = f"Olá! Seguem as informações atualizadas da entrega (Cotação: {cotacao_busca}):\n\n"
                    
                    for i, (_, linha) in enumerate(resultado.iterrows(), start=1):
                        if len(resultado) > 1:
                            mensagem += f"🔹 --- Item {i} ---\n"
                            
                        mensagem += f"📦 OV Pedido: {tratar_valor(linha, 'OV Pedido')}\n"
                        mensagem += f"📱 Aparelho: {tratar_valor(linha, 'Modelo do Aparelho')} ({tratar_valor(linha, 'Descrição')})\n"
                        mensagem += f"📌 Status Atual: {tratar_valor(linha, 'Última Ocorrência Geral')}\n"
                        mensagem += f"🚚 Transportadora: {tratar_valor(linha, 'Transportadora_V2')} (Pacote: {tratar_valor(linha, 'Num_Embalagem')})\n"
                        mensagem += f"📅 Previsão de Entrega: {tratar_valor(linha, 'Previsão_Entrega', is_data=True)}\n\n"
                        
                    mensagem += "Qualquer dúvida, é só avisar!"
                    
                    st.success(f"Encontrado(s) {len(resultado)} item(ns) para esta Cotação:")
                    st.code(mensagem, language="text")
                    
                else:
                    st.warning("Cotação não encontrada na base de dados.")
                    
            except Exception as e:
                st.error(f"Erro ao consultar o banco de dados: {e}")
    else:
        st.warning("Por favor, informe o número da Cotação.")

with st.expander("Status da sincronização"):
    (st.success if ok else st.error)(msg_sync)