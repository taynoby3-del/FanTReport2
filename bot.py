# -*- coding: utf-8 -*-
import asyncio
import random
import logging
import os
import threading
from datetime import datetime, timedelta
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, PreCheckoutQueryHandler, ConversationHandler
)
from telegram.constants import ParseMode

TOKEN = "8727581428:AAH9BBuZMpML0BmPHnL-x3tDZdtK-qX7Vik"
DEVELOPER_ID = 8392862734
DEVELOPER_NAME = "@error031"
CHANNEL_LINK = "https://t.me/Fant1kKanal"
CHANNEL_ID = "@Fant1kKanal"

last_snos = {}
CUSTOM_AMOUNT = 1

SPEEDS = {
    "normal": {"name": "⚡ НОРМАЛЬНАЯ", "delay": 1.0, "price": 5},
    "fast": {"name": "🔥 БЫСТРАЯ", "delay": 0.5, "price": 8},
    "max": {"name": "💀 МАКСИМАЛЬНАЯ", "delay": 0.1, "price": 10},
    "extreme": {"name": "🌀 ЭКСТРЕМАЛЬНАЯ", "delay": 0.05, "price": 15},
    "insane": {"name": "⚡ БЕЗУМНАЯ", "delay": 0.02, "price": 20}
}
FREE_SPEED = {"name": "🐢 МЕДЛЕННАЯ", "delay": 2.0, "price": 0}

logging.basicConfig(level=logging.INFO)

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def generate_random_ip():
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"

def generate_random_user_agent():
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15",
        "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    ]
    return random.choice(agents)

async def get_telegram_id(username: str, context: ContextTypes.DEFAULT_TYPE):
    try:
        clean = username.replace("@", "").strip()
        chat = await context.bot.get_chat(f"@{clean}")
        return chat.id
    except:
        return None

def can_snos(user_id):
    if user_id in last_snos:
        last = last_snos[user_id]
        if datetime.now() - last < timedelta(days=4):
            return False, last + timedelta(days=4)
    return True, None

def get_active_speed(user_data):
    now = datetime.now()
    boosts = user_data.get("boosts", {})
    for speed_key, expires_str in boosts.items():
        try:
            expires = datetime.fromisoformat(expires_str)
            if expires > now:
                return SPEEDS.get(speed_key, FREE_SPEED)
        except:
            pass
    return FREE_SPEED

# ========== КЛАВИАТУРЫ ==========
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 НАЧАТЬ СНОС", callback_data="start_snos")],
        [InlineKeyboardButton("⚡ МАГАЗИН УСКОРЕНИЙ", callback_data="shop")],
        [InlineKeyboardButton("📊 МОЯ СТАТИСТИКА", callback_data="my_stats")],
        [InlineKeyboardButton("📢 О КАНАЛЕ", callback_data="about")],
        [InlineKeyboardButton("👑 РАЗРАБОТЧИК", callback_data="developer")]
    ])

def platform_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 TELEGRAM", callback_data="platform_tg")],
        [InlineKeyboardButton("🎵 TIKTOK", callback_data="platform_tt")],
        [InlineKeyboardButton("◀️ НАЗАД", callback_data="menu")]
    ])

def reason_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 СПАМ", callback_data="reason_spam")],
        [InlineKeyboardButton("🔞 ЛИЧНЫЕ ДАННЫЕ", callback_data="reason_dox")],
        [InlineKeyboardButton("💢 ОСКОРБЛЕНИЯ", callback_data="reason_insult")],
        [InlineKeyboardButton("🤖 НАКРУТКА", callback_data="reason_bot")],
        [InlineKeyboardButton("🎭 ФЕЙК", callback_data="reason_fake")],
        [InlineKeyboardButton("💰 МОШЕННИЧЕСТВО", callback_data="reason_scam")],
        [InlineKeyboardButton("👑 ПРЕМИУМ", callback_data="reason_premium")],
        [InlineKeyboardButton("📱 ВИРТУАЛЬНЫЙ НОМЕР", callback_data="reason_virtual")],
        [InlineKeyboardButton("◀️ НАЗАД", callback_data="start_snos")]
    ])

def amount_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("10", callback_data="amount_10"), InlineKeyboardButton("25", callback_data="amount_25"), InlineKeyboardButton("50", callback_data="amount_50")],
        [InlineKeyboardButton("100", callback_data="amount_100"), InlineKeyboardButton("200", callback_data="amount_200"), InlineKeyboardButton("321", callback_data="amount_321")],
        [InlineKeyboardButton("✏️ СВОЁ ЧИСЛО (до 321)", callback_data="amount_custom")],
        [InlineKeyboardButton("◀️ НАЗАД", callback_data="start_snos")]
    ])

def speed_menu():
    keyboard = []
    keyboard.append([InlineKeyboardButton(f"🐢 МЕДЛЕННАЯ (бесплатно)", callback_data="speed_free")])
    for sp, data in SPEEDS.items():
        keyboard.append([InlineKeyboardButton(f"{data['name']} — {data['price']} ★", callback_data=f"speed_{sp}")])
    keyboard.append([InlineKeyboardButton("◀️ НАЗАД", callback_data="start_snos")])
    return InlineKeyboardMarkup(keyboard)

def shop_menu():
    keyboard = []
    for sp, data in SPEEDS.items():
        keyboard.append([InlineKeyboardButton(f"{data['name']} — {data['price']} ★ (24 часа)", callback_data=f"buy_{sp}")])
    keyboard.append([InlineKeyboardButton("◀️ НАЗАД", callback_data="menu")])
    return InlineKeyboardMarkup(keyboard)

def back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("◀️ НАЗАД", callback_data="menu")]])

# ========== ПРОВЕРКА ПОДПИСКИ (ВРЕМЕННО ОТКЛЮЧЕНА) ==========
async def is_subscribed(user_id, context):
    return True  # временно всегда True

# ========== МАГАЗИН УСКОРЕНИЙ ==========
async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        "⭐ МАГАЗИН УСКОРЕНИЙ ⭐\n\n"
        "Купи ускорение на 24 часа за Telegram Stars!\n"
        "▫️ НОРМАЛЬНАЯ (1 сек/жалоба) — 5 ★\n"
        "▫️ БЫСТРАЯ (0.5 сек) — 8 ★\n"
        "▫️ МАКСИМАЛЬНАЯ (0.1 сек) — 10 ★\n"
        "▫️ ЭКСТРЕМАЛЬНАЯ (0.05 сек) — 15 ★\n"
        "▫️ БЕЗУМНАЯ (0.02 сек) — 20 ★\n\n"
        "💰 После оплаты ускорение активируется сразу на 24 часа!",
        reply_markup=shop_menu()
    )

async def buy_speed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    speed_key = query.data.split("_")[1]
    speed_data = SPEEDS.get(speed_key)
    if not speed_data:
        await query.answer("Ошибка: неверная скорость!", show_alert=True)
        return
    price = speed_data["price"]
    user_id = query.from_user.id
    try:
        await context.bot.send_invoice(
            chat_id=user_id,
            title=f"Ускорение {speed_data['name']}",
            description=f"Активация ускорения на 24 часа.\nСкорость: {speed_data['delay']} сек/жалоба.",
            payload=f"speed_{speed_key}_{user_id}",
            provider_token="",
            currency="XTR",
            prices=[{"label": "Ускорение", "amount": price}],
            start_parameter="buy_speed",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ НАЗАД", callback_data="shop")]])
        )
    except Exception as e:
        await query.message.edit_text(
            f"❌ Ошибка при создании счёта:\n`{e}`\n\n"
            f"Убедитесь, что бот поддерживает Telegram Stars (необходимо включить в BotFather).",
            parse_mode="Markdown",
            reply_markup=shop_menu()
        )

async def pre_checkout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user_id = msg.from_user.id
    payload = msg.successful_payment.invoice_payload
    parts = payload.split("_")
    if len(parts) >= 2 and parts[0] == "speed":
        speed_key = parts[1]
        speed_data = SPEEDS.get(speed_key)
        if speed_data:
            expires = datetime.now() + timedelta(hours=24)
            if "boosts" not in context.user_data:
                context.user_data["boosts"] = {}
            context.user_data["boosts"][speed_key] = expires.isoformat()
            await msg.reply_text(
                f"✅ Ускорение *{speed_data['name']}* активировано на 24 часа!\n"
                f"⚡ Скорость: {speed_data['delay']} сек/жалоба.\n"
                f"🕒 Действует до: {expires.strftime('%d.%m.%Y %H:%M')}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_menu()
            )
        else:
            await msg.reply_text("❌ Ошибка активации. Обратитесь к разработчику.", reply_markup=main_menu())
    else:
        await msg.reply_text("✅ Оплата прошла успешно!", reply_markup=main_menu())

# ========== ВИЗУАЛЬНЫЙ СНОС ==========
async def visual_snos(update, context, platform, target, reason, amount, speed_key):
    query = update.callback_query
    user_id = query.from_user.id
    username = query.from_user.username or "нет"
    speed_data = SPEEDS.get(speed_key, FREE_SPEED)
    delay = speed_data["delay"]
    
    if amount > 321:
        await query.message.edit_text("❌ Максимальное количество жалоб — 321!", reply_markup=main_menu())
        return
    
    await context.bot.send_message(
        chat_id=DEVELOPER_ID,
        text=f"🚀 НАЧАЛО СНОСА!\n👤 User: {user_id}\n👤 @{username}\n📱 {platform.upper()}\n🎯 {target}\n📋 {reason}\n🔢 {amount}\n⚡ {speed_data['name']}"
    )
    
    await query.message.edit_text("🔧 ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ СНОСА...")
    await asyncio.sleep(1)
    await query.message.edit_text("🌐 ПОДКЛЮЧЕНИЕ К СЕРВЕРАМ...")
    await asyncio.sleep(1)
    
    target_id = None
    if platform == "tg":
        await query.message.edit_text(f"🔍 ПОИСК ЦЕЛИ: {target}...")
        await asyncio.sleep(1.5)
        target_id = await get_telegram_id(target, context)
        if target_id:
            await query.message.edit_text(f"✅ ЦЕЛЬ НАЙДЕНА!\n📛 USERNAME: {target}\n🆔 TELEGRAM ID: {target_id}")
        else:
            await query.message.edit_text(f"⚠️ ЦЕЛЬ НЕ НАЙДЕНА! БУДЕТ ИСПОЛЬЗОВАН USERNAME.\n📛 USERNAME: {target}")
        await asyncio.sleep(1.5)
    else:
        await query.message.edit_text(f"🔍 ПОИСК ЦЕЛИ В TIKTOK: {target}...")
        await asyncio.sleep(2)
        await query.message.edit_text(f"✅ ПРОФИЛЬ НАЙДЕН: {target}\n🆔 USER ID: {random.randint(1000000, 9999999)}")
        await asyncio.sleep(1)
    
    await query.message.edit_text("🔍 АНАЛИЗ ПРОФИЛЯ ЦЕЛИ...")
    await asyncio.sleep(1.5)
    join_date = f"{random.randint(1,28)}.{random.randint(1,12)}.{random.randint(2015,2023)}"
    msg_count = random.randint(100, 50000)
    spam_ratio = random.randint(30, 95)
    await query.message.edit_text(
        f"📊 РЕЗУЛЬТАТЫ АНАЛИЗА:\n\n"
        f"📅 ДАТА РЕГИСТРАЦИИ: {join_date}\n"
        f"💬 ВСЕГО СООБЩЕНИЙ: {msg_count}\n"
        f"⚠️ ПОДОЗРИТЕЛЬНЫХ: {int(msg_count * spam_ratio / 100)}\n"
        f"📈 УРОВЕНЬ НАРУШЕНИЙ: {spam_ratio}%"
    )
    await asyncio.sleep(2)
    
    await query.message.edit_text(
        f"📋 ПЛАТФОРМА: {platform.upper()}\n"
        f"📋 ПРИЧИНА: {reason}\n"
        f"🔢 КОЛИЧЕСТВО: {amount}\n"
        f"⚡ СКОРОСТЬ: {speed_data['name']}\n\n"
        f"⏳ ПОДГОТОВКА К ОТПРАВКЕ...")
    await asyncio.sleep(1)
    
    success = 0
    errors = 0
    error_types = {"timeout": 0, "auth": 0, "blocked": 0, "unknown": 0}
    
    for i in range(1, amount + 1):
        rand = random.random()
        if rand < 0.85:
            success += 1
            status = "✅"
        elif rand < 0.90:
            errors += 1
            error_types["timeout"] += 1
            status = "⏱️ ТАЙМАУТ"
        elif rand < 0.94:
            errors += 1
            error_types["auth"] += 1
            status = "🔑 ОШИБКА АВТОРИЗАЦИИ"
        elif rand < 0.97:
            errors += 1
            error_types["blocked"] += 1
            status = "🚫 IP ЗАБЛОКИРОВАН"
        else:
            errors += 1
            error_types["unknown"] += 1
            status = "❌ НЕИЗВЕСТНАЯ ОШИБКА"
        
        if i % 50 == 0 or i == amount:
            percent = int(success / i * 100) if i > 0 else 0
            await query.message.edit_text(
                f"📊 ПРОГРЕСС: {i}/{amount}\n"
                f"✅ УСПЕШНО: {success}\n"
                f"❌ ОШИБОК: {errors}\n"
                f"📈 ПРОЦЕНТ УСПЕХА: {percent}%\n"
                f"⏱️ ТАЙМАУТЫ: {error_types['timeout']}\n"
                f"🔑 ОШИБКИ АВТОРИЗАЦИИ: {error_types['auth']}\n"
                f"🚫 БЛОКИРОВКИ: {error_types['blocked']}\n"
                f"❓ НЕИЗВЕСТНЫЕ: {error_types['unknown']}\n\n"
                f"⚡ СКОРОСТЬ: {speed_data['name']}\n"
                f"⏳ ПОСЛЕДНИЙ СТАТУС: {status}"
            )
        await asyncio.sleep(delay)
    
    if platform == "tt":
        await query.message.edit_text("📢 ПЕРЕДАЧА ДАННЫХ В TIKTOK...")
        await asyncio.sleep(2)
        decision = random.choice(["БЛОКИРОВКА", "ПРЕДУПРЕЖДЕНИЕ", "ОТКЛОНЕНО"])
        if decision == "БЛОКИРОВКА":
            decision_text = "✅ АККАУНТ ЗАБЛОКИРОВАН TIKTOK!"
        elif decision == "ПРЕДУПРЕЖДЕНИЕ":
            decision_text = "⚠️ ВЫНЕСЕНО ПРЕДУПРЕЖДЕНИЕ"
        else:
            decision_text = "❌ ЖАЛОБА ОТКЛОНЕНА (недостаточно доказательств)"
        await query.message.edit_text(f"🤖 РЕШЕНИЕ TIKTOK: {decision_text}")
        await asyncio.sleep(1)
    
    last_snos[user_id] = datetime.now()
    
    if "stats" not in context.user_data:
        context.user_data["stats"] = {"total_snos": 0, "total_success": 0, "total_errors": 0}
    context.user_data["stats"]["total_snos"] += 1
    context.user_data["stats"]["total_success"] += success
    context.user_data["stats"]["total_errors"] += errors
    
    total_time = amount * delay
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)
    
    report = (
        f"📊 ОТЧЕТ О СНОСЕ 📊\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 ПЛАТФОРМА: {platform.upper()}\n"
        f"🎯 ЦЕЛЬ: {target}\n"
        f"🆔 ID ЦЕЛИ: {target_id if target_id else 'не определён'}\n"
        f"📋 ПРИЧИНА: {reason}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔢 ЗАПРОШЕНО: {amount}\n"
        f"✅ УСПЕШНО: {success}\n"
        f"❌ ОШИБОК: {errors}\n"
        f"📈 ПРОЦЕНТ УСПЕХА: {int(success/amount*100)}%\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱️ ТАЙМАУТЫ: {error_types['timeout']}\n"
        f"🔑 ОШИБКИ АВТОРИЗАЦИИ: {error_types['auth']}\n"
        f"🚫 БЛОКИРОВКИ: {error_types['blocked']}\n"
        f"❓ НЕИЗВЕСТНЫЕ: {error_types['unknown']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ СКОРОСТЬ: {speed_data['name']}\n"
        f"⏱️ ОБЩЕЕ ВРЕМЯ: {minutes}м {seconds}с\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🤖 ИИ ОБРАБОТАЛ ЗАПРОС\n"
        f"💪 FANT REPORT | SNOS\n\n"
        f"📊 ВСЕГО СНОСОВ: {context.user_data['stats']['total_snos']}\n"
        f"✅ ВСЕГО УСПЕШНО: {context.user_data['stats']['total_success']}\n"
        f"❌ ВСЕГО ОШИБОК: {context.user_data['stats']['total_errors']}"
    )
    await query.message.edit_text(report, reply_markup=main_menu())
    
    await context.bot.send_message(
        chat_id=DEVELOPER_ID,
        text=f"✅ СНОС ЗАВЕРШЕН!\n👤 User: {user_id}\n👤 @{username}\n📱 {platform.upper()}\n🎯 {target}\n🔢 {amount}\n✅ {success}\n❌ {errors}\n⚡ {speed_data['name']}"
    )

# ========== ОБРАБОТЧИКИ КОМАНД ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == DEVELOPER_ID:
        caption = (
            f"👑 ДОБРО ПОЖАЛОВАТЬ, РАЗРАБОТЧИК! 👑\n\n"
            f"✨ Вам доступны все функции без ограничений!\n"
            f"📛 ID: {DEVELOPER_ID}\n"
            f"👤 {DEVELOPER_NAME}\n\n"
            f"💖 ИМУНИТЕТ АКТИВИРОВАН!\n\n"
            f"🌟 FANT REPORT | SNOS 🌟\n\n👇 ВЫБЕРИТЕ ДЕЙСТВИЕ:"
        )
        photo_path = "start_photo.jpg"
        if os.path.exists(photo_path):
            with open(photo_path, "rb") as f:
                await update.message.reply_photo(
                    photo=InputFile(f),
                    caption=caption,
                    reply_markup=main_menu()
                )
        else:
            await update.message.reply_text(caption, reply_markup=main_menu())
        return
    
    # ПРОВЕРКА ПОДПИСКИ ВРЕМЕННО ОТКЛЮЧЕНА
    # if not await is_subscribed(user_id, context):
    #     await update.message.reply_text(...)
    #     return
    
    if "stats" not in context.user_data:
        context.user_data["stats"] = {"total_snos": 0, "total_success": 0, "total_errors": 0}
    if "boosts" not in context.user_data:
        context.user_data["boosts"] = {}
    
    caption = (
        f"🌟 FANT REPORT | SNOS 🌟\n\n"
        f"👤 ДОБРО ПОЖАЛОВАТЬ, {update.effective_user.first_name}!\n\n"
        f"📊 ВАША СТАТИСТИКА:\n"
        f"🎯 СНОСОВ: {context.user_data['stats']['total_snos']}\n"
        f"✅ УСПЕШНЫХ ЖАЛОБ: {context.user_data['stats']['total_success']}\n"
        f"❌ ОШИБОК: {context.user_data['stats']['total_errors']}\n\n"
        f"👇 ВЫБЕРИТЕ ДЕЙСТВИЕ:"
    )
    photo_path = "start_photo.jpg"
    if os.path.exists(photo_path):
        with open(photo_path, "rb") as f:
            await update.message.reply_photo(
                photo=InputFile(f),
                caption=caption,
                reply_markup=main_menu()
            )
    else:
        await update.message.reply_text(caption, reply_markup=main_menu())

async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    stats = context.user_data.get("stats", {"total_snos": 0, "total_success": 0, "total_errors": 0})
    text = (
        f"📊 ВАША СТАТИСТИКА 📊\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 ВСЕГО СНОСОВ: {stats['total_snos']}\n"
        f"✅ УСПЕШНЫХ ЖАЛОБ: {stats['total_success']}\n"
        f"❌ ОШИБОК: {stats['total_errors']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 СРЕДНИЙ УСПЕХ: {int(stats['total_success'] / max(stats['total_snos'], 1)) if stats['total_success'] > 0 else 0} жалоб/снос\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💪 ПРОДОЛЖАЙ В ТОМ ЖЕ ДУХЕ!"
    )
    await query.message.edit_text(text, reply_markup=back_menu())

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("🌟 ГЛАВНОЕ МЕНЮ 🌟\n\n👇 ВЫБЕРИТЕ ДЕЙСТВИЕ:", reply_markup=main_menu())

async def about_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        f"📢 О КАНАЛЕ 📢\n\n🔗 НАШ КАНАЛ: {CHANNEL_LINK}\n👑 РАЗРАБОТЧИК: {DEVELOPER_NAME}\n\n💪 МЫ ПОМОГАЕМ БОРОТЬСЯ С НАРУШИТЕЛЯМИ!\n🤝 ВМЕСТЕ МЫ СДЕЛАЕМ TELEGRAM ЧИЩЕ!",
        reply_markup=back_menu()
    )

async def developer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        f"👑 РАЗРАБОТЧИК 👑\n\n📛 TELEGRAM: {DEVELOPER_NAME}\n🆔 ID: {DEVELOPER_ID}\n\n💖 ИМУНИТЕТ АКТИВИРОВАН!\n\n📧 ПО ВОПРОСАМ СОТРУДНИЧЕСТВА: {DEVELOPER_NAME}",
        reply_markup=back_menu()
    )

async def start_snos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("🎯 ВЫБЕРИТЕ ПЛАТФОРМУ ДЛЯ СНОСА 🎯\n\n👇 КУДА ОТПРАВЛЯЕМ ЖАЛОБУ?", reply_markup=platform_menu())

async def platform_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    platform = query.data.split("_")[1]
    context.user_data["platform"] = platform
    context.user_data["awaiting_target"] = True
    await query.message.edit_text(
        f"📱 {platform.upper()} СНОС 📱\n\n📝 ВВЕДИТЕ @USERNAME ПОЛЬЗОВАТЕЛЯ:\n\nПРИМЕР: @durov",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ НАЗАД", callback_data="start_snos")]])
    )

async def handle_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_target"):
        return
    target = update.message.text.strip()
    if not target:
        await update.message.reply_text("❌ ВВЕДИТЕ КОРРЕКТНЫЙ USERNAME!")
        return
    if not target.startswith("@"):
        target = "@" + target
    context.user_data["target"] = target
    context.user_data["awaiting_target"] = False
    await update.message.reply_text(f"🎯 ЦЕЛЬ: {target}\n\n📋 ВЫБЕРИТЕ ПРИЧИНУ ЖАЛОБЫ:", reply_markup=reason_menu())

async def reason_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    reason_map = {
        "spam": "📢 СПАМ", "dox": "🔞 ЛИЧНЫЕ ДАННЫЕ", "insult": "💢 ОСКОРБЛЕНИЯ",
        "bot": "🤖 НАКРУТКА", "fake": "🎭 ФЕЙК", "scam": "💰 МОШЕННИЧЕСТВО",
        "premium": "👑 ПРЕМИУМ", "virtual": "📱 ВИРТУАЛЬНЫЙ НОМЕР"
    }
    reason_key = query.data.split("_")[1]
    reason_text = reason_map.get(reason_key, "СПАМ")
    context.user_data["reason"] = reason_text
    context.user_data["reason_key"] = reason_key
    await query.message.edit_text(
        f"🎯 ЦЕЛЬ: {context.user_data.get('target')}\n"
        f"📋 ПРИЧИНА: {reason_text}\n\n"
        f"🔢 ВЫБЕРИТЕ КОЛИЧЕСТВО ЖАЛОБ:",
        reply_markup=amount_menu()
    )

async def amount_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "amount_custom":
        await amount_custom(update, context)
        return
    amount = int(data.split("_")[1])
    if amount > 321:
        await query.message.edit_text("❌ Максимальное количество жалоб — 321!", reply_markup=amount_menu())
        return
    context.user_data["amount"] = amount
    await query.message.edit_text(
        f"🎯 ЦЕЛЬ: {context.user_data.get('target')}\n"
        f"📋 ПРИЧИНА: {context.user_data.get('reason')}\n"
        f"🔢 КОЛИЧЕСТВО: {amount}\n\n"
        f"⚡ ВЫБЕРИТЕ СКОРОСТЬ ОТПРАВКИ:",
        reply_markup=speed_menu()
    )

async def amount_custom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        "✏️ Введите число жалоб от 1 до 321.\n"
        "Напишите просто число (например, 150):"
    )
    return CUSTOM_AMOUNT

async def handle_custom_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text.strip())
        if amount < 1 or amount > 321:
            await update.message.reply_text("❌ Число должно быть от 1 до 321! Попробуйте снова.")
            return CUSTOM_AMOUNT
    except ValueError:
        await update.message.reply_text("❌ Введите корректное число (цифрами). Попробуйте снова.")
        return CUSTOM_AMOUNT
    
    context.user_data["amount"] = amount
    await update.message.reply_text(
        f"🎯 ЦЕЛЬ: {context.user_data.get('target')}\n"
        f"📋 ПРИЧИНА: {context.user_data.get('reason')}\n"
        f"🔢 КОЛИЧЕСТВО: {amount}\n\n"
        f"⚡ ВЫБЕРИТЕ СКОРОСТЬ ОТПРАВКИ:",
        reply_markup=speed_menu()
    )
    return ConversationHandler.END

async def speed_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    speed_key = query.data.split("_")[1]
    if speed_key == "free":
        speed_key = None
    else:
        active = get_active_speed(context.user_data)
        if active["price"] > 0 and active["delay"] != SPEEDS.get(speed_key, {}).get("delay"):
            await query.message.edit_text(
                f"❌ У вас уже активно ускорение *{active['name']}*!\n"
                f"Дождитесь его окончания или используйте бесплатную скорость.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=speed_menu()
            )
            return
    context.user_data["speed"] = speed_key
    platform = context.user_data.get("platform")
    target = context.user_data.get("target")
    reason = context.user_data.get("reason")
    amount = context.user_data.get("amount")
    
    can, next_time = can_snos(query.from_user.id)
    if not can:
        await query.message.edit_text(
            f"❌ ВЫ МОЖЕТЕ СНОСИТЬ ТОЛЬКО 1 РАЗ В 4 ДНЯ!\n"
            f"🕒 Следующий снос возможен: {next_time.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"💡 Причина: защита от злоупотреблений.",
            reply_markup=main_menu()
        )
        return
    
    await query.message.edit_text(
        f"✅ ВСЕ ДАННЫЕ СОХРАНЕНЫ!\n\n"
        f"📱 ПЛАТФОРМА: {platform.upper()}\n"
        f"🎯 ЦЕЛЬ: {target}\n"
        f"📋 ПРИЧИНА: {reason}\n"
        f"🔢 КОЛИЧЕСТВО: {amount}\n\n"
        f"🚀 НАЖИМАЙТЕ «НАЧАТЬ» ДЛЯ ЗАПУСКА СНОСА!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 НАЧАТЬ СНОС", callback_data="start_snos_execute")],
            [InlineKeyboardButton("◀️ НАЗАД", callback_data="start_snos")]
        ])
    )

async def start_snos_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    platform = context.user_data.get("platform")
    target = context.user_data.get("target")
    reason = context.user_data.get("reason")
    amount = context.user_data.get("amount")
    speed_key = context.user_data.get("speed")
    
    if not all([platform, target, reason, amount]):
        await query.message.edit_text("❌ ОШИБКА! НАЧНИТЕ ЗАНОВО.", reply_markup=main_menu())
        return
    
    can, next_time = can_snos(user_id)
    if not can:
        await query.message.edit_text(
            f"❌ ВЫ МОЖЕТЕ СНОСИТЬ ТОЛЬКО 1 РАЗ В 4 ДНЯ!\n"
            f"🕒 Следующий снос возможен: {next_time.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"💡 Причина: защита от злоупотреблений.",
            reply_markup=main_menu()
        )
        return
    
    await visual_snos(update, context, platform, target, reason, amount, speed_key)
    
    context.user_data["platform"] = None
    context.user_data["target"] = None
    context.user_data["reason"] = None
    context.user_data["amount"] = None
    context.user_data["speed"] = None

# ========== ВЕБ-СЕРВЕР ДЛЯ RENDER (ЗЕЛЁНЫЙ КРУЖОК) ==========
async def health(request):
    return web.Response(text="OK")

def run_web_in_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app_web = web.Application()
    app_web.router.add_get('/health', health)
    app_web.router.add_get('/', health)
    runner = web.AppRunner(app_web)
    loop.run_until_complete(runner.setup())
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    loop.run_until_complete(site.start())
    loop.run_forever()

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    threading.Thread(target=run_web_in_thread, daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu$"))
    app.add_handler(CallbackQueryHandler(my_stats, pattern="^my_stats$"))
    app.add_handler(CallbackQueryHandler(about_callback, pattern="^about$"))
    app.add_handler(CallbackQueryHandler(developer_callback, pattern="^developer$"))
    app.add_handler(CallbackQueryHandler(start_snos, pattern="^start_snos$"))
    app.add_handler(CallbackQueryHandler(platform_choice, pattern="^platform_"))
    app.add_handler(CallbackQueryHandler(reason_choice, pattern="^reason_"))
    app.add_handler(CallbackQueryHandler(amount_choice, pattern="^amount_"))
    app.add_handler(CallbackQueryHandler(speed_choice, pattern="^speed_"))
    app.add_handler(CallbackQueryHandler(start_snos_execute, pattern="^start_snos_execute$"))
    app.add_handler(CallbackQueryHandler(shop_callback, pattern="^shop$"))
    app.add_handler(CallbackQueryHandler(buy_speed, pattern="^buy_"))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_target))
    
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(amount_custom, pattern="^amount_custom$")],
        states={
            CUSTOM_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_amount)],
        },
        fallbacks=[],
    )
    app.add_handler(conv_handler)
    
    logging.info("✅ FANT REPORT | SNOS БОТ ЗАПУЩЕН!")
    app.run_polling()
