from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from database import db
from core.parsers.excel_parser import UniversalExcelParser
from core.parsers.ens_parser import ENSParser
from core.calculators.tax_calculator import TaxCalculator
from core.generators.declaration_generator import DeclarationGenerator
from core.generators.kudir_generator import KUDIRGenerator
from config import DOWNLOADS_DIR
from loguru import logger
import os
from datetime import datetime

router = Router()

@router.message(F.text == "/calculate")
async def cmd_calculate(message: types.Message, state: FSMContext):
    data = await state.get_data()
    files = data.get('files', [])
    
    if not files:
        await message.answer("❌ Сначала загрузите файлы выписок")
        return
    
    await message.answer("⏳ Обрабатываю файлы...")
    
    try:
        # Парсим банковские выписки
        excel_parser = UniversalExcelParser()
        total_income = 0
        total_expense = 0
        all_transactions = []
        
        for file_info in files:
            if file_info['type'] == 'bank':
                income, expense, transactions = excel_parser.parse_file(
                    file_info['path'], file_info['name']
                )
                total_income += income
                total_expense += expense
                all_transactions.extend(transactions)
        
        # Группируем по кварталам
        quarters = excel_parser.group_by_quarter(all_transactions)
        
        # Парсим ЕНС
        ens_parser = ENSParser()
        insurance = 0
        for file_info in files:
            if file_info['type'] == 'ens':
                ens_data = ens_parser.parse(file_info['path'])
                insurance = ens_data['insurance_contributions']
        
        # Рассчитываем налог
        user = await db.get_user(message.from_user.id)
        calculator = TaxCalculator(
            usn_type=user.get('usn_type', 'income') if user else 'income',
            has_employees=user.get('has_employees', False) if user else False
        )
        tax_data = calculator.calculate(quarters, insurance)
        
        # Генерируем файлы
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        declaration_path = DOWNLOADS_DIR / f"Declaration_{timestamp}.xlsx"
        kudir_path = DOWNLOADS_DIR / f"KUDIR_{timestamp}.xlsx"
        
        inn = user.get('inn', '632312967829') if user else '632312967829'
        name = user.get('username', 'ИП Леонтьев Артём Владиславович') if user else 'ИП Леонтьев Артём Владиславович'
        
        decl_gen = DeclarationGenerator()
        decl_gen.generate(tax_data, str(declaration_path), inn, name)
        
        kudir_gen = KUDIRGenerator()
        kudir_gen.generate(tax_data, str(kudir_path), inn, name)
        
        # Сохраняем расчёт
        await db.save_calculation(message.from_user.id, tax_data)
        
        # Отправляем результат
        await message.answer(
            "✅ <b>Расчёт завершён!</b>\n\n"
            f"💰 Доходы за год: {sum(quarters[q]['income'] for q in ['q1','q2','q3','q4']):,.2f} ₽\n"
            f"💸 Расходы за год: {sum(quarters[q]['expense'] for q in ['q1','q2','q3','q4']):,.2f} ₽\n"
            f"📋 Страховые взносы: {insurance:,.2f} ₽\n"
            f"🧾 Налог исчисленный: {tax_data['tax_year']:,.2f} ₽\n"
            f"💵 Налог к доплате: {tax_data['to_pay_year']:,.2f} ₽\n\n"
            "📁 Готовые файлы отправлены ниже 👇"
        )
        
        # Отправляем файлы
        with open(declaration_path, 'rb') as doc:
            await message.answer_document(doc, caption="📄 Декларация УСН")
        
        with open(kudir_path, 'rb') as doc:
            await message.answer_document(doc, caption="📖 КУДИР")
        
        # Очищаем файлы
        for file_info in files:
            if os.path.exists(file_info['path']):
                os.remove(file_info['path'])
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка расчёта: {e}")
        await message.answer(f"❌ Ошибка при расчёте: {str(e)}")