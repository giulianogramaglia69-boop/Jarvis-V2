import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from groq import Groq

# Importa l'agente router che abbiamo creato
from router import route_and_execute
from gtts import gTTS

# Carica le variabili d'ambiente
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))  # Il tuo ID Telegram autorizzato

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Configurazione logging di base
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def check_auth(user_id: int) -> bool:
    """Controlla se l'utente è autorizzato (il creatore del bot)."""
    return user_id == ADMIN_ID


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce i messaggi di testo in arrivo."""
    user = update.effective_user
    if not check_auth(user.id):
        await update.message.reply_text("⛔ Non sei autorizzato a usare questo bot.")
        return

    user_text = update.message.text
    logger.info(f"[Testo] Da {user.username}: {user_text}")

    # Notifica di elaborazione
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Invia la richiesta al Router Agent
    response_text = route_and_execute(user_text)

    await update.message.reply_text(response_text)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce i messaggi vocali: scarica, trascrive con Whisper, smista e risponde in audio."""
    user = update.effective_user
    if not check_auth(user.id):
        await update.message.reply_text("⛔ Non sei autorizzato a usare questo bot.")
        return

    logger.info(f"[Vocale] Ricevuto messaggio vocale da {user.username}")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="record_voice")

    voice_file = None
    ogg_path = "temp_voice.ogg"
    mp3_path = "response.mp3"

    try:
        # 1. Scarica il file audio da Telegram
        file = await context.bot.get_file(update.message.voice.file_id)
        await file.download_to_drive(ogg_path)

        # 2. Trascrizione con Whisper (Groq API)
        with open(ogg_path, "rb") as file_audio:
            transcription = client.audio.transcriptions.create(
                file=(ogg_path, file_audio.read()),
                model="whisper-large-v3",
                language="it",
                response_format="text"
            )
        
        user_text = transcription.strip()
        logger.info(f"[Whisper Trascrizione]: {user_text}")

        # Invia una notifica con il testo capito
        await update.message.reply_text(f"🗣️ *Trascrizione:* {user_text}", parse_mode="Markdown")

        # 3. Invia il testo trascritto al Router Agent
        response_text = route_and_execute(user_text)

        # 4. Genera la risposta audio (TTS con gTTS)
        tts = gTTS(text=response_text, lang="it", slow=False)
        tts.save(mp3_path)

        # 5. Invia il messaggio di testo e la risposta vocale su Telegram
        await update.message.reply_text(response_text)
        with open(mp3_path, "rb") as voice_resp:
            await update.message.reply_voice(voice=voice_resp)

    except Exception as e:
        logger.error(f"[Voice Error]: {e}")
        await update.message.reply_text("⚠️ Si è verificato un errore durante l'elaborazione del vocale.")

    finally:
        # Pulisce i file temporanei locali
        if os.path.exists(ogg_path):
            os.remove(ogg_path)
        if os.path.exists(mp3_path):
            os.remove(mp3_path)


def main():
    """Avvia il bot in modalità polling."""
    if not TELEGRAM_TOKEN:
        logger.error("ERRORE: TELEGRAM_TOKEN non trovato nel file .env!")
        return

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Registrazione degli handler
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    logger.info("🤖 Jarvis Bot avviato con successo e in ascolto...")
    application.run_polling()


if __name__ == "__main__":
    main()
