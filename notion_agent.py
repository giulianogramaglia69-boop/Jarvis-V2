import os
import requests
from dotenv import load_dotenv

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

def save_to_notion(text: str) -> str:
    """Salva una nota o un'idea all'interno del database Notion configurato."""
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        return "⚠️ Credenziali Notion mancanti nel file .env."

    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    # Pulisce il testo rimuovendo eventuali prefissi di comando comuni
    clean_text = text.replace("nota", "").replace("annotami", "").replace("ricordati di", "").strip()
    if not clean_text:
        clean_text = text

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": clean_text
                        }
                    }
                ]
            }
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return f"📝 Nota salvata con successo su Notion: \"{clean_text}\""
        else:
            print(f"[Notion Error] {response.text}")
            return "⚠️ Errore durante la comunicazione con l'API di Notion."
    except Exception as e:
        print(f"[Notion Exception] {e}")
        return "⚠️ Impossibile raggiungere Notion al momento."
