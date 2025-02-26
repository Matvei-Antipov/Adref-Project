from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from constants import CHANNEL_LINK

# subscribe

def subscribe_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("Подписаться на канал", url=CHANNEL_LINK),
        InlineKeyboardButton("Проверить подписку", callback_data="check")
    )
    return keyboard

#main

def main_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("👨 Личный кабинет", callback_data="cabinet"),
        InlineKeyboardButton("🎲 Мини-игры", callback_data="games"),
        InlineKeyboardButton("💸 Вывод средств", callback_data="payment"),
        InlineKeyboardButton("📋 Задания", callback_data="tasks"),
        InlineKeyboardButton("🔗 Реферальная система", callback_data="ref")
    )
    return keyboard

#main admin

def main_keyboard_admin():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("👨 Личный кабинет", callback_data="cabinet"),
        InlineKeyboardButton("🎲 Мини-игры", callback_data="games"),
        InlineKeyboardButton("💸 Вывод средств", callback_data="payment"),
        InlineKeyboardButton("📋 Задания", callback_data="tasks"),
        InlineKeyboardButton("🔗 Реферальная система", callback_data="ref"),
        InlineKeyboardButton("⚠️ Админ панель", callback_data="admin")
    )
    return keyboard

#games

def games_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("🎲 Кубик", callback_data="dice"),
        InlineKeyboardButton("🏀 Баскетбол", callback_data="basketball"),
        InlineKeyboardButton("⚽ Футбол", callback_data="football"),
    )
    keyboard.add(
        InlineKeyboardButton("🎡 Колесо Фортуны", callback_data="wheel_of_fortune"),
        InlineKeyboardButton("🪙 Монетка", callback_data="coin_toss"),
    )
    keyboard.add(
        InlineKeyboardButton("🎰 Рулетка", callback_data="roulette"),
        InlineKeyboardButton("🔢 Угадай число", callback_data="guess_number"),
    )
    keyboard.add(
        InlineKeyboardButton("🎟️ Счастливый билет", callback_data="lucky_ticket"),
    )
    keyboard.add(
        InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")
    )
    return keyboard

#back button

back_button = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton("Назад", callback_data="back"))

#back button form

back_button_form = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton("Назад", callback_data="back_form"))

#back button form admin

back_button_form_admin = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton("Назад", callback_data="back_form_admin"))

#play button

play_button = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("Играть", callback_data="play_button"),
    InlineKeyboardButton("Назад", callback_data="back")
)

#payment

def payment():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("⏩ Запросить вывод", callback_data="payment_form"),
        InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")
    )
    return keyboard

#back menu

def back_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")
    )
    return keyboard

#back menu admin

def back_menu_admin():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("⬅️ Назад", callback_data="main_menu_admin")
    )
    return keyboard

#admin panel

def admin_panel():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("👁️ Работа с заданиями", callback_data="tasks_admin"),
        InlineKeyboardButton("⬅️ Назад", callback_data="main_menu_admin")
    )
    return keyboard

#admin panel tasks

def admin_panel_tasks():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("📋 Посмотреть список", callback_data="list_admin"),
        InlineKeyboardButton("➕ Добавить задание", callback_data="add_task"),
        InlineKeyboardButton("🗑️ Удалить задание", callback_data="delete_task"),
        InlineKeyboardButton("⬅️ Назад", callback_data="main_menu_admin")
    )
    return keyboard

#payment admin
def payment_admin(ticket_id: str, user_id: str, balance: str):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("✅ Тикет исполнен", callback_data=f"answered_{ticket_id}_{user_id}_{balance}"),
    )
    return keyboard

#task 
def task_keyboard(task_id: str):
    keyboard = InlineKeyboardMarkup(row_width=2)
    check_subscription_button = InlineKeyboardButton("🔍 Проверить подписку", callback_data=f"check_subscription_{task_id}")
    back_button = InlineKeyboardButton("⬅️ Назад", callback_data="back_to_list_admin")
    
    keyboard.add(check_subscription_button, back_button)
    return keyboard

#task delete
def task_keyboard_delete(task_id: str):
    keyboard = InlineKeyboardMarkup(row_width=2)
    check_subscription_button = InlineKeyboardButton("🗑️ Удалить задание", callback_data=f"0x0_{task_id}")
    back_button = InlineKeyboardButton("⬅️ Назад", callback_data="back_to_list_admin")
    
    keyboard.add(check_subscription_button, back_button)
    return keyboard