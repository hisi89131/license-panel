import random
import string
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from database import SessionLocal
from models import User, License
from config import BOT_TOKEN, MAIN_ADMINS


# ================= DB =================

def db():
    return SessionLocal()


# ================= PRICE TABLE =================

PRICE_TABLE = {
    "5H": {"label": "5 Hours", "hours": 5, "price": 50},
    "1D": {"label": "1 Day", "hours": 24, "price": 99},
    "3D": {"label": "3 Days", "hours": 72, "price": 249},
    "7D": {"label": "7 Days", "hours": 168, "price": 499},
    "15D": {"label": "15 Days", "hours": 360, "price": 699},
    "30D": {"label": "30 Days", "hours": 720, "price": 999},
    "60D": {"label": "60 Days", "hours": 1440, "price": 1499},
}


# ================= ROLE PROTECTION =================

MAIN_ONLY_ACTIONS = {
    "addsub", "removesub", "addbal",
    "adminlist", "searchkey",
    "editprice", "delkey",
    "resetkey", "blockkey", "restorekey"
}


# ================= MENU =================

async def show_main_menu(update, context, edit=False):
    session = db()
    tg = update.effective_user

    user = session.query(User).filter_by(telegram_id=str(tg.id)).first()

    if not user:
        if str(tg.id) in MAIN_ADMINS:
            user = User(
                telegram_id=str(tg.id),
                username=tg.username,
                role="main_admin",
                balance=0,
            )
            session.add(user)
            session.commit()
        else:
            await update.message.reply_text("Access Denied ❌")
            return

    user.username = tg.username
    session.commit()

    if user.role == "main_admin":
        buttons = [
            ["🔑 Generate", "gen"],
            ["📂 My Keys", "my"],
            ["➕ Add Sub", "addsub"],
            ["➖ Remove Sub", "removesub"],
            ["💰 Add Balance", "addbal"],
            ["📊 Admin List", "adminlist"],
            ["🔎 Search Key", "searchkey"],
            ["💲 Edit Price", "editprice"],
            ["🗑 Delete Key", "delkey"],
            ["🔁 Reset Key", "resetkey"],
            ["🚫 Block Key", "blockkey"],
            ["♻ Restore Key", "restorekey"],
        ]
    else:
        buttons = [
            ["🔑 Generate", "gen"],
            ["📂 My Keys", "my"],
            ["💰 Check Balance", "bal"],
        ]

    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(t, callback_data=d)] for t, d in buttons]
    )

    if edit:
        await update.callback_query.edit_message_text("🎓 Panel", reply_markup=markup)
    else:
        await update.message.reply_text("🎓 Panel", reply_markup=markup)


# ================= BUTTON HANDLER =================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    session = db()
    tg = update.effective_user
    user = session.query(User).filter_by(telegram_id=str(tg.id)).first()

    data = q.data

    if data == "back":
        context.user_data.clear()
        await show_main_menu(update, context, edit=True)
        return

    # Role protection
    if data in MAIN_ONLY_ACTIONS and user.role != "main_admin":
        await q.answer("Not allowed ❌", show_alert=True)
        return

    # GENERATE FLOW
    if data == "gen":
        buttons = [
            [InlineKeyboardButton(
                f"{v['label']} - {v['price']} Rs",
                callback_data=f"dur_{k}"
            )]
            for k, v in PRICE_TABLE.items()
        ]
        buttons.append([InlineKeyboardButton("⬅ Back", callback_data="back")])
        await q.edit_message_text("Choose Duration:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data.startswith("dur_"):
        context.user_data.clear()
        context.user_data["duration"] = data.split("_")[1]
        buttons = [
            [InlineKeyboardButton("Automatic", callback_data="auto")],
            [InlineKeyboardButton("Custom", callback_data="custom")],
            [InlineKeyboardButton("⬅ Back", callback_data="gen")],
        ]
        await q.edit_message_text("Select Key Type:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data == "auto":
        context.user_data["key_type"] = "auto"
        await q.edit_message_text("Send device count:")
        return

    if data == "custom":
        context.user_data["key_type"] = "custom"
        context.user_data["await_custom"] = True
        await q.edit_message_text("Send custom key:")
        return

    # MY KEYS
    if data == "my":
        licenses = session.query(License).filter_by(owner_id=str(tg.id)).all()
        text = "No keys found." if not licenses else "\n".join(
            [f"`{l.key}` | {l.status}" for l in licenses]
        )
        await q.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅ Back", callback_data="back")]]
            )
        )
        return

    # BALANCE
    if data == "bal":
        await q.edit_message_text(
            f"💰 Balance: {user.balance}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅ Back", callback_data="back")]]
            )
        )
        return

    # ADMIN LIST
    if data == "adminlist":
        subs = session.query(User).filter_by(role="sub_admin").all()

        if not subs:
            await q.edit_message_text("No sub admins.")
            return

        buttons = []
        text = ""

        for s in subs:
            total = session.query(License).filter_by(owner_id=s.telegram_id).count()
            uname = f"@{s.username}" if s.username else "No Username"

            text += (
                f"{uname}\n"
                f"ID: `{s.telegram_id}`\n"
                f"Balance: {s.balance}\n"
                f"Keys: {total}\n\n"
            )

            buttons.append([
                InlineKeyboardButton(
                    f"View Keys ({s.telegram_id})",
                    callback_data=f"view_{s.telegram_id}"
                )
            ])

        buttons.append([InlineKeyboardButton("⬅ Back", callback_data="back")])

        await q.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if data.startswith("view_"):
        sub_id = data.split("_")[1]
        licenses = session.query(License).filter_by(owner_id=sub_id).all()
        text = "No keys found." if not licenses else "\n".join(
            [f"`{l.key}` | {l.status}" for l in licenses]
        )
        await q.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅ Back", callback_data="adminlist")]]
            )
        )
        return

    # SIMPLE ACTIONS
    if data in MAIN_ONLY_ACTIONS:
        context.user_data["action"] = data
        await q.edit_message_text("Send required input:")
        return


# ================= TEXT HANDLER =================

async def texts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = db()
    tg = update.effective_user
    user = session.query(User).filter_by(telegram_id=str(tg.id)).first()
    text = update.message.text.strip()

    # CUSTOM KEY INPUT
    if context.user_data.get("await_custom"):
        context.user_data["custom_key"] = text
        context.user_data.pop("await_custom")
        await update.message.reply_text("Send device count:")
        return

    # GENERATE FINAL
    if "duration" in context.user_data:
        try:
            device = int(text)
        except:
            await update.message.reply_text("Send valid number.")
            return

        code = context.user_data["duration"]
        data = PRICE_TABLE[code]
        price = data["price"] * device

        if user.role != "main_admin":
            if user.balance < price:
                await update.message.reply_text("Insufficient balance.")
                return
            user.balance -= price

        if context.user_data.get("key_type") == "custom":
            key = context.user_data["custom_key"]
        else:
            key = code + "-" + "".join(
                random.choices(string.ascii_uppercase + string.digits, k=10)
            )

        # Duplicate check
        if session.query(License).filter_by(key=key).first():
            await update.message.reply_text("Key already exists ❌")
            context.user_data.clear()
            return

        lic = License(
            key=key,
            owner_id=str(tg.id),
            duration_hours=data["hours"],
            device_limit=device,
            price=price,
            expiry=datetime.utcnow() + timedelta(hours=data["hours"]),
            status="active",
        )

        session.add(lic)
        session.commit()
        context.user_data.clear()

        await update.message.reply_text(f"✅ Key Generated\n\n`{key}`", parse_mode="Markdown")
        return

    # ACTION ROUTER
    action = context.user_data.get("action")

    if not action:
        return

    # ADD SUB
    if action == "addsub":
        if session.query(User).filter_by(telegram_id=text).first():
            await update.message.reply_text("Already exists ❌")
        else:
            session.add(User(telegram_id=text, role="sub_admin", balance=0))
            session.commit()
            await update.message.reply_text("Sub Admin Added ✅")
        context.user_data.clear()
        return

    # REMOVE SUB
    if action == "removesub":
        sub = session.query(User).filter_by(telegram_id=text).first()
        if sub and sub.role == "sub_admin":
            session.delete(sub)
            session.commit()
            await update.message.reply_text("Removed ✅")
        else:
            await update.message.reply_text("Not found.")
        context.user_data.clear()
        return

    # ADD BALANCE
    if action == "addbal":
        try:
            sub_id, amount = text.split()
            sub = session.query(User).filter_by(telegram_id=sub_id).first()
            if not sub:
                await update.message.reply_text("Sub not found ❌")
            else:
                sub.balance += float(amount)
                session.commit()
                await update.message.reply_text("Balance Added ✅")
        except:
            await update.message.reply_text("Format: ID AMOUNT")
        context.user_data.clear()
        return

    # SEARCH KEY
    if action == "searchkey":
        lic = session.query(License).filter_by(key=text).first()
        if not lic:
            await update.message.reply_text("Key not found.")
        else:
            await update.message.reply_text(
                f"Key: `{lic.key}`\nOwner: {lic.owner_id}\nStatus: {lic.status}\nDevices: {lic.device_limit}\nExpiry: {lic.expiry}",
                parse_mode="Markdown"
            )
        context.user_data.clear()
        return

    # EDIT PRICE
    if action == "editprice":
        try:
            code, new_price = text.split()
            PRICE_TABLE[code]["price"] = float(new_price)
            await update.message.reply_text("Price Updated ✅")
        except:
            await update.message.reply_text("Format: CODE PRICE")
        context.user_data.clear()
        return

    # KEY CONTROLS
    if action in ["delkey", "resetkey", "blockkey", "restorekey"]:
        lic = session.query(License).filter_by(key=text).first()
        if not lic:
            await update.message.reply_text("Key not found.")
        else:
            if action == "delkey":
                lic.status = "deleted"
            elif action == "resetkey":
                lic.device_limit = 0
            elif action == "blockkey":
                lic.status = "blocked"
            elif action == "restorekey":
                lic.status = "active"
            session.commit()
            await update.message.reply_text("Done ✅")
        context.user_data.clear()
        return


# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", show_main_menu))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, texts))
    app.run_polling()


if __name__ == "__main__":
    main()
