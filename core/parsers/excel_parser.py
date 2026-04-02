import pandas as pd
from typing import List, Dict, Tuple
from datetime import datetime
from loguru import logger
import re

class UniversalExcelParser:
    """Универсальный парсер банковских выписок Excel"""
    
    def __init__(self):
        self.income_keywords = [
            'поступление', 'выручка', 'доход', 'оплата по договору',
            'перевод от покупателя', 'бонус', 'возврат', 'за товар',
            'за услуги', 'контракт', 'реестр'
        ]
        self.expense_keywords = [
            'оплата за', 'услуги', 'товар', 'комиссия', 'аренда',
            'налог', 'взнос', 'штраф', 'по договору'
        ]
        self.own_transfer_keywords = [
            'перевод собственных', 'вывод собственных', 'на личные нужды',
            'собственных средств', 'вывод', 'на карту', 'на счёт'
        ]
    
    def detect_bank_format(self, df: pd.DataFrame, file_name: str) -> str:
        """Определяет формат банка по структуре файла"""
        file_name_lower = file_name.lower()
        
        if 'озон' in file_name_lower or 'ozon' in file_name_lower:
            return 'ozon'
        elif 'вб' in file_name_lower or 'wb' in file_name_lower or 'wildberries' in file_name_lower:
            return 'wb'
        
        # Авто-детекция по колонкам
        columns = [str(c).lower() for c in df.columns]
        
        if 'кредит' in columns and 'дебет' in columns:
            return 'ozon'
        elif 'по кредиту' in columns or 'по дебету' in columns:
            return 'wb'
        
        return 'unknown'
    
    def parse_file(self, file_path: str, file_name: str) -> Tuple[float, float, List[Dict]]:
        """Парсит файл выписки любого формата"""
        try:
            # Читаем Excel, пропускаем шапку
            df = pd.read_excel(file_path, skiprows=10)
            
            # Определяем формат
            bank_format = self.detect_bank_format(df, file_name)
            logger.info(f"Определён формат банка: {bank_format}")
            
            income = 0.0
            expense = 0.0
            transactions = []
            
            for idx, row in df.iterrows():
                try:
                    transaction = self._parse_row(row, bank_format)
                    if transaction:
                        if transaction['type'] == 'income':
                            income += transaction['amount']
                        else:
                            expense += transaction['amount']
                        transactions.append(transaction)
                except Exception as e:
                    logger.warning(f"Пропущена строка {idx}: {e}")
                    continue
            
            return income, expense, transactions
            
        except Exception as e:
            logger.error(f"Ошибка парсинга файла {file_name}: {e}")
            raise
    
    def _parse_row(self, row: pd.Series, bank_format: str) -> Optional[Dict]:
        """Парсит одну строку выписки"""
        try:
            # Извлекаем дату
            date = self._get_date(row)
            if not date:
                return None
            
            # Извлекаем суммы
            credit = self._get_credit(row, bank_format)
            debit = self._get_debit(row, bank_format)
            
            # Извлекаем описание
            description = self._get_description(row)
            
            # Извлекаем контрагента
            counterparty = self._get_counterparty(row)
            
            # Пропускаем переводы себе
            if self._is_own_transfer(description):
                return None
            
            transaction = {
                'date': date,
                'counterparty': counterparty,
                'description': description
            }
            
            if credit > 0:
                transaction['type'] = 'income'
                transaction['amount'] = credit
                return transaction
            elif debit > 0:
                transaction['type'] = 'expense'
                transaction['amount'] = debit
                return transaction
            
            return None
            
        except Exception as e:
            logger.warning(f"Ошибка парсинга строки: {e}")
            return None
    
    def _get_date(self, row: pd.Series) -> Optional[datetime]:
        """Извлекает дату из строки"""
        date_columns = ['дата', 'дата совершения', 'date']
        for col in row.index:
            if any(keyword in str(col).lower() for keyword in date_columns):
                try:
                    val = row[col]
                    if pd.notna(val):
                        if isinstance(val, datetime):
                            return val
                        return pd.to_datetime(val)
                except:
                    pass
        return None
    
    def _get_credit(self, row: pd.Series, bank_format: str) -> float:
        """Извлекает сумму поступления"""
        credit_columns = ['кредит', 'по кредиту', 'credit', 'поступления']
        for col in row.index:
            if any(keyword in str(col).lower() for keyword in credit_columns):
                try:
                    val = row[col]
                    if pd.notna(val):
                        return float(val)
                except:
                    pass
        return 0.0
    
    def _get_debit(self, row: pd.Series, bank_format: str) -> float:
        """Извлекает сумму расхода"""
        debit_columns = ['дебет', 'по дебету', 'debit', 'расходы']
        for col in row.index:
            if any(keyword in str(col).lower() for keyword in debit_columns):
                try:
                    val = row[col]
                    if pd.notna(val):
                        return float(val)
                except:
                    pass
        return 0.0
    
    def _get_description(self, row: pd.Series) -> str:
        """Извлекает назначение платежа"""
        desc_columns = ['назначение', 'описание', 'description', 'платежа']
        for col in row.index:
            if any(keyword in str(col).lower() for keyword in desc_columns):
                try:
                    val = row[col]
                    if pd.notna(val):
                        return str(val)
                except:
                    pass
        return ""
    
    def _get_counterparty(self, row: pd.Series) -> str:
        """Извлекает контрагента"""
        counterparty_columns = ['контрагент', 'плательщик', 'получатель', 'inn']
        for col in row.index:
            if any(keyword in str(col).lower() for keyword in counterparty_columns):
                try:
                    val = row[col]
                    if pd.notna(val):
                        return str(val)
                except:
                    pass
        return ""
    
    def _is_own_transfer(self, description: str) -> bool:
        """Проверяет, является ли перевод собственным"""
        desc_lower = description.lower()
        return any(keyword in desc_lower for keyword in self.own_transfer_keywords)
    
    def group_by_quarter(self, transactions: List[Dict]) -> Dict[str, Dict]:
        """Группирует транзакции по кварталам"""
        quarters = {
            'q1': {'income': 0, 'expense': 0},
            'q2': {'income': 0, 'expense': 0},
            'q3': {'income': 0, 'expense': 0},
            'q4': {'income': 0, 'expense': 0}
        }
        
        for tx in transactions:
            month = tx['date'].month
            if month in [1, 2, 3]:
                q = 'q1'
            elif month in [4, 5, 6]:
                q = 'q2'
            elif month in [7, 8, 9]:
                q = 'q3'
            else:
                q = 'q4'
            
            if tx['type'] == 'income':
                quarters[q]['income'] += tx['amount']
            else:
                quarters[q]['expense'] += tx['amount']
        
        return quarters