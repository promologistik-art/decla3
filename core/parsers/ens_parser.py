import pandas as pd
from typing import Dict
from loguru import logger

class ENSParser:
    """Парсер выписки ЕНС (Единый Налоговый Счёт)"""
    
    def __init__(self):
        self.insurance_kbk = '18210202000010000160'
        self.tax_kbk = '18201061201010000510'
    
    def parse(self, file_path: str) -> Dict:
        """Парсит CSV файл ЕНС"""
        try:
            df = pd.read_csv(file_path, sep=';', decimal=',')
            return self._process_dataframe(df)
        except Exception as e:
            logger.error(f"Ошибка парсинга ЕНС: {e}")
            raise
    
    def _process_dataframe(self, df: pd.DataFrame) -> Dict:
        result = {
            'insurance_contributions': 0.0,
            'tax_payments': 0.0,
            'penalties': 0.0,
            'operations': []
        }
        
        for idx, row in df.iterrows():
            try:
                amount = self._parse_amount(row.get('Сумма операции', 0))
                operation_type = str(row.get('Наименование операции', ''))
                kbk = str(row.get('КБК', ''))
                
                operation = {
                    'date': row.get('Дата записи', ''),
                    'type': operation_type,
                    'amount': amount,
                    'kbk': kbk,
                    'description': row.get('Наименование обязательства', '')
                }
                result['operations'].append(operation)
                
                # Страховые взносы
                if 'Страховые взносы' in operation_type or self.insurance_kbk in kbk:
                    if amount < 0:  # Начислено
                        result['insurance_contributions'] += abs(amount)
                
                # Налоговые платежи
                elif 'Единый налоговый платеж' in operation_type or self.tax_kbk in kbk:
                    if amount > 0:  # Уплата
                        result['tax_payments'] += amount
                
                # Пени
                elif 'Пени' in operation_type:
                    if amount < 0:
                        result['penalties'] += abs(amount)
                        
            except Exception as e:
                logger.warning(f"Пропущена строка ЕНС {idx}: {e}")
                continue
        
        return result
    
    def _parse_amount(self, value) -> float:
        try:
            if isinstance(value, str):
                value = value.replace(',', '.').replace('+', '').replace(' ', '')
            return float(value)
        except:
            return 0.0