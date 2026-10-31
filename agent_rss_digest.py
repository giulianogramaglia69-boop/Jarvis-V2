import feedparser
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Puoi personalizzare o espandere questa lista con i feed RSS che preferisci
DEFAULT_FEEDS = [
    "https://www.omgubuntu.co.feed",
    "https://lwn.net/headlines/rss",
]

def fetch_rss_summaries(feed_urls=None, max_items=3):
    if feed_urls is None:
        feed_urls = DEFAULT_FEEDS

    articles_text = ""
    for url in feed_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_items]:
                articles_text += f"- Titolo: {entry.title}\n  Link: {entry.link}\n\n"
        except Exception as e:
            continue

    if not articles_text:
        return "❌ Non sono riuscito a recuperare nessun articolo dai feed RSS al momento."

    # Prompt per fare sintetizzare a Groq le novità
    prompt = f"""
Sei un assistente tech esperto. Analizza questi titoli di ultime notizie/articoli dai feed RSS e compila un briefing sintetico, ordinato e d'impatto in italiano, evidenziando le 3 notizie più interessanti con i relativi link:

{articles_text}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # o il modello Groq che stai usando nel progetto
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Errore durante la generazione del digest con l'IA: {str(e)}"
