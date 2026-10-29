import imaplib
import email
import os
import pandas as pd
import sqlite3
from dotenv import load_dotenv
   
# Carrega as senhas ocultas do arquivo .env
load_dotenv()
   
# --- CONFIGURAÇÕES ---
# Agora o código puxa as senhas sem mostrar no texto!
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")
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
    print("✅ Banco de dados 'logistica.db' atualizado com sucesso!")

def verificar_gmail():
    """Conecta ao Gmail e busca planilhas anexas em e-mails não lidos."""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select("inbox")

        # Busca e-mails não lidos com o assunto de logística
        status, messages = mail.search(None, '(UNSEEN SUBJECT "Status de Transporte")')

        for num in messages[0].split():
            _, data = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])

            for part in msg.walk():
                if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                    continue

                filename = part.get_filename()
                if filename and filename.endswith('.xlsx'):
                    temp_filepath = os.path.join(".", "logistica_temp.xlsx")
                    with open(temp_filepath, 'wb') as f:
                        f.write(part.get_payload(decode=True))
                    
                    print(f"📥 Anexo '{filename}' baixado com sucesso.")
                    processar_e_atualizar_banco(temp_filepath)
                    
                    # Remove o arquivo temporário
                    if os.path.exists(temp_filepath):
                        os.remove(temp_filepath)

        mail.logout()
    except Exception as e:
        print(f"Erro no processamento do Gmail: {e}")

if __name__ == "__main__":
    verificar_gmail()