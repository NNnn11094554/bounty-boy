import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎣 Добро пожаловать в BOUNTY!\n\n"
        "Здесь начинается твоя охота за BOUNTY.\n\n"
        "Используй /help, чтобы узнать команды."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎣 BOUNTY — Telegram fishing game\n\n"
        "/start — начать игру\n"
        "/help — помощь"
    )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    print("BOUNTY bot started!")
    app.run_polling()


if __name__ == "__main__":
    main()
