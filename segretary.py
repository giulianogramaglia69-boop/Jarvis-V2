import os
import json
import logging
from typing import Tuple, Dict, Any
from groq import Groq

logger = logging.getLogger(__name__)

class SecretaryModule:
    def __init__(self):
        # Caricamento Admin ID dalla variabile d'ambiente
        admin_env = os.getenv("ADMIN_ID", "0")
        try:
            self.admin_ids = [int(x.strip()) for x in admin_env.split(",") if x.strip().isdigit()]
        except ValueError:
            self.admin_ids = [0]
            logger.error("Formato ADMIN_ID non valido nelle variabili d'ambiente.")

        # Inizializzazione Client Groq API
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if self.groq_api_key:
            self.client = Groq(api_key=self.groq_api_key)
        else:
            self.client = None
            logger.warning("GROQ_API_KEY non trovata. Il segretario utilizzerà la modalità di fallback senza IA.")

    def is_authorized(self, user_id: int) -> bool:
        """Verifica se l'utente è l'amministratore autorizzato."""
        return user_id in self.admin_ids

    async def evaluate_message_with_ai(self, user_message: str, user_data: Dict[str, Any]) -> Tuple[str, bool, str]:
        """
        Analizza il messaggio di un utente non autorizzato tramite il modello openai/gpt-oss-120b su Groq.
        Restituisce una tupla: (risposta_per_utente, deve_inoltrare_all_admin, motivazione_inoltro)
        """
        username = user_data.get("username", "sconosciuto")
        first_name = user_data.get("first_name", "Utente")

        # Fallback nel caso in cui le API di Groq non siano configurate
        if not self.client:
            return self._fallback_evaluation(user_message)

        # System Prompt per istruire il modello sul comportamento da tenere
        system_prompt = (
            "Sei Jarvis, un assistente IA avanzato che fa da segretario per il tuo creatore/amministratore (Giuliano).\n"
            "Il tuo compito è analizzare i messaggi degli utenti esterni e decidere come comportarti.\n\n"
            "REGOLE DI COMPORTAMENTO:\n"
            "1. Se l'utente fa domande generali, di cultura, curiosità, o chiede assistenza generica su argomenti standard, "
            "rispondi direttamente in modo cortese, utile e sintetico. In questo caso 'should_forward' deve essere FALSE.\n"
            "2. Se l'utente sta cercando di contattare l'amministratore, lascia un messaggio per lui, chiede appuntamenti, "
            "parla di questioni personali, o scrive messaggi urgenti/rilevanti diretti a lui, rispondi dicendo che la richiesta "
            "è stata presa in carico e sarà valutata dal proprietario. In questo caso 'should_forward' deve essere TRUE.\n\n"
            "DEVI RISPONDERE ESCLUSIVAMENTE IN FORMATO JSON VALIDABILE CON LA SEGUENTE STRUTTURA:\n"
            "{\n"
            '  "reply": "La risposta testuale formattata in Markdown da inviare all\'utente",\n'
            '  "should_forward": true/false,\n'
            '  "reason": "Una breve motivazione in italiano del perché hai deciso di inoltrare o meno il messaggio"\n'
            "}"
        )

        user_prompt = f"Messaggio ricevuto da {first_name} (@{username}):\n\"{user_message}\""

        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=500
            )

            result_json = json.loads(response.choices[0].message.content)
            
            reply = result_json.get("reply", "Richiesta ricevuta.")
            should_forward = result_json.get("should_forward", False)
            reason = result_json.get("reason", "Analisi completata.")

            return reply, should_forward, reason

        except Exception as e:
            logger.error(f"Errore durante la chiamata alle API di Groq con openai/gpt-oss-120b: {e}")
            return self._fallback_evaluation(user_message)

    def _fallback_evaluation(self, user_message: str) -> Tuple[str, bool, str]:
        """Logica deterministica di emergenza se le API IA non rispondono."""
        text_lower = user_message.lower()
        keywords = ["urgente", "emergenza", "importante", "contatto", "chiama", "scrivi", "appuntamento", "giuliano"]
        
        is_important = any(kw in text_lower for kw in keywords)
        
        reply = (
            "🤖 **Segretario Virtuale Jarvis**\n\n"
            "Ho preso in carico il tuo messaggio. "
            "Se la comunicazione contiene una richiesta diretta per l'amministratore, gli verrà inoltrata."
        )
        reason = "Rilevamento parole chiave (Modalità Fallback)" if is_important else "Messaggio generico (Modalità Fallback)"
        
        return reply, is_important, reason
