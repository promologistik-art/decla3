from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from config import DOWNLOADS_DIR, MAX_FILE_SIZE
from loguru import logger
import os

router = Router()

@router.message(F.document)
async def handle_file(message: types.Message, state: FSMContext):
    file = message.document
    
    # Проверка размера
    if file.file_size > MAX_FILE_SIZE:
        await message.answer("❌ Файл слишком большой (макс. 50 MB)")
        return
    
    # Проверка формата
    file_name = file.file_name.lower()
    if not (file_name.endswith('.xlsx') or file_name.endswith('.csv')):
        await message.answer("❌ Поддерживаются только .xlsx и .csv файлы")
        return
    
    await message.answer("⏳ Загружаю файл...")
    
    # Скачиваем файл
    file_obj = await message.bot.get_file(file.file_id)
    file_path = DOWNLOADS_DIR / f"{message.from_user.id}_{file.file_unique_id}_{file.file_name}"
    await message.bot.download_file(file_obj.file_path, file_path)
    
    # Определяем тип файла
    if 'енс' in file_name or 'ens' in file_name or file_name.endswith('.csv'):
        file_type = 'ens'
    else:
        file_type = 'bank'
    
    # Сохраняем в сессию
    data = await state.get_data()
    files = data.get('files', [])
    files.append({'path': str(file_path), 'type': file_type, 'name': file.file_name})
    await state.update_data(files=files)
    
    await message.answer(
        f"✅ Файл получен: <b>{file.file_name}</b>\n"
        f"📁 Тип: {'Выписка ЕНС' if file_type == 'ens' else 'Банковская выписка'}\n\n"
        "📤 Отправьте остальные файлы или нажмите /calculate"
    )

@router.message(F.text == "/clear")
async def cmd_clear(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🗑️ Все загруженные файлы очищены")