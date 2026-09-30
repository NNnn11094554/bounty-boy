import os
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")

players = {}


def get_player(user_id):
    if user_id not in players:
        players[user_id] = {
            "coins": 0,
            "energy": 10,
            "fish": []
        }
    return players[user_id]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = get_player(update.effective_user.id)

    keyboard = [
        [InlineKeyboardButton("🎣 ЛОВИТЬ", callback_data="fish")],
        [
            InlineKeyboardButton("🐟 МОЙ УЛОВ", callback_data="catch"),
            InlineKeyboardButton("💰 БАЛАНС", callback_data="balance"),
        ],
    ]

    text = (
        "🎣 <b>BOUNTY</b>\n\n"
        "Добро пожаловать в мир большой рыбалки!\n\n"
        f"💰 BOUNTY: {player['coins']}\n"
        f"⚡ Энергия: {player['energy']}/10\n\n"
        "Забрасывай удочку и попробуй поймать редкую рыбу!"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    player = get_player(query.from_user.id)

    if query.data == "fish":
        if player["energy"] <= 0:
            await query.edit_message_text(
                "⚡ <b>Энергия закончилась!</b>\n\n"
                "Возвращайся позже.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 НАЗАД", callback_data="back")]
                ]),
            )
            return

        player["energy"] -= 1

        fish_list = [
            ("🐟 Карась", 50, "Обычная"),
            ("🐠 Окунь", 80, "Обычная"),
            ("🐡 Щука", 150, "Необычная"),
            ("🐟 Сом", 250, "Необычная"),
            ("✨ Золотой карп", 700, "Редкая"),
            ("🌙 Лунная форель", 2000, "Эпическая"),
            ("🐉 МОРСКОЙ ДРАКОН", 10000, "Легендарная"),
        ]

        fish, reward, rarity = random.choices(
            fish_list,
            weights=[40, 25, 15, 10, 6, 3, 1],
            k=1
        )[0]

        player["coins"] += reward
        player["fish"].append(fish)

        keyboard = [
            [InlineKeyboardButton("🎣 ЕЩЁ РАЗ", callback_data="fish")],
            [InlineKeyboardButton("🔙 МЕНЮ", callback_data="back")],
        ]

        text = (
            "🌊 <b>КЛЁВ!</b>\n\n"
            f"{fish}\n"
            f"⭐ Редкость: <b>{rarity}</b>\n\n"
            f"💰 Награда: +{reward} BOUNTY\n"
            f"⚡ Энергия: {player['energy']}/10\n\n"
            "Удача сегодня на твоей стороне 👀"
        )

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "balance":
        await query.edit_message_text(
            f"💰 <b>ТВОЙ БАЛАНС</b>\n\n"
            f"BOUNTY: {player['coins']}\n"
            f"⚡ Энергия: {player['energy']}/10",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 НАЗАД", callback_data="back")]
            ]),
        )

    elif query.data == "catch":
        if player["fish"]:
            fish_text = "\n".join(
                f"• {fish}" for fish in player["fish"][-10:]
            )
        else:
            fish_text = "Пока пусто 😢"

        await query.edit_message_text(
            f"🎒 <b>ТВОЙ УЛОВ</b>\n\n{fish_text}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 НАЗАД", callback_data="back")]
            ]),
        )

    elif query.data == "back":
        keyboard = [
            [InlineKeyboardButton("🎣 ЛОВИТЬ", callback_data="fish")],
            [
                InlineKeyboardButton("🐟 МОЙ УЛОВ", callback_data="catch"),
                InlineKeyboardButton("💰 БАЛАНС", callback_data="balance"),
            ],
        ]

        await query.edit_message_text(
            f"🎣 <b>BOUNTY</b>\n\n"
            f"💰 BOUNTY: {player['coins']}\n"
            f"⚡ Энергия: {player['energy']}/10\n\n"
            "Что будем делать?",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN не установлен")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    print("BOUNTY запущен!")

    app.run_polling()


if __name__ == "__main__":
    main()
