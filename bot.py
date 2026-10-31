import os
import sys
import logging
import time
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from secretary import SecretaryModule
from notion_agent import NotionAgent
from weather_agent import WeatherAgent
from system_monitor_agent import SystemMonitorAgent

# Configurazione Logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("jarvis_bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("JarvisCore")

# Inizializzazione dei moduli
secretary = SecretaryModule()
notion = NotionAgent()
weather = WeatherAgent()
system_monitor = SystemMonitorAgent()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if secretary.is_authorized(user.id):
        await update.message.reply_text("👋 Bentornato, Admin. I sistemi di Jarvis (Meteo, Notion, System Monitor e IA) sono operativi.")
    else:
        await update.message.reply_text("Benvenuto. Questo è il terminale privato di Jarvis.")

async def handle_incoming_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text

    if not text:
        return

    # --- 1. GESTIONE UTENTE AUTORIZZATO (ADMIN) ---
    if secretary.is_authorized(user_id):
        logger.info(f"Messaggio dall'Admin ({user_id}): {text}")
        
        # Comando /status o /sys per il System Monitor del Pi Zero
        if text.lower().startswith("/status") or text.lower().startswith("/sys"):
            status_report = system_monitor.get_system_report()
            await update.message.reply_text(status_report, parse_mode="Markdown")
            return

        # Comando /meteo per Agrigento
        if text.lower().startswith("/meteo"):
            weather_report = weather.get_agrigento_weather()
            await update.message.reply_text(weather_report, parse_mode="Markdown")
            return

        # Comando /nota <testo> per Notion
        if text.startswith("/nota "):
            content = text[6:].strip()
            title = content.split("\n")[0][:50] if content else "Nota Rapida Telegram"
            success = notion.create_database_page(title=title, content=content, category="Note Rapide")
            
            if success:
                await update.message.reply_text("✅ Nota archiviata con successo nel database Notion.")
            else:
                await update.message.reply_text("❌ Errore durante la scrittura su Notion.")
            return

        # Qualsiasi altro messaggio dell'admin diventa una chat libera con l'IA (es. "Chi era Albert Einstein?")
        ai_response = await secretary.chat_with_admin_ai(text)
        await update.message.reply_text(ai_response, parse_mode="Markdown")
        return

    # --- 2. GESTIONE UTENTE NON AUTORIZZATO (CON IA SEGRETARIO) ---
    logger.info(f"Messaggio da utente esterno ID: {user_id} (@{user.username or 'N/A'}) -> Analisi con openai/gpt-oss-120b...")
    
    bot_reply, should_forward, reason = await secretary.evaluate_message_with_ai(text, user.to_dict())
    await update.message.reply_text(bot_reply, parse_mode="Markdown")

    # Se l'IA stabilisce che il messaggio è diretto a te o richiede attenzione, lo inoltra
    if should_forward and secretary.admin_ids:
        primary_admin = secretary.admin_ids[0]
        alert_msg = (
            f"🚨 **SEGNALAZIONE DA INOLTRARE (IA)**\n\n"
            f"👤 **Mittente:** {user.full_name} (`@{user.username or 'Senza username'}`)\n"
            f"🆔 **ID:** `{user_id}`\n"
            f"🧠 **Motivazione IA:** *{reason}*\n\n"
            f"💬 **Messaggio:**\n> {text}"
        )
        try:
            await context.bot.send_message(chat_id=primary_admin, text=alert_msg, parse_mode="Markdown")
            logger.info(f"Segnalazione inoltrata con successo all'admin {primary_admin}")
        except Exception as e:
            logger.error(f"Errore durante l'inoltro dell'alert all'admin: {e}")

if __name__ == "__main__":
    if not TELEGRAM_TOKEN:
        logger.critical("TELEGRAM_BOT_TOKEN mancante!")
        sys.exit(1)

    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .build()
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_incoming_message))

    while True:
        try:
            logger.info("Avvio polling Telegram...")
            app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
        except Exception as e:
            logger.error(f"Errore critico polling: {e}. Riavvio tra 10 secondi...")
            time.sleep(10)
