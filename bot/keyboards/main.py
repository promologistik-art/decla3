from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/calculate"), KeyboardButton(text="/profile")],
            [KeyboardButton(text="/clear"), KeyboardButton(text="/history")]
        ],
        resize_keyboard=True
    )
    return keyboard