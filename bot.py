import os
import asyncio
import threading
import sqlite3
import random
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)


TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")


# =========================
# DATABASE
# =========================

DB_NAME = "bounty.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0,
            energy INTEGER DEFAULT 100,
            level INTEGER DEFAULT 1,
            catches INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def get_player(user):
    conn = sqlite3.connect(DB_NAME)

    player = conn.execute(
        "SELECT * FROM players WHERE user_id = ?",
        (user.id,)
    ).fetchone()

    if player is None:
        conn.execute(
            """
            INSERT INTO players
            (user_id, username, balance, energy, level, catches)
            VALUES (?, ?, 0, 100, 1, 0)
            """,
            (user.id, user.username or user.first_name)
        )

        conn.commit()

        player = conn.execute(
            "SELECT * FROM players WHERE user_id = ?",
            (user.id,)
        ).fetchone()

    conn.close()

    return player


# =========================
# WEB SERVER FOR RENDER
# =========================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"BOUNTY bot is alive!")

    def log_message(self, format, *args):
        pass


def run_web_server():
    port = int(os.getenv("PORT", "10000"))

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    server.serve_forever()


# =========================
# MAIN MENU
# =========================

def main_menu():

    keyboard = [
        [
            InlineKeyboardButton("🎣 ЛОВИТЬ", callback_data="fish")
        ],
        [
            InlineKeyboardButton("🎒 ИНВЕНТАРЬ", callback_data="inventory"),
            InlineKeyboardButton("🔧 СНАРЯЖЕНИЕ", callback_data="equipment")
        ],
        [
            InlineKeyboardButton("📜 КОНТРАКТЫ", callback_data="contracts"),
            InlineKeyboardButton("🏆 РЕЙТИНГ", callback_data="rating")
        ],
        [
            InlineKeyboardButton("👥 ДРУЗЬЯ", callback_data="friends"),
            InlineKeyboardButton("🎁 БОНУС", callback_data="bonus")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


def player_text(player):

    user_id, username, balance, energy, level, catches = player

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    init_db()

    player = get_player(update.effective_user)

    await update.message.reply_text(
        player_text(player),
        parse_mode="HTML",
        reply_markup=main_menu()
    )


# =========================
# BUTTONS
# =========================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer
