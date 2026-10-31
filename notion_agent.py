import os
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class NotionAgent:
    def __init__(self):
        self.api_key = os.getenv("NOTION_API_KEY")
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        self.version = "2022-06-28"
        
        if not self.api_key or not self.database_id:
            logger.warning("NotionAgent: NOTION_API_KEY o NOTION_DATABASE_ID non configurati correttamente nelle variabili d'ambiente.")

    def _get_headers(self) -> Dict[str, str]:
        """Restituisce gli header di autenticazione richiesti dalle API di Notion."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": self.version
        }

    def create_database_page(self, title: str, content: str, category: Optional[str] = "Generale") -> bool:
        """
        Crea una nuova pagina all'interno del database Notion specificato.
        Suddivide automaticamente il contenuto in blocchi da massimo 2000 caratteri.
        """
        if not self.api_key or not self.database_id:
            logger.error("Impossibile procedere con Notion: credenziali mancanti.")
            return False

        url = "https://api.notion.com/v1/pages"
        
        # Suddivide il testo in blocchi conformi al limite di 2000 caratteri dei paragrafi Notion
        chunks = [content[i:i+2000] for i in range(0, len(content), 2000)]
        children_blocks = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                }
            } for chunk in chunks
        ]

        payload = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": title}}]
                },
                "Categoria": {
                    "select": {"name": category}
                }
            },
            "children": children_blocks
        }

        try:
            response = requests.post(url, json=payload, headers=self._get_headers(), timeout=15)
            if response.status_code == 200:
                logger.info(f"Pagina Notion '{title}' creata con successo.")
                return True
            else:
                logger.error(f"Errore Notion API ({response.status_code}): {response.text}")
                return False
                
        except Exception as e:
            logger.exception(f"Eccezione durante la chiamata alle API di Notion: {e}")
            return False
