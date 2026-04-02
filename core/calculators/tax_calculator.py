from typing import Dict
from config import Config

class TaxCalculator:
    """Калькулятор налогов УСН"""
    
    def __init__(self, usn_type: str = 'income', has_employees: bool = False):
        self.usn_type = usn_type
        self.has_employees = has_employees
        self.rate = Config.USN_RATE_INCOME if usn_type == 'income' else Config.USN_RATE_INCOME_EXPENSE
    
    def calculate(self, quarters: Dict, insurance: float) -> Dict:
        """Рассчитывает налог УСН"""
        result = {
            'income_q1': quarters.get('q1', {}).get('income', 0),
            'income_q2': quarters.get('q2', {}).get('income', 0),
            'income_q3': quarters.get('q3', {}).get('income', 0),
            'income_q4': quarters.get('q4', {}).get('income', 0),
            'expense_q1': quarters.get('q1', {}).get('expense', 0),
            'expense_q2': quarters.get('q2', {}).get('expense', 0),
            'expense_q3': quarters.get('q3', {}).get('expense', 0),
            'expense_q4': quarters.get('q4', {}).get('expense', 0),
            'insurance': insurance,
            'tax_q1': 0,
            'tax_q2': 0,
            'tax_q3': 0,
            'tax_year': 0,
            'to_pay_q1': 0,
            'to_pay_q2': 0,
            'to_pay_q3': 0,
            'to_pay_year': 0
        }
        
        if self.usn_type == 'income':
            self._calculate_income(result)
        else:
            self._calculate_income_expense(result)
        
        return result
    
    def _calculate_income(self, result: Dict):
        """УСН 6% Доходы"""
        # Нарастающим итогом
        income_cumulative = {
            'q1': result['income_q1'],
            'q2': result['income_q1'] + result['income_q2'],
            'q3': result['income_q1'] + result['income_q2'] + result['income_q3'],
            'year': sum([result[f'income_{q}'] for q in ['q1', 'q2', 'q3', 'q4']])
        }
        
        # Исчисленный налог
        result['tax_q1'] = income_cumulative['q1'] * self.rate / 100
        result['tax_q2'] = income_cumulative['q2'] * self.rate / 100
        result['tax_q3'] = income_cumulative['q3'] * self.rate / 100
        result['tax_year'] = income_cumulative['year'] * self.rate / 100
        
        # Уменьшение на взносы
        if self.has_employees:
            reduction_limit = 0.5  # 50%
        else:
            reduction_limit = 1.0  # 100% для ИП без сотрудников
        
        # К уплате (с учётом предыдущих платежей)
        result['to_pay_q1'] = max(0, result['tax_q1'] - result['insurance'] * 0.25 * reduction_limit)
        result['to_pay_q2'] = max(0, result['tax_q2'] - result['insurance'] * 0.5 * reduction_limit - result['to_pay_q1'])
        result['to_pay_q3'] = max(0, result['tax_q3'] - result['insurance'] * 0.75 * reduction_limit - result['to_pay_q1'] - result['to_pay_q2'])
        result['to_pay_year'] = max(0, result['tax_year'] - result['insurance'] * reduction_limit - result['to_pay_q1'] - result['to_pay_q2'] - result['to_pay_q3'])
    
    def _calculate_income_expense(self, result: Dict):
        """УСН 15% Доходы-Расходы"""
        # Налоговая база
        base_q1 = max(0, result['income_q1'] - result['expense_q1'])
        base_q2 = max(0, (result['income_q1'] + result['income_q2']) - (result['expense_q1'] + result['expense_q2']))
        base_q3 = max(0, (result['income_q1'] + result['income_q2'] + result['income_q3']) - (result['expense_q1'] + result['expense_q2'] + result['expense_q3']))
        base_year = max(0, sum([result[f'income_{q}'] for q in ['q1', 'q2', 'q3', 'q4']]) - sum([result[f'expense_{q}'] for q in ['q1', 'q2', 'q3', 'q4']]))
        
        # Исчисленный налог
        result['tax_q1'] = base_q1 * self.rate / 100
        result['tax_q2'] = base_q2 * self.rate / 100
        result['tax_q3'] = base_q3 * self.rate / 100
        result['tax_year'] = base_year * self.rate / 100
        
        # Минимальный налог (1% от доходов)
        total_income = sum([result[f'income_{q}'] for q in ['q1', 'q2', 'q3', 'q4']])
        minimal_tax = total_income * Config.MINIMAL_TAX_RATE / 100
        
        if result['tax_year'] < minimal_tax:
            result['tax_year'] = minimal_tax
        
        # К уплате
        result['to_pay_q1'] = result['tax_q1']
        result['to_pay_q2'] = max(0, result['tax_q2'] - result['to_pay_q1'])
        result['to_pay_q3'] = max(0, result['tax_q3'] - result['to_pay_q1'] - result['to_pay_q2'])
        result['to_pay_year'] = max(0, result['tax_year'] - result['to_pay_q1'] - result['to_pay_q2'] - result['to_pay_q3'])