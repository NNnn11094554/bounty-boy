import os
import asyncio
import threading
import sqlite3
import random
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes


TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")


DB_NAME = "bounty.db"


# =========================
# DATABASE
# =========================

def init_db():
    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER NOT NULL DEFAULT 0,
            energy INTEGER NOT NULL DEFAULT 100,
            level INTEGER NOT NULL DEFAULT 1,
            catches INTEGER NOT NULL DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def get_player(user):
    conn = sqlite3.connect(DB_NAME)

    try:
        player = conn.execute(
            """
            SELECT user_id, username, balance, energy, level, catches
            FROM players
            WHERE user_id = ?
            """,
            (user.id,)
        ).fetchone()

        if player is None:
            conn.execute(
                """
                INSERT INTO players
                (user_id, username, balance, energy, level, catches)
                VALUES (?, ?, 0, 100, 1, 0)
                """,
                (
                    user.id,
                    user.username or user.first_name or "Hunter"
                )
            )

            conn.commit()

            player = conn.execute(
                """
                SELECT user_id, username, balance, energy, level, catches
                FROM players
                WHERE user_id = ?
                """,
                (user.id,)
            ).fetchone()

        return player

    finally:
        conn.close()


# =========================
# RENDER WEB SERVER
# =========================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        body = b"BOUNTY bot is alive!"

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/plain; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.end_headers()

        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


def run_web_server():
    port = int(os.getenv("PORT", "10000"))

    server = ThreadingHTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    print(
        f"HTTP server listening on port {port}",
        flush=True
    )

    server.serve_forever()


# =========================
# MAIN MENU
# =========================

def main_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "🎣 ЛОВИТЬ",
                callback_data="fish"
            )
        ],

        [
            InlineKeyboardButton(
                "🎒 ИНВЕНТАРЬ",
                callback_data="inventory"
            ),
            InlineKeyboardButton(
                "🔧 СНАРЯЖЕНИЕ",
                callback_data="equipment"
            )
        ],

        [
            InlineKeyboardButton(
                "📜 КОНТРАКТЫ",
                callback_data="contracts"
            ),
            InlineKeyboardButton(
                "🏆 РЕЙТИНГ",
                callback_data="rating"
            )
        ],

        [
            InlineKeyboardButton(
                "👥 ДРУЗЬЯ",
                callback_data="friends"
            ),
            InlineKeyboardButton(
                "🎁 БОНУС",
                callback_data="bonus"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================
# PLAYER TEXT
# =========================

def player_text(player):

    (
        user_id,
        username,
        balance,
        energy,
        level,
        catches
    ) = player

    return (
        "🎣 <b>BOUNTY</b>\n\n"

        f"💰 <b>{balance:,}</b> BNT\n"

        f"⚡ <b>{energy}/100</b> энергия\n"

        f"⭐ Уровень <b>{level}</b>\n\n"

        f"🎣 Уловов: <b>{catches}</b>\n\n"

        "🌊 <i>Твоя охота начинается...</i>"
    )


# =========================
# START
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    player = get_player(
        update.effective_user
    )

    await update.message.reply_text(
        player_text(player),
        parse_mode="HTML",
        reply_markup=main_menu()
    )


# =========================
# BUTTON HANDLER
# =========================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user = query.from_user

    player = get_player(user)

    (
        user_id,
        username,
        balance,
        energy,
        level,
        catches
    ) = player


    # =====================
    # FISH
    # =====================

    if query.data == "fish":

        if energy < 5:

            await query.answer(
                "⚡ Недостаточно энергии!",
                show_alert=True
            )

            return


        rewards = [

            ("🐟 Карп", 15, 60),

            ("🐠 Тунец", 30, 25),

            ("🦈 Акула", 100, 10),

            ("🐙 Осьминог", 250, 4),

            ("🐋 КИТ", 1000, 1)

        ]


        roll = random.randint(1, 100)

        current = 0

        catch = rewards[-1]


        for item in rewards:

            current += item[2]

            if roll <= current:

                catch = item

                break


        name, reward, chance = catch


        new_balance = balance + reward

        new_energy = energy - 5

        new_catches = catches + 1

        new_level = 1 + new_catches // 50


        conn = sqlite3.connect(DB_NAME)

        try:

            conn.execute(
                """
                UPDATE players

                SET balance = ?,
                    energy = ?,
                    catches = ?,
                    level = ?

                WHERE user_id = ?
                """,

                (
                    new_balance,
                    new_energy,
                    new_catches,
                    new_level,
                    user_id
                )
            )

            conn.commit()

        finally:

            conn.close()


        await query.edit_message_text(

            f"🎣 <b>ПОКЛЁВКА!</b>\n\n"

            f"{name}\n\n"

            f"💰 <b>+{reward:,} BNT</b>\n"

            f"⚡ -5 энергии\n\n"

            f"💰 Баланс: "
            f"<b>{new_balance:,} BNT</b>\n"

            f"⚡ Энергия: "
            f"<b>{new_energy}/100</b>\n"

            f"⭐ Уровень: "
            f"<b>{new_level}</b>",

            parse_mode="HTML",

            reply_markup=main_menu()
        )

        return


    # =====================
    # OTHER MENUS
    # =====================

    messages = {

        "inventory":

            "🎒 <b>ИНВЕНТАРЬ</b>\n\n"
            "Пока здесь пусто.\n\n"
            "🎣 Лови добычу, "
            "чтобы заполнить коллекцию!",


        "equipment":

            "🔧 <b>СНАРЯЖЕНИЕ</b>\n\n"
            "🎣 Удочка — уровень 1\n"
            "🪝 Крючок — уровень 1\n"
            "🧵 Леска — уровень 1\n\n"
            "🔒 Улучшения скоро будут доступны.",


        "contracts":

            "📜 <b>КОНТРАКТЫ</b>\n\n"

            "🎯 Поймай 10 существ\n"
            "💰 Награда: 500 BNT\n\n"

            "🎯 Сделай 25 забросов\n"
            "💰 Награда: 1,500 BNT\n\n"

            "🔒 Система контрактов будет расширена.",


        "rating":

            "🏆 <b>РЕЙТИНГ ОХОТНИКОВ</b>\n\n"

            "Рейтинг появится после "
            "накопления статистики.",


        "friends":

            "👥 <b>ДРУЗЬЯ</b>\n\n"

            "Приглашай охотников "
            "и создавай свою команду!",


        "bonus":

            "🎁 <b>ЕЖЕДНЕВНЫЙ БОНУС</b>\n\n"

            "🔥 Заходи каждый день.\n"

            "🎁 Получай BNT.\n"

            "⚡ Получай энергию.\n"

            "💎 Серия дней будет "
            "увеличивать награду!"
    }


    if query.data in messages:

        text = messages[query.data]


        if query.data == "friends":

            bot_username = (
                context.bot.username
                or "YOUR_BOT"
            )


            referral_link = (
                f"https://t.me/"
                f"{bot_username}"
                f"?start=ref_{user_id}"
            )


            text += (
                "\n\n🔗 Твоя ссылка:\n"
                f"{referral_link}"
            )


        await query.edit_message_text(

            text,

            parse_mode="HTML",

            reply_markup=main_menu()
        )


# =========================
# MAIN
# =========================

async def main():

    print(
        "Starting BOUNTY...",
        flush=True
    )


    init_db()


    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()


    print(
        "Building Telegram application...",
        flush=True
    )


    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )


    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )


    print(
        "Initializing Telegram application...",
        flush=True
    )


    await app.initialize()


    print(
        "Starting Telegram application...",
        flush=True
    )


    await app.start()


    if app.updater is None:

        raise RuntimeError(
            "Telegram updater is not available"
        )


    print(
        "Starting Telegram polling...",
        flush=True
    )


    await app.updater.start_polling()


    print(
        "🎣 BOUNTY bot started successfully!",
        flush=True
    )


    try:

        await asyncio.Event().wait()

    finally:

        print(
            "Stopping BOUNTY...",
            flush=True
        )


        await app.updater.stop()

        await app.stop()

        await app.shutdown()


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except Exception as exc:

        print(
            f"FATAL ERROR: "
            f"{type(exc).__name__}: {exc}",
            flush=True
        )

        raise
