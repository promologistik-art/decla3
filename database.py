import aiosqlite
from datetime import datetime
from typing import Optional, Dict, Any
from config import DB_PATH

class Database:
    def __init__(self):
        self.db_path = DB_PATH
    
    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    inn TEXT,
                    usn_type TEXT DEFAULT 'income',
                    has_employees BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    bank_files TEXT,
                    ens_file TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS calculations (
                    calc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    income_q1 REAL,
                    income_q2 REAL,
                    income_q3 REAL,
                    income_q4 REAL,
                    expense_q1 REAL,
                    expense_q2 REAL,
                    expense_q3 REAL,
                    expense_q4 REAL,
                    insurance REAL,
                    tax_q1 REAL,
                    tax_q2 REAL,
                    tax_q3 REAL,
                    tax_year REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            await db.commit()
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def save_user(self, user_id: int, username: str, inn: str = None, 
                       usn_type: str = 'income', has_employees: bool = False):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO users 
                (user_id, username, inn, usn_type, has_employees)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, inn, usn_type, has_employees))
            await db.commit()
    
    async def save_calculation(self, user_id: int, data: Dict):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO calculations 
                (user_id, income_q1, income_q2, income_q3, income_q4,
                 expense_q1, expense_q2, expense_q3, expense_q4,
                 insurance, tax_q1, tax_q2, tax_q3, tax_year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                data.get('income_q1', 0), data.get('income_q2', 0),
                data.get('income_q3', 0), data.get('income_q4', 0),
                data.get('expense_q1', 0), data.get('expense_q2', 0),
                data.get('expense_q3', 0), data.get('expense_q4', 0),
                data.get('insurance', 0),
                data.get('tax_q1', 0), data.get('tax_q2', 0),
                data.get('tax_q3', 0), data.get('tax_year', 0)
            ))
            await db.commit()

db = Database()