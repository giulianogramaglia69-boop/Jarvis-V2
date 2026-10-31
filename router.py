import os
from dotenv import load_dotenv
from groq import Groq

# Importa i tuoi moduli di agente esistenti
from agents.notion_agent import save_to_notion
from agents.meteo_agent import get_meteo
from agents.system_agent import get_system_status

# Importa i nuovi agenti
from agents.agent_rss_digest import fetch_rss_summaries
from agents.agent_cmd import run_system_command

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Definizione del modello unico scelto per il router
ROUTER_MODEL = "openai/gpt-oss-120b"

def route_and_execute(user_text: str) -> str:
    """
    Analizza l'input dell'utente, determina l'intento tramite LLM (gpt-oss-120b)
    e smista la richiesta all'agente di competenza.
    """
    system_prompt = (
        "Sei il router centrale di Jarvis. Analizza la richiesta dell'utente "
        "e rispondi ESCLUSIVAMENTE con una delle seguenti parole chiave:\n\n"
        "- NOTION: se chiede di salvare note, appunti, idee o promemoria.\n"
        "- METEO: se chiede previsioni del tempo, temperatura o se piove.\n"
        "- SYSTEM: se chiede lo stato dell'hardware, CPU, RAM, temperature o risorse del Pi.\n"
        "- RSS: se chiede news, notizie tech, aggiornamenti RSS o briefing giornaliero.\n"
        "- CMD: se chiede di eseguire un comando terminale, riavviare servizi o lanciare script Bash.\n"
        "- GENERAL: per qualsiasi altra conversazione, domanda generale o richiesta di codice.\n\n"
        "Rispondi SOLO con la parola chiave scelta."
    )
    
    try:
        # Classificazione dell'intento con openai/gpt-oss-120b
        completion = client.chat.completions.create(
            model=ROUTER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            temperature=0.0,
            max_tokens=10
        )
        
        intent = completion.choices[0].message.content.strip().upper()
        print(f"[Router] Intento rilevato: {intent}")
        
        # Smistamento degli intenti
        if "NOTION" in intent:
            result = save_to_notion(user_text)
            return "📝 Nota salvata su Notion con successo!"
            
        elif "METEO" in intent:
            return get_meteo()
            
        elif "SYSTEM" in intent:
            return get_system_status()
            
