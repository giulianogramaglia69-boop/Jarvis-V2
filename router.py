import os
from dotenv import load_dotenv
from groq import Groq

# Importa i tuoi moduli di agente esistenti o futuri
from agents.notion_agent import save_to_notion
from agents.meteo_agent import get_meteo
from agents.system_agent import get_system_status

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def route_and_execute(user_text: str) -> str:
    """
    Analizza l'input dell'utente, determina l'intento tramite LLM 
    e smista la richiesta all'agente di competenza.
    """
    system_prompt = (
        "Sei il router centrale di Jarvis. Il tuo compito è analizzare la richiesta "
        "dell'utente e classificarla esattamente in una di queste categorie:\n"
        "1. NOTION (es. appunti, ricordati di, annota, salva nota)\n"
        "2. METEO (es. tempo, previsioni, piove, temperatura)\n"
        "3. SYSTEM (es. stato, cpu, ram, batteria, risorse)\n"
        "4. GENERAL (qualsiasi altra conversazione o domanda generale)\n\n"
        "Rispondi unicamente con una delle quattro parole chiave: NOTION, METEO, SYSTEM, GENERAL."
    )
    
    try:
        # Chiamata rapida ed economica per il routing dell'intento
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Modello fulmineo perfetto per il Pi Zero
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            temperature=0.0,
            max_tokens=10
        )
        
        intent = completion.choices[0].message.content.strip().upper()
        print(f"[Router] Intento rilevato: {intent}")
        
        # Smistamento basato sull'intento
        if "NOTION" in intent:
            # Estrae il contenuto rimuovendo il comando se necessario o passando tutto
            result = save_to_notion(user_text)
            return f"📝 Nota salvata su Notion con successo!"
            
        elif "METEO" in intent:
            return get_meteo()
            
        elif "SYSTEM" in intent:
            return get_system_status()
            
        else:
            # Fallback su un modello conversazionale generale (es. gpt-oss-120b o llama-3.3)
            return ask_general_llm(user_text)
            
    except Exception as e:
        print(f"[Router Error] {e}")
        return "⚠️ Si è verificato un errore nel routing della richiesta."

def ask_general_llm(text: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": text}],
        temperature=0.7,
        max_tokens=300
    )
    return response.choices[0].message.content
