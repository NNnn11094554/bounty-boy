    else:
        await query.answer("вњ… РЈР»СѓС‡С€РµРЅРѕ!")

    text, keyboard = equipment_view(res["player"])
    await show(query, text, keyboard)


async def on_contracts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id, name = who(update)
    row, claimed = await asyncio.to_thread(api_contracts, user_id, name)
    text, keyboard = contracts_view(row, claimed)
    await show(query, text, keyboard)


async def on_claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    contract_id = context.match.group(1)
    user_id, name = who(update)
    res = await asyncio.to_thread(api_claim_contract, user_id, name, contract_id)

    if res["status"] == "ok":
        await query.answer(f"рџЋЃ +{res['reward']:,} BNT!", show_alert=True)
    else:
        await query.answer("РќР°РіСЂР°РґР° РЅРµРґРѕСЃС‚СѓРїРЅР°.")

    row, claimed = await asyncio.to_thread(api_contracts, user_id, name)
    text, keyboard = contracts_view(row, claimed)
    await show(query, text, keyboard)


async def on_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id, name = who(update)
    row, top, rank = await asyncio.to_thread(api_leaderboard, user_id, name)
    await show(query, rating_text(row, top, rank), back_menu())


async def on_friends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id, name = who(update)
    _, invited = await asyncio.to_thread(api_friends, user_id, name)

    link = f"https://t.me/{context.bot.username}?start=ref_{user_id}"
    text = (
        "рџ‘Ґ <b>Р”Р РЈР—Р¬РЇ</b>\n\n"
        f"РџСЂРёРіР»Р°С€РµРЅРѕ РѕС…РѕС‚РЅРёРєРѕРІ: <b>{invited}</b>\n\n"
        f"Р—Р° РєР°Р¶РґРѕРіРѕ РґСЂСѓРіР°: <b>+{REFERRAL_INVITER_BONUS} BNT</b> С‚РµР±Рµ "
        f"Рё <b>+{REFERRAL_NEW_BONUS} BNT</b> РµРјСѓ.\n\n"
        f"рџ”— РўРІРѕСЏ СЃСЃС‹Р»РєР°:\n<code>{esc(link)}</code>"
    )
    await show(query, text, back_menu())


async def on_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id, name = who(update)
    row = await asyncio.to_thread(api_profile, user_id, name)
    text, keyboard = bonus_view(row)
    await show(query, text, keyboard)


async def on_claim_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id, name = who(update)
    res = await asyncio.to_thread(api_claim_bonus, user_id, name)

    if res["status"] == "ok":
        await query.answer(
            f"рџЋЃ +{res['reward']:,} BNT Рё +{DAILY_ENERGY} СЌРЅРµСЂРіРёРё! РЎРµСЂРёСЏ: {res['streak']}",
            show_alert=True,
        )
    else:
        await query.answer("РЎРµРіРѕРґРЅСЏ Р±РѕРЅСѓСЃ СѓР¶Рµ РїРѕР»СѓС‡РµРЅ.")

    text, keyboard = bonus_view(res["player"])
    await show(query, text, keyboard)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error("Unhandled exception", exc_info=context.error)


# =========================
# Р—РђРџРЈРЎРљ
# =========================

def main():
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )
    # httpx РїРёС€РµС‚ РІ Р»РѕРі РїРѕР»РЅС‹Р№ URL Р·Р°РїСЂРѕСЃРѕРІ, Р° РІ РЅС‘Рј вЂ” С‚РѕРєРµРЅ Р±РѕС‚Р°
    logging.getLogger("httpx").setLevel(logging.WARNING)

    init_db()
    threading.Thread(target=run_web_server, daemon=True).start()

    app = Application.builder().token(TOKEN).concurrent_updates(True).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_command))

    routes = [
        (r"^menu$", on_menu),
        (r"^fish$", on_fish),
        (r"^inventory$", on_inventory),
        (r"^equipment$", on_equipment),
        (r"^upgrade:(rod|hook|line)$", on_upgrade),
        (r"^contracts$", on_contracts),
        (r"^claim:(\w+)$", on_claim),
        (r"^rating$", on_rating),
        (r"^friends$", on_friends),
        (r"^bonus$", on_bonus),
        (r"^claimbonus$", on_claim_bonus),
    ]
    for pattern, handler in routes:
        app.add_handler(CallbackQueryHandler(handler, pattern=pattern))

    app.add_error_handler(on_error)

    log.info("рџЋЈ BOUNTY bot starting...")
    app.run_polling(
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
