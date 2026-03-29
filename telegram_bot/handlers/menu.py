"""
Menu handler - Shaxsiy kabinet komandalar.

Komandalar:
  📋 Sotuvlarim   - So'nggi xaridlar ro'yxati
  💰 Qarzim       - Qarz holati
  👤 Profilim     - Shaxsiy ma'lumotlar
  📊 Statistika   - Umumiy statistika
  ⬅️ Orqaga      - Sahifalash uchun
"""

import logging
import httpx
from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command

from config import config
from handlers.start import main_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()

API_BASE = config.API_URL

PAYMENT_STATUS_MAP = {
    "paid": "✅ To'liq to'langan",
    "partial": "⚠️ Qisman to'langan",
    "unpaid": "🔴 To'lanmagan",
}


def fmt_money(amount) -> str:
    """Pulni formatlash."""
    try:
        return f"{float(amount):,.0f}".replace(",", " ")
    except Exception:
        return "0"


async def api_get(path: str, telegram_id: str, params: dict = None) -> dict:
    """API ga GET so'rov yuborish."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{API_BASE}{path}",
                headers={"X-Telegram-Id": str(telegram_id)},
                params=params or {}
            )
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                return {"success": False, "error": "not_registered"}
    except Exception as e:
        logger.error(f"API GET {path} error: {e}")
    return {"success": False, "error": "server_error"}


def not_registered_message() -> str:
    return (
        "❌ Siz hali ro'yxatdan o'tmagansiz.\n\n"
        "Ro'yxatdan o'tish uchun /start bosing va telefon raqamingizni yuboring."
    )


def server_error_message() -> str:
    return "⚠️ Server bilan bog'lanishda xatolik. Keyinroq urinib ko'ring."


# ===== 📋 SOTUVLARIM =====

@router.message(F.text == "📋 Sotuvlarim")
async def my_sales(message: Message):
    """So'nggi xaridlar ro'yxati."""
    telegram_id = str(message.from_user.id)
    await show_sales_page(message, telegram_id, page=1)


async def show_sales_page(message: Message, telegram_id: str, page: int):
    """Sotuvlar sahifasini ko'rsatish."""
    result = await api_get("/bot/my-sales", telegram_id, {"page": page, "per_page": 5})

    if not result.get("success"):
        err = result.get("error", "")
        text = not_registered_message() if err == "not_registered" else server_error_message()
        await message.answer(text)
        return

    sales = result.get("data", [])
    total = result.get("total", 0)
    total_pages = result.get("total_pages", 1)

    if not sales:
        await message.answer(
            "📋 Sizning xaridlaringiz hali mavjud emas.\n\n"
            "Birinchi xaridingizdan keyin bu yerda ko'rinadi.",
        )
        return

    lines = [f"📋 <b>Xaridlarim</b> ({total} ta)\n"]

    for sale in sales:
        status_icon = sale.get("status_icon", "")
        sale_num = sale.get("sale_number", "")
        sale_date = sale.get("sale_date", "")[:10]
        total_amount = fmt_money(sale.get("total_amount", 0))
        debt = float(sale.get("debt_amount", 0))

        lines.append(
            f"{'━' * 22}\n"
            f"🧾 <b>#{sale_num}</b> — {sale_date}\n"
            f"💵 Jami: <b>{total_amount} so'm</b>\n"
            f"{status_icon} {sale.get('status_text', '')}"
        )
        if debt > 0:
            lines.append(f"🔴 Qarz: <b>{fmt_money(debt)} so'm</b>")

        # Mahsulotlar preview
        items = sale.get("items_preview", [])
        if items:
            items_text = ", ".join(
                f"{it['product_name']} ({it['quantity']:.0f} {it['uom_symbol']})"
                for it in items[:2]
            )
            if sale.get("has_more_items"):
                items_text += f" va {sale.get('items_count', 0) - 2} ta boshqa"
            lines.append(f"📦 {items_text}")

        lines.append("")  # Bo'sh qator

    text = "\n".join(lines)

    # Sahifalash tugmalari
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"sales_page:{page-1}")
        )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"sales_page:{page+1}")
        )

    keyboard = None
    if nav_buttons:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[nav_buttons])

    if page == 1:
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data.startswith("sales_page:"))
async def sales_pagination(callback: CallbackQuery):
    """Sahifalash callback."""
    page = int(callback.data.split(":")[1])
    telegram_id = str(callback.from_user.id)

    result = await api_get("/bot/my-sales", telegram_id, {"page": page, "per_page": 5})

    if not result.get("success"):
        await callback.answer("Xatolik yuz berdi", show_alert=True)
        return

    sales = result.get("data", [])
    total = result.get("total", 0)
    total_pages = result.get("total_pages", 1)

    if not sales:
        await callback.answer("Boshqa xaridlar yo'q", show_alert=True)
        return

    lines = [f"📋 <b>Xaridlarim</b> ({total} ta) — Sahifa {page}/{total_pages}\n"]

    for sale in sales:
        status_icon = sale.get("status_icon", "")
        sale_num = sale.get("sale_number", "")
        sale_date = sale.get("sale_date", "")[:10]
        total_amount = fmt_money(sale.get("total_amount", 0))
        debt = float(sale.get("debt_amount", 0))

        lines.append(
            f"{'━' * 22}\n"
            f"🧾 <b>#{sale_num}</b> — {sale_date}\n"
            f"💵 Jami: <b>{total_amount} so'm</b>\n"
            f"{status_icon} {sale.get('status_text', '')}"
        )
        if debt > 0:
            lines.append(f"🔴 Qarz: <b>{fmt_money(debt)} so'm</b>")

        items = sale.get("items_preview", [])
        if items:
            items_text = ", ".join(
                f"{it['product_name']} ({it['quantity']:.0f} {it['uom_symbol']})"
                for it in items[:2]
            )
            if sale.get("has_more_items"):
                items_text += f" +{sale.get('items_count', 0) - 2} ta"
            lines.append(f"📦 {items_text}")

        lines.append("")

    text = "\n".join(lines)

    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"sales_page:{page-1}")
        )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"sales_page:{page+1}")
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[nav_buttons]) if nav_buttons else None

    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard)

    await callback.answer()


# ===== 💰 QARZIM =====

@router.message(F.text == "💰 Qarzim")
async def my_debt(message: Message):
    """Qarz holati va to'lovlar tarixi."""
    telegram_id = str(message.from_user.id)
    result = await api_get("/bot/my-debt", telegram_id)

    if not result.get("success"):
        err = result.get("error", "")
        text = not_registered_message() if err == "not_registered" else server_error_message()
        await message.answer(text)
        return

    data = result.get("data", {})
    current_debt = float(data.get("current_debt", 0))
    advance_balance = float(data.get("advance_balance", 0))
    debt_sales = data.get("debt_sales", [])
    history = data.get("history", [])
    company_phone = data.get("company_phone") or config.COMPANY_PHONE
    company_name = data.get("company_name") or config.COMPANY_NAME

    lines = ["💰 <b>Qarz holati</b>\n"]
    lines.append("═" * 22)

    if current_debt > 0:
        lines.append(f"🔴 Joriy qarz: <b>{fmt_money(current_debt)} so'm</b>")
    else:
        lines.append("✅ Hech qanday qarzingiz yo'q!")

    if advance_balance > 0:
        lines.append(f"📥 Avans balans: <b>{fmt_money(advance_balance)} so'm</b>")

    # Qarz bo'lgan sotuvlar
    if debt_sales:
        lines.append(f"\n📋 <b>Qarz bo'lgan xaridlar ({len(debt_sales)} ta):</b>")
        for sale in debt_sales[:5]:
            lines.append(
                f"  • #{sale['sale_number']} ({sale['sale_date'][:10]}) — "
                f"🔴 {fmt_money(sale['debt_amount'])} so'm"
            )
        if len(debt_sales) > 5:
            lines.append(f"  ... va {len(debt_sales) - 5} ta boshqa")

    # So'nggi harakatlar
    if history:
        lines.append(f"\n📊 <b>So'nggi harakatlar:</b>")
        for record in history[:6]:
            date_str = ""
            if record.get("date"):
                date_str = record["date"][:10]
            amount = float(record.get("amount", 0))
            type_text = record.get("type_text", "")
            balance_after = float(record.get("balance_after", 0))

            sign = "+" if "Xarid" in type_text else "-" if "To'lov" in type_text else ""
            lines.append(
                f"  {type_text} — {sign}{fmt_money(abs(amount))} so'm"
                f"  ({date_str}) | Qoldiq: {fmt_money(balance_after)} so'm"
            )

    lines.append("\n═" * 22)
    if company_phone:
        lines.append(f"📞 To'lov uchun: <b>{company_phone}</b>")

    await message.answer("\n".join(lines), parse_mode="HTML")


# ===== 👤 PROFILIM =====

@router.message(F.text == "👤 Profilim")
async def my_profile(message: Message):
    """Shaxsiy ma'lumotlar."""
    telegram_id = str(message.from_user.id)
    result = await api_get("/bot/my-profile", telegram_id)

    if not result.get("success"):
        err = result.get("error", "")
        text = not_registered_message() if err == "not_registered" else server_error_message()
        await message.answer(text)
        return

    c = result.get("data", {})
    company_name = c.get("company_name") or config.COMPANY_NAME
    company_phone = c.get("company_phone") or config.COMPANY_PHONE

    type_map = {
        "regular": "Oddiy mijoz",
        "vip": "⭐ VIP mijoz",
        "wholesale": "🏭 Ulgurji",
        "contractor": "🏗️ Pudratchi",
    }
    ctype = type_map.get(c.get("customer_type", "regular"), "Mijoz")

    lines = [
        "👤 <b>Mening profilim</b>\n",
        "═" * 22,
        f"📛 Ism: <b>{c.get('name', '')}</b>",
        f"📱 Telefon: <b>{c.get('phone', '')}</b>",
        f"🏷️ Tur: <b>{ctype}</b>",
    ]

    discount = float(c.get("personal_discount_percent", 0))
    if discount > 0:
        lines.append(f"🎁 Shaxsiy chegirma: <b>{discount:.1f}%</b>")

    lines.append("")
    lines.append("📊 <b>Statistika:</b>")
    lines.append(f"  🛒 Jami xaridlar: <b>{c.get('total_purchases_count', 0)} marta</b>")
    lines.append(f"  💵 Jami summa: <b>{fmt_money(c.get('total_purchases', 0))} so'm</b>")

    if c.get("last_purchase_date"):
        lines.append(f"  📅 Oxirgi xarid: <b>{c['last_purchase_date'][:10]}</b>")

    debt = float(c.get("current_debt", 0))
    advance = float(c.get("advance_balance", 0))

    lines.append("")
    if debt > 0:
        lines.append(f"🔴 Joriy qarz: <b>{fmt_money(debt)} so'm</b>")
    else:
        lines.append("✅ Qarz yo'q")

    if advance > 0:
        lines.append(f"📥 Avans: <b>{fmt_money(advance)} so'm</b>")

    lines.append(f"\n🏪 <b>{company_name}</b>")
    if company_phone:
        lines.append(f"📞 {company_phone}")

    await message.answer("\n".join(lines), parse_mode="HTML")


# ===== 📊 STATISTIKA =====

@router.message(F.text == "📊 Statistika")
async def my_stats(message: Message):
    """Umumiy statistika."""
    telegram_id = str(message.from_user.id)
    result = await api_get("/bot/my-profile", telegram_id)

    if not result.get("success"):
        err = result.get("error", "")
        text = not_registered_message() if err == "not_registered" else server_error_message()
        await message.answer(text)
        return

    c = result.get("data", {})
    total_p = float(c.get("total_purchases", 0))
    total_count = int(c.get("total_purchases_count", 0))
    debt = float(c.get("current_debt", 0))

    avg = total_p / total_count if total_count > 0 else 0

    lines = [
        "📊 <b>Mening statistikam</b>\n",
        "═" * 22,
        f"🛒 Jami xaridlar soni: <b>{total_count} ta</b>",
        f"💵 Jami xarid summasi: <b>{fmt_money(total_p)} so'm</b>",
        f"📈 O'rtacha xarid: <b>{fmt_money(avg)} so'm</b>",
        "",
    ]

    if debt > 0:
        lines.append(f"🔴 Joriy qarz: <b>{fmt_money(debt)} so'm</b>")
    else:
        lines.append("✅ Qarz yo'q — ajoyib!")

    discount = float(c.get("personal_discount_percent", 0))
    if discount > 0:
        lines.append(f"\n🎁 Shaxsiy chegirma: <b>{discount:.1f}%</b>")

    if c.get("last_purchase_date"):
        lines.append(f"\n📅 Oxirgi xarid: <b>{c['last_purchase_date'][:10]}</b>")

    await message.answer("\n".join(lines), parse_mode="HTML")


# ===== /HELP =====

@router.message(Command("help"))
async def cmd_help(message: Message):
    telegram_id = str(message.from_user.id)
    webapp_url = config.WEBAPP_URL or ""
    webapp_line = "🌐 <b>Shaxsiy Kabinetim</b> — to'liq ma'lumot\n" if webapp_url.startswith("https://") else ""

    # Kompaniya telefoni API dan
    profile_result = await api_get("/bot/my-profile", telegram_id)
    profile_data = profile_result.get("data", {}) if profile_result.get("success") else {}
    company_phone = profile_data.get("company_phone") or config.COMPANY_PHONE

    phone_line = f"\n📞 Aloqa: <b>{company_phone}</b>" if company_phone else ""

    await message.answer(
        "ℹ️ <b>Yordam</b>\n\n"
        "📋 <b>Sotuvlarim</b> — xaridlar ro'yxati\n"
        "💰 <b>Qarzim</b> — qarz holati\n"
        "👤 <b>Profilim</b> — shaxsiy ma'lumotlar\n"
        "📊 <b>Statistika</b> — umumiy statistika\n"
        + webapp_line +
        "\n/start — qayta boshlash"
        + phone_line,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(webapp_url)
    )
