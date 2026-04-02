from aiogram import types, Router, F
from database import db
from loguru import logger

router = Router()

@router.message(F.text == "/history")
async def cmd_history(message: types.Message):
    await message.answer("📊 История расчётов будет доступна в следующей версии")