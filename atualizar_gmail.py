import imaplib
import email
import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def _get_secret(nome):
    """Lê do .env/variável de ambiente; se não achar, tenta st.secrets."""
    valor = os.getenv(nome)
    if valor:
        return valor
    try:
        import streamlit as st
        return st.secrets[nome]
    except Exception:
        return None

GMAIL_USER = _get_secret("GMAIL_USER")
GMAIL_PASS = _get_secret("GMAIL_PASS")
DB_PATH = "logistica.db"


def processar_e_atualizar_banco(caminho_excel):
    """Lê o Excel baixado e salva no banco de dados SQLite."""
    df = pd.read_excel(caminho_excel)

    if 'Cotação' in df.columns:
        df['Cotação'] = df['Cotação'].astype(str).str.strip()
    if 'OV Pedido' in df.columns:
        df['OV Pedido'] = df['OV Pedido'].astype(str).str.strip()

    conn = sqlite3.connect(DB_PATH)
    df.to_sql('pedidos_logistica', conn, if_exists='replace', index=False)
    conn.close()


def verificar_gmail():
    """Busca o e-mail mais recente com planilha .xlsx e atualiza o banco.
    Retorna (sucesso: bool, mensagem: str)."""
    if not GMAIL_USER or not GMAIL_PASS:
        return False, "GMAIL_USER/GMAIL_PASS não configurados."

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select("inbox")

        status, messages = mail.search(None, '(SUBJECT "Status de Transporte")')
        ids = messages[0].split()

        if not ids:
            mail.logout()
            return False, "Nenhum e-mail com esse assunto foi encontrado."

        # Do mais novo para o mais antigo; para no primeiro com .xlsx
        for num in reversed(ids):
            _, data = mail.fetch(num, "(BODY.PEEK[])")  # não marca como lido
            msg = email.message_from_bytes(data[0][1])

            for part in msg.walk():
                if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                    continue

                filename = part.get_filename()
                if filename and filename.lower().endswith('.xlsx'):
                    temp_filepath = os.path.join(".", "logistica_temp.xlsx")
                    with open(temp_filepath, 'wb') as f:
                        f.write(part.get_payload(decode=True))

                    try:
                        processar_e_atualizar_banco(temp_filepath)
                    finally:
                        if os.path.exists(temp_filepath):
                            os.remove(temp_filepath)

                    mail.logout()
                    return True, f"Banco atualizado com '{filename}'."

        mail.logout()
        return False, "Nenhum anexo .xlsx encontrado nos e-mails."

    except Exception as e:
        return False, f"Erro no processamento do Gmail: {e}"


if __name__ == "__main__":
    print(verificar_gmail())