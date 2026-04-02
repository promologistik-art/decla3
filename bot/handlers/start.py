from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from database import db
from loguru import logger

router = Router()

@router.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "Не указан"
    
    # Сохраняем пользователя
    await db.save_user(user_id, username)
    
    await message.answer(
        "👋 Привет! Я бот для автоматизации налоговой отчётности ИП на УСН.\n\n"
        "📋 <b>Что я умею:</b>\n"
        "• Принимаю выписки из любых банков (Excel)\n"
        "• Принимаю выписку ЕНС (CSV)\n"
        "• Заполняю КУДИР автоматически\n"
        "• Заполняю Декларацию УСН\n"
        "• Рассчитываю налог к уплате\n\n"
        "📤 <b>Для начала работы:</b>\n"
        "1. Отправьте файлы выписок из банков\n"
        "2. Отправьте выписку ЕНС\n"
        "3. Нажмите /calculate для расчёта\n\n"
        "ℹ️ Поддерживаются любые форматы Excel выписок!"
    )

@router.message(F.text == "/profile")
async def cmd_profile(message: types.Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if user:
        await message.answer(
            "👤 <b>Ваш профиль:</b>\n\n"
            f"ИНН: <code>{user.get('inn', 'Не указан')}</code>\n"
            f"Система: {user.get('usn_type', 'Доходы (6%)')}\n"
            f"Сотрудники: {'Есть' if user.get('has_employees') else 'Нет'}"
        )
    else:
        await message.answer("Профиль не найден. Нажмите /start")