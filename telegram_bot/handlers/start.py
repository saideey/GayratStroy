"""
Start handler - /start komandasi va telefon raqam registratsiya.

Oqim:
  1. Foydalanuvchi /start bosadi
  2. Bot telefon raqam so'raydi (Contact button orqali)
  3. Foydalanuvchi telefon yuboradi
  4. API ga link-phone so'rovi yuboriladi
  5. Topilsa → Asosiy menyu, topilmasa → Xabar
"""

import logging
import httpx
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import config

logger = logging.getLogger(__name__)
router = Router()


class RegistrationStates(StatesGroup):
    waiting_for_phone = State()


def phone_request_keyboard() -> ReplyKeyboardMarkup:
    """Telefon raqam so'rash uchun keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamimni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def main_menu_keyboard(webapp_url: str = None) -> ReplyKeyboardMarkup:
    """Asosiy menyu keyboard."""
    buttons = [
        [KeyboardButton(text="📋 Sotuvlarim"), KeyboardButton(text="💰 Qarzim")],
        [KeyboardButton(text="👤 Profilim"), KeyboardButton(text="📊 Statistika")],
    ]
    # WebApp tugmasi faqat to'g'ri HTTPS URL bo'lganda qo'shiladi
    if webapp_url and webapp_url.startswith("https://"):
        from aiogram.types import WebAppInfo
        buttons.append([
            KeyboardButton(
                text="🌐 Shaxsiy Kabinetim",
                web_app=WebAppInfo(url=webapp_url)
            )
        ])
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )


async def link_phone_to_customer(telegram_id: str, phone: str,
                                  first_name: str = None,
                                  last_name: str = None,
                                  username: str = None) -> dict:
    """API orqali telefon raqamni bog'lash."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{config.API_URL}/bot/link-phone",
                json={
                    "telegram_id": telegram_id,
                    "phone": phone,
                    "first_name": first_name,
                    "last_name": last_name,
                    "username": username,
                }
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.error(f"link-phone API error: {e}")
    return {"success": False, "found": False, "message": "Server bilan bog'lanishda xatolik"}


async def get_customer_profile(telegram_id: str) -> dict:
    """Mijoz profilini API dan olish."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{config.API_URL}/bot/my-profile",
                headers={"X-Telegram-Id": str(telegram_id)}
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.error(f"my-profile API error: {e}")
    return None


async def get_company_info_from_api() -> dict:
    """Kompaniya nomi va telefon raqamini API dan olish (autentifikatsiyasiz)."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{config.API_URL}/bot/company-info")
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", {})
    except Exception as e:
        logger.error(f"company-info API error: {e}")
    return {}


# ===== HANDLERS =====

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    /start komandasi.
    Agar allaqachon ro'yxatdan o'tgan bo'lsa — menyuni ko'rsat.
    Aks holda telefon so'ra.
    """
    await state.clear()
    telegram_id = str(message.from_user.id)

    # Avval allaqachon bog'langanmi tekshir
    profile = await get_customer_profile(telegram_id)

    if profile and profile.get("success"):
        customer = profile["data"]
        webapp_url = config.WEBAPP_URL or ""
        company_name = customer.get("company_name") or config.COMPANY_NAME
        company_phone = customer.get("company_phone") or config.COMPANY_PHONE

        await message.answer(
            f"👋 Xush kelibsiz, <b>{customer['name']}</b>!\n\n"
            f"🏪 <b>{company_name}</b> shaxsiy kabinetingizga kiring.\n\n"
            f"💰 Joriy qarz: <b>{customer['current_debt']:,.0f} so'm</b>\n"
            f"🛒 Jami xaridlar: <b>{customer['total_purchases_count']} marta</b>",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(webapp_url)
        )
    else:
        # Ro'yxatdan o'tmagan — telefon so'ra
        # Kompaniya nomini DB dan olamiz
        company = await get_company_info_from_api()
        company_name = company.get("name") or config.COMPANY_NAME

        await state.set_state(RegistrationStates.waiting_for_phone)
        await message.answer(
            f"🏪 <b>{company_name}</b> botiga xush kelibsiz!\n\n"
            "Bu bot orqali siz:\n"
            "✅ O'z xaridlaringizni ko'rishingiz\n"
            "✅ Qarz holatini bilishingiz\n"
            "✅ To'lovlar tarixini kuzatishingiz mumkin\n\n"
            "📱 Davom etish uchun <b>telefon raqamingizni</b> yuboring:",
            parse_mode="HTML",
            reply_markup=phone_request_keyboard()
        )


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def handle_contact(message: Message, state: FSMContext):
    """
    Foydalanuvchi Contact button orqali telefon yubordi.
    """
    contact = message.contact
    telegram_id = str(message.from_user.id)

    # Faqat o'z raqamini yuborganligini tekshirish
    if contact.user_id and str(contact.user_id) != telegram_id:
        await message.answer(
            "⚠️ Iltimos, <b>o'z</b> telefon raqamingizni yuboring.",
            parse_mode="HTML",
            reply_markup=phone_request_keyboard()
        )
        return

    phone = contact.phone_number
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username

    # Kutayotganligini bildirish
    wait_msg = await message.answer(
        "🔍 Ma'lumotlar tekshirilmoqda...",
        reply_markup=ReplyKeyboardRemove()
    )

    # API orqali bog'lash
    result = await link_phone_to_customer(
        telegram_id=telegram_id,
        phone=phone,
        first_name=first_name,
        last_name=last_name,
        username=username
    )

    # Kutish xabarini o'chirish
    try:
        await wait_msg.delete()
    except Exception:
        pass

    await state.clear()

    if result.get("success") and result.get("found"):
        customer_name = result.get("customer_name", "Mijoz")
        webapp_url = config.WEBAPP_URL or ""

        await message.answer(
            f"✅ <b>Muvaffaqiyatli!</b>\n\n"
            f"Salom, <b>{customer_name}</b>! 👋\n\n"
            f"Endi siz shaxsiy kabinetingizdan foydalanishingiz mumkin.\n"
            f"Quyidagi tugmalardan birini tanlang:",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(webapp_url)
        )
    else:
        # API dan kelgan xabarda allaqachon DB dagi kompaniya telefoni bor
        msg = result.get("message", "Xatolik yuz berdi")
        await message.answer(
            f"❌ <b>Topilmadi</b>\n\n"
            f"{msg}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Qayta urinish", callback_data="retry_register")]
            ])
        )


@router.message(RegistrationStates.waiting_for_phone)
async def handle_wrong_input(message: Message, state: FSMContext):
    """Foydalanuvchi matn yozdi — tugmani bosishni so'rash."""
    await message.answer(
        "📱 Iltimos, <b>«Telefon raqamimni yuborish»</b> tugmasini bosing:",
        parse_mode="HTML",
        reply_markup=phone_request_keyboard()
    )


from aiogram.types import CallbackQuery

@router.callback_query(F.data == "retry_register")
async def retry_register(callback: CallbackQuery, state: FSMContext):
    """Qayta urinish."""
    await callback.message.edit_reply_markup(reply_markup=None)
    await state.set_state(RegistrationStates.waiting_for_phone)
    await callback.message.answer(
        "📱 Telefon raqamingizni yuboring:",
        reply_markup=phone_request_keyboard()
    )
    await callback.answer()
