import random
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.storage import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils import executor
from middleware import SubscriptionMiddleware
from constants import TOKEN, CHANNEL_ID, ADMIN_ID
from keyboards import (subscribe_keyboard,
                       main_keyboard,
                       games_keyboard,
                       back_button,
                       play_button,
                       back_button_form,
                       back_button_form_admin,
                       payment,
                       back_menu,
                       payment_admin,
                       main_keyboard_admin,
                       admin_panel,
                       admin_panel_tasks,
                       back_menu_admin,
                       task_keyboard,
                       task_keyboard_delete
)
from database import (
    insert_user,
    find_user,
    get_info,
    update_balance,
    insert_game,
    get_games,
    update_game,
    delete_games,
    generate_ticket_id,
    get_tickets,
    delete_ticket,
    set_balance,
    count_tasks,
    add_task,
    set_link,
    get_tasks,
    get_task,
    insert_completed,
    get_completed_tasks,
    get_task_private,
    update_completed,
    delete_task,
    add_referral
)

class ClientStates(StatesGroup):
    bet = State()
    predict = State()
    game = State()
    name = State()
    link = State()

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=MemoryStorage())

error_messages = {}
administrators = {
    "developer": ADMIN_ID
}

dp.middleware.setup(SubscriptionMiddleware(CHANNEL_ID, subscribe_keyboard))

async def check_subscription_start(user_id):
    try:
        user_status = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        print(f"Статус пользователя {user_id} в канале: {user_status.status}")
        return user_status.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Ошибка при проверке подписки: {e}")
        return False

@dp.callback_query_handler(lambda c: c.data == "check")
async def check_subscription_callback(callback_query: CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        user_status = await bot.get_chat_member(CHANNEL_ID, user_id)
        print(f"Проверка подписки: {user_status}")

        if user_status.status in ["member", "administrator", "creator"]:
            await bot.answer_callback_query(
                callback_query.id,
                text="Вы успешно подписаны на канал! Теперь вы можете использовать бота.",
                show_alert=True
            )
        else:
            await bot.answer_callback_query(
                callback_query.id,
                text="Вы не подписаны на канал. Пожалуйста, подпишитесь, чтобы продолжить.",
                show_alert=True
            )
    except Exception as e:
        print(f"Ошибка в check_subscription_callback: {e}")
        await bot.answer_callback_query(
            callback_query.id,
            text="Произошла ошибка при проверке подписки.",
            show_alert=True
        )

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    print(f"Тип message: {type(message)}")
    try:
        user_id = message.from_user.id
        admin_id = administrators.get("developer", 0)

        args = message.get_args()
        referrer_id = int(args) if args.isdigit() else None

        if referrer_id and referrer_id != user_id:
            print("REF: ", referrer_id)
            add_referral(referrer_id)
            await bot.send_message(
                chat_id=referrer_id,
                text=f"Поздравляем! Вы пригласили нового пользователя: {user_id}."
            )

        is_subscribed = await check_subscription_start(user_id)
        print(f"User subscription status: {is_subscribed}")

        if not is_subscribed:
            await bot.send_message(
                chat_id=user_id,
                text="Пожалуйста, подпишитесь на наш канал, чтобы использовать бота.",
                reply_markup=subscribe_keyboard()
            )
            return

        if user_id == int(admin_id):
            print("Администратор зашел.")
            await bot.send_message(
                chat_id=user_id,
                text="Добро пожаловать, администратор!",
                reply_markup=main_keyboard_admin()
            )
            return

        print("Обычный пользователь зашел.")
        await bot.send_message(
            chat_id=user_id,
            text="Добро пожаловать!",
            reply_markup=main_keyboard()
        )

    except Exception as e:
        print(f"Ошибка в start_handler: {e}")
        await bot.send_message(
            chat_id=message.from_user.id,
            text="Произошла ошибка. Попробуйте позже."
        )

#cabinet callback
@dp.callback_query_handler(lambda c: c.data == "cabinet")
async def cabinet_callback(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    admin_id = administrators.get('developer')
    if user_id == int(admin_id):
        try:
            if find_user(user_id=user_id):
                chat_id = callback_query.message.chat.id
                user_data = get_info(user_id)

                first_name = callback_query.from_user.first_name
                balance = user_data["balance"]
                invited_referals = user_data["invited_referals"]
                completed_tasks = user_data["completed_tasks"]

                cabinet_message = (
                    f"👋 *Здравствуйте, {first_name}!*\n"
                    f"📋 *Ваш личный кабинет:*\n\n"
                    f"💰 Баланс: *{balance} $ADREF*\n"
                    f"👥 Приглашённых рефералов: *{invited_referals}*\n"
                    f"✅ Выполнено заданий: *{completed_tasks}*\n\n"
                    f"🎉 Спасибо, что вы с нами!"
                )

                try:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=callback_query.message.message_id,
                        text=cabinet_message,
                        reply_markup=main_keyboard_admin(),
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    print(f"Ошибка при редактировании сообщения: {e}")
                    await bot.answer_callback_query(
                        callback_query.id,
                        text="Произошла ошибка при отображении кабинета. Попробуйте позже.",
                        show_alert=True
                    )
            else:
                try:
                    insert_user(user_id=user_id)
                    if find_user(user_id=user_id):
                        chat_id = callback_query.message.chat.id
                        user_data = get_info(user_id)

                        first_name = callback_query.from_user.first_name
                        balance = user_data["balance"]
                        invited_referals = user_data["invited_referals"]
                        completed_tasks = user_data["completed_tasks"]

                        cabinet_message = (
                            f"👋 *Здравствуйте, {first_name}!*\n"
                            f"📋 *Ваш личный кабинет:*\n\n"
                            f"💰 Баланс: *{balance} $ADREF*\n"
                            f"👥 Приглашённых рефералов: *{invited_referals}*\n"
                            f"✅ Выполнено заданий: *{completed_tasks}*\n\n"
                            f"🎉 Спасибо, что вы с нами!"
                        )

                        try:
                            await bot.edit_message_text(
                                chat_id=chat_id,
                                message_id=callback_query.message.message_id,
                                text=cabinet_message,
                                reply_markup=main_keyboard_admin(),
                                parse_mode="Markdown"
                            )
                        except Exception as e:
                            print(f"Ошибка при редактировании сообщения: {e}")
                            await bot.answer_callback_query(
                                callback_query.id,
                                text="Произошла ошибка при отображении кабинета. Попробуйте позже.",
                                show_alert=True
                            )

                except Exception as e:
                    print(f"Ошибка проверки подписки: {e}")
                    await bot.answer_callback_query(
                        callback_query.id,
                        text="Произошла ошибка при регистрации. Попробуйте позже.",
                        show_alert=True
                    )
                chat_id = callback_query.message.chat.id
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=callback_query.message.message_id,
                    text=f'Здравствуйте, *{callback_query.from_user.first_name}*!\n\nВаш личный кабинет:\n\n',
                    reply_markup=main_keyboard_admin(),
                    parse_mode='Markdown',
                )

        except Exception as e:
            print(f"Ошибка проверки подписки: {e}")
            await bot.answer_callback_query(
                callback_query.id,
                text="Произошла ошибка при проверке подписки. Попробуйте позже.",
                show_alert=True
            )
    else:
        try:
            if find_user(user_id=user_id):
                chat_id = callback_query.message.chat.id
                user_data = get_info(user_id)

                first_name = callback_query.from_user.first_name
                balance = user_data["balance"]
                invited_referals = user_data["invited_referals"]
                completed_tasks = user_data["completed_tasks"]

                cabinet_message = (
                    f"👋 *Здравствуйте, {first_name}!*\n"
                    f"📋 *Ваш личный кабинет:*\n\n"
                    f"💰 Баланс: *{balance} $ADREF*\n"
                    f"👥 Приглашённых рефералов: *{invited_referals}*\n"
                    f"✅ Выполнено заданий: *{completed_tasks}*\n\n"
                    f"🎉 Спасибо, что вы с нами!"
                )

                try:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=callback_query.message.message_id,
                        text=cabinet_message,
                        reply_markup=main_keyboard(),
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    print(f"Ошибка при редактировании сообщения: {e}")
                    await bot.answer_callback_query(
                        callback_query.id,
                        text="Произошла ошибка при отображении кабинета. Попробуйте позже.",
                        show_alert=True
                    )
            else:
                try:
                    insert_user(user_id=user_id)
                    if find_user(user_id=user_id):
                        chat_id = callback_query.message.chat.id
                        user_data = get_info(user_id)

                        first_name = callback_query.from_user.first_name
                        balance = user_data["balance"]
                        invited_referals = user_data["invited_referals"]
                        completed_tasks = user_data["completed_tasks"]

                        cabinet_message = (
                            f"👋 *Здравствуйте, {first_name}!*\n"
                            f"📋 *Ваш личный кабинет:*\n\n"
                            f"💰 Баланс: *{balance} $ADREF*\n"
                            f"👥 Приглашённых рефералов: *{invited_referals}*\n"
                            f"✅ Выполнено заданий: *{completed_tasks}*\n\n"
                            f"🎉 Спасибо, что вы с нами!"
                        )

                        try:
                            await bot.edit_message_text(
                                chat_id=chat_id,
                                message_id=callback_query.message.message_id,
                                text=cabinet_message,
                                reply_markup=main_keyboard(),
                                parse_mode="Markdown"
                            )
                        except Exception as e:
                            print(f"Ошибка при редактировании сообщения: {e}")
                            await bot.answer_callback_query(
                                callback_query.id,
                                text="Произошла ошибка при отображении кабинета. Попробуйте позже.",
                                show_alert=True
                            )

                except Exception as e:
                    print(f"Ошибка проверки подписки: {e}")
                    await bot.answer_callback_query(
                        callback_query.id,
                        text="Произошла ошибка при регистрации. Попробуйте позже.",
                        show_alert=True
                    )
                chat_id = callback_query.message.chat.id
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=callback_query.message.message_id,
                    text=f'Здравствуйте, *{callback_query.from_user.first_name}*!\n\nВаш личный кабинет:\n\n',
                    reply_markup=main_keyboard(),
                    parse_mode='Markdown',
                )

        except Exception as e:
            print(f"Ошибка проверки подписки: {e}")
            await bot.answer_callback_query(
                callback_query.id,
                text="Произошла ошибка при проверке подписки. Попробуйте позже.",
                show_alert=True
            )

# games
@dp.callback_query_handler(lambda c: c.data == "games")
async def games_callback(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    try:
        user_data = get_info(user_id)
        if not user_data:
            await bot.answer_callback_query(
                callback_query.id,
                text="Вы ещё не зарегистрированы. Пожалуйста, начните с команды /start.",
                show_alert=True
            )
            return

        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="Выберите мини-игру 🎮:",
            reply_markup=games_keyboard()
        )

    except Exception as e:
        print(f"Ошибка мини-игр: {e}")
        await bot.answer_callback_query(
            callback_query.id,
            text="Произошла ошибка при запуске игр. Попробуйте позже.",
            show_alert=True
        )

@dp.callback_query_handler(lambda c: c.data in ["dice", "basketball", "football", "wheel_of_fortune", "coin_toss", "roulette", "guess_number", "lucky_ticket"])
async def game_rules_callback(callback_query: CallbackQuery, state: FSMContext):
    game = callback_query.data
    user_id = callback_query.from_user.id
    await state.set_state(ClientStates.game)
    await state.update_data(game=game)
    game_info = {
            'user_id': user_id,
            'bet': 0,
            'result_value': 'tbd',
            'result_status': False,
            'counter': 0,
            'game': game
        }
    if get_games(user_id=user_id):
        pass
    else:
        insert_game(game_info)
    
    rules = {
        "dice": "🎲 *Кубик*: Бросьте кубик и узнайте, какое число выпадет\\!\n\nКоеффициент \\- *х2*\\.",
        "basketball": "🏀 *Баскетбол*: Попробуйте забросить мяч в корзину\\!\n\nКоеффициент \\- *х1\\.75*\\.",
        "football": "⚽ *Футбол*: Забейте гол в ворота\\!\n\nКоеффициент \\- *х1\\.5*\\.",
        "wheel_of_fortune": "🎡 *Колесо Фортуны*: Испытайте свою удачу\\!\n\nКоеффициент \\- *х3*\\.",
        "coin_toss": "🪙 *Монетка*: Орел или решка?\n\nКоеффициент \\- *х1\\.5*\\.",
        "roulette": "🎰 *Рулетка*: Сделайте ставку и испытайте удачу\\!\n\nКоеффициент \\- *x3\\.2*\\.",
        "guess_number": "🔢 *Угадай число*: Попробуйте угадать загаданное число\\!\n\nКоеффициент \\- *х1\\.66*\\.",
        "lucky_ticket": "🎟️ *Счастливый билет*: Проверьте, принесет ли вам удачу ваш билет\\!\n\nКоеффициент \\- *х100*\\.",
    }
    text = rules.get(game, "Информация об этой игре пока недоступна.")

    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=f"{text}\n\nВыберите действие:",
        parse_mode="MarkdownV2",
        reply_markup=play_button
    )
    await state.reset_state()

@dp.callback_query_handler(lambda c: c.data == "play_button")
async def make_bet(callback_query: types.CallbackQuery, state:FSMContext):
    async with state.proxy() as data:
        await ClientStates.bet.set()
        user_data = get_info(callback_query.from_user.id)
        msg = await callback_query.message.edit_text(
            text=f"Введите сумму ставки в *$ADREF*\n\nМинимальная сумма \\- 5 *$ADREF*\nМаксимальная сумма \\- {user_data.get('balance')} *$ADREF*\\.",
            reply_markup=back_button_form,
            parse_mode='MarkdownV2',
        )
        data['id_to_edit'] = msg.message_id
        

@dp.message_handler(state=ClientStates.bet)
async def bet(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = message.from_user.id
        bet_amount = message.text.strip()
        user_balance = int(get_info(user_id=user_id).get('balance'))
        chat_id = message.chat.id
        if not bet_amount.isdigit():
            error_msg = "Введите число, а не строку или символ!"
            id_msg = await message.answer(error_msg, reply_markup=None)

            if user_id not in error_messages:
                    error_messages[user_id] = []
            error_messages[user_id].append(id_msg.message_id)

            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            return

        bet_amount = int(bet_amount)

        if bet_amount < 5:
            error_msg = "Минимальная ставка - 5 $ADREF!"
            id_msg = await message.answer(error_msg, reply_markup=None)

            if user_id not in error_messages:
                    error_messages[user_id] = []
            error_messages[user_id].append(id_msg.message_id)

            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            return

        if bet_amount > user_balance:
            error_msg = f"У вас недостаточно средств для этой ставки. Ваш баланс: {user_balance} $ADREF."
            id_msg = await message.answer(error_msg, reply_markup=None)

            if user_id not in error_messages:
                    error_messages[user_id] = []
            error_messages[user_id].append(id_msg.message_id)

            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            return

        if user_id in error_messages:
            try:
                for message_id in error_messages[user_id]:
                    await message.bot.delete_message(chat_id, message_id)
                del error_messages[user_id]
            except Exception as e:
                print(f"Не удалось удалить сообщение об ошибке: {e}")

        data['bet'] = bet_amount
        update_game(user_id=user_id, amount=data['bet'], status="bet")
        user_game_state = get_games(user_id=user_id).get('game')

        chat_id = message.chat.id
        text = ""
        if user_game_state == "dice":
            text = "ваше предсказание для игры в 🎲 Кубик.\n\nНапишите число, которое по вашему мнению выпадет."
        elif user_game_state == "basketball":
            text = "ваше предсказание для игры в 🏀 Баскетбол.\n\nНапишите, попадет ли мяч в кольцо *(ДА/НЕТ)*."
        elif user_game_state == "football":
            text = "ваше предсказание для игры в ⚽ Футбол.\n\nНапишите, попадет ли мяч в ворота *(ДА/НЕТ)*."
        elif user_game_state == "wheel_of_fortune":
            text = "ваше предсказание для игры в 🎡 Колесо Фортуны.\n\nНапишите номер сектора, который, по вашему мнению, выиграет."
        elif user_game_state == "coin_toss":
            text = "ваше предсказание для игры в 🪙 Монетка.\n\nНапишите, какое выпадет *ОРЕЛ* или *РЕШКА*."
        elif user_game_state == "roulette":
            text = "ваше предсказание для игры в 🎰 Рулетка.\n\nНапишите номер , который, по вашему мнению, выпадет."
        elif user_game_state == "guess_number":
            text = "ваше предсказание для игры в 🔢 Угадай число.\n\nНапишите число, которое, по вашему мнению, загадано."
        elif user_game_state == "lucky_ticket":
            text = "ваше предсказание для игры в 🎟️ Счастливый билет.\n\nНапишите номер вашего счастливого билета."

        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=data.get('id_to_edit'),
            text=f"Успешно!\n📈 Вы добавили ставку в размере - *{data['bet']} $ADREF*\n\nТеперь отправьте {text}",
            reply_markup=back_button_form,
            parse_mode='Markdown',
        )
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await state.reset_state()
        await ClientStates.predict.set()

@dp.message_handler(state=ClientStates.predict)
async def bet(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = message.from_user.id
        user_game_state = get_games(user_id).get('game')
        chat_id = message.chat.id
        prediction = message.text.strip()

        if user_game_state == "dice":
            if not prediction.isdigit() or not 1 <= int(prediction) <= 6:
                error_msg = "Ошибка! Введите число от 1 до 6 для игры в 🎲 Кубик."
                id_msg = await message.answer(error_msg, reply_markup=None)

                if user_id not in error_messages:
                        error_messages[user_id] = []
                error_messages[user_id].append(id_msg.message_id)

                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                return
        elif user_game_state == "basketball" or user_game_state == "football":
            if prediction not in ["ДА", "НЕТ"]:
                error_msg = "Ошибка! Введите ДА или НЕТ для игры в 🏀 Баскетбол или ⚽ Футбол."
                id_msg = await message.answer(error_msg, reply_markup=None)

                if user_id not in error_messages:
                        error_messages[user_id] = []
                error_messages[user_id].append(id_msg.message_id)
                
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                return
        elif user_game_state == "wheel_of_fortune":
            if not prediction.isdigit() or not 1 <= int(prediction) <= 12:
                error_msg = "Ошибка! Введите число от 1 до 12 для игры в 🎡 Колесо Фортуны."
                id_msg = await message.answer(error_msg, reply_markup=None)

                if user_id not in error_messages:
                        error_messages[user_id] = []
                error_messages[user_id].append(id_msg.message_id)

                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                return
        elif user_game_state == "coin_toss":
            if prediction not in ["ОРЕЛ", "РЕШКА"]:
                error_msg = "Ошибка! Введите ОРЕЛ или РЕШКА для игры в 🪙 Монетку."
                id_msg = await message.answer(error_msg, reply_markup=None)

                if user_id not in error_messages:
                        error_messages[user_id] = []
                error_messages[user_id].append(id_msg.message_id)

                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                return
        elif user_game_state == "roulette":
            if not prediction.isdigit() or not 0 <= int(prediction) <= 36:
                error_msg = "Ошибка! Введите число от 0 до 36 для игры в 🎰 Рулетку."
                id_msg = await message.answer(error_msg, reply_markup=None)

                if user_id not in error_messages:
                        error_messages[user_id] = []
                error_messages[user_id].append(id_msg.message_id)

                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                return
        elif user_game_state == "guess_number":
            if not prediction.isdigit() or not 1 <= int(prediction) <= 9:
                error_msg = "Ошибка! Введите число от 1 до 9 для игры в 🔢 Угадай число."
                id_msg = await message.answer(error_msg, reply_markup=None)

                if user_id not in error_messages:
                        error_messages[user_id] = []
                error_messages[user_id].append(id_msg.message_id)

                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                return
        elif user_game_state == "lucky_ticket":
            if not prediction.isdigit() or not 1 <= int(prediction) <= 999:
                error_msg = "Ошибка! Введите число от 1 до 999 для игры в 🎟️ Счастливый билет."
                id_msg = await message.answer(error_msg, reply_markup=None)

                if user_id not in error_messages:
                        error_messages[user_id] = []
                error_messages[user_id].append(id_msg.message_id)

                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                return

        if user_id in error_messages:
            try:
                for message_id in error_messages[user_id]:
                    await message.bot.delete_message(chat_id, message_id)
                del error_messages[user_id]
            except Exception as e:
                print(f"Не удалось удалить сообщение об ошибке: {e}")

        data['predict'] = message.text
        if get_games(user_id=user_id):

            update_game(user_id=user_id, amount=data['predict'], status="predict")

        else:

            print("ERROR DATABASE")

        chat_id = message.chat.id

        if user_game_state == "dice":
            result_value = random.randint(1, 6)
            index = 2
            win_value = get_games(user_id=user_id).get('bet') * index
            if result_value == int(data['predict']):
                status = True
                updater = int(get_games(user_id=user_id).get('bet'))
                update_balance(user_id=user_id, amount=updater)
                text = f"✅ Ваше предсказание для игры в 🎲 Кубик верное.\n🏆 Сумма выигрыша составит *{win_value} $ADREF* с коефициентом *x{index}*!"
                update_game(user_id=user_id, amount=status, status="status")
            else:
                status = False
                updater = 0 - int(get_games(user_id=user_id).get('bet'))
                update_balance(user_id=user_id, amount=updater)
                update_game(user_id=user_id, amount=status, status="status")
                text = f"❌ Ваше предсказание для игры в 🎲 Кубик не верное.\n🏆 Сумма проигрыша составит *{get_games(user_id=user_id).get('bet')} $ADREF*."

        elif user_game_state == "basketball":
            yes_no_list = ["ДА", "НЕТ"]
            random_choice = random.choice(yes_no_list)
            index = 1.75
            win_value = get_games(user_id=user_id).get('bet') * index
            if random_choice == str(data['predict']):
                status = True
                updater = int(get_games(user_id=user_id).get('bet'))
                update_balance(user_id=user_id, amount=updater)
                text = f"✅ Ваше предсказание для игры в 🏀 Баскетбол верное.\n🏆 Сумма выигрыша составит *{win_value} $ADREF* с коефициентом *x{index}*!"
                update_game(user_id=user_id, amount=status, status="status")
            else:
                status = False
                updater = 0 - int(get_games(user_id=user_id).get('bet'))
                update_balance(user_id=user_id, amount=updater)
                update_game(user_id=user_id, amount=status, status="status")
                text = f"❌ Ваше предсказание для игры в 🏀 Баскетбол не верное.\n🏆 Сумма проигрыша составит *{get_games(user_id=user_id).get('bet')} $ADREF*."

        elif user_game_state == "football":
            yes_no_list = ["ДА", "НЕТ"]
            random_choice = random.choice(yes_no_list)
            index = 1.5
            win_value = get_games(user_id=user_id).get('bet') * index
            if random_choice == str(data['predict']):
                status = True
                updater = int(get_games(user_id=user_id).get('bet'))
                update_balance(user_id=user_id, amount=updater)
                text = f"✅ Ваше предсказание для игры в ⚽ Футбол верное.\n🏆 Сумма выигрыша составит *{win_value} $ADREF* с коефициентом *x{index}*!"
                update_game(user_id=user_id, amount=status, status="status")
            else:
                status = False
                updater = 0 - int(get_games(user_id=user_id).get('bet'))
                update_balance(user_id=user_id, amount=updater)
                update_game(user_id=user_id, amount=status, status="status")
                text = f"❌ Ваше предсказание для игры в ⚽ Футбол не верное.\n🏆 Сумма проигрыша составит *{get_games(user_id=user_id).get('bet')} $ADREF*."

        elif user_game_state == "wheel_of_fortune":
            result_value = random.randint(1, 12)
            index = 3
            win_value = get_games(user_id=user_id).get('bet') * index
            if result_value == int(data['predict']):
                status = True
                updater = int(get_games(user_id=user_id).get('bet'))
                update_balance(user_id=user_id, amount=updater)
                text = f"✅ Ваше предсказание для игры в 🎡 Колесо Фортуны верное.\n🏆 Сумма выигрыша составит *{win_value} $ADREF* с коефициентом *x{index}*!"
                update_game(user_id=user_id, amount=status, status="status")
            else:
                status = False
                updater = 0 - int(get_games(user_id=user_id).get('bet'))
                update_balance(user_id=user_id, amount=updater)
                update_game(user_id=user_id, amount=status, status="status")
                text = f"❌ Ваше предсказание для игры в 🎡 Колесо Фортуны не верное.\n🏆 Сумма проигрыша составит *{get_games(user_id=user_id).get('bet')} $ADREF*."

        elif user_game_state == "coin_toss":
            coin_list = ["ОРЕЛ", "РЕШКА"]
            random_choice = random.choice(coin_list)
            index = 1.5
            win_value = get_games(user_id=user_id).get('bet') * index
            if random_choice == str(data['predict']):
                status = True
                updater = int(get_games(user_id=user_id).get('bet'))
                update_balance(user_id=user_id, amount=updater)
                text = f"✅ Ваше предсказание для игры в 🪙 Монетку верное.\n🏆 Сумма выигрыша составит *{win_value} $ADREF* с коефициентом *x{index}*!"
                update_game(user_id=user_id, amount=status, status="status")
            else:
                status = False
                updater = 0 - int(get_games(user_id=user_id).get('bet'))
                update_balance(user_id=user_id, amount=updater)
                update_game(user_id=user_id, amount=status, status="status")
                text = f"❌ Ваше предсказание для игры в 🪙 Монетку не верное.\n🏆 Сумма проигрыша составит *{get_games(user_id=user_id).get('bet')} $ADREF*."

        elif user_game_state == "roulette":
            result_value = random.randint(0, 36)
            index = 3.2
            win_value = get_games(user_id=user_id).get('bet') * index
            if result_value == int(data['predict']):
                status = True
                updater = int(get_games(user_id=user_id).get('bet'))
                update_balance(user_id=user_id, amount=updater)
                text = f"✅ Ваше предсказание для игры в 🎰 Рулетку верное.\n🏆 Сумма выигрыша составит *{win_value} $ADREF* с коефициентом *x{index}*!"
                update_game(user_id=user_id, amount=status, status="status")
            else:
                status = False
                updater = 0 - int(get_games(user_id=user_id).get('bet'))
                update_balance(user_id=user_id, amount=updater)
                update_game(user_id=user_id, amount=status, status="status")
                text = f"❌ Ваше предсказание для игры в 🎰 Рулетку не верное.\n🏆 Сумма проигрыша составит *{get_games(user_id=user_id).get('bet')} $ADREF*."

        elif user_game_state == "guess_number":
            result_value = random.randint(1, 9)
            index = 1.66
            win_value = get_games(user_id=user_id).get('bet') * index
            if result_value == int(data['predict']):
                status = True
                updater = int(get_games(user_id=user_id).get('bet'))
                update_balance(user_id=user_id, amount=updater)
                text = f"✅ Ваше предсказание для игры в 🔢 Угадай число верное.\n🏆 Сумма выигрыша составит *{win_value} $ADREF* с коефициентом *x{index}*!"
                update_game(user_id=user_id, amount=status, status="status")
            else:
                status = False
                updater = 0 - int(get_games(user_id=user_id).get('bet'))
                update_balance(user_id=user_id, amount=updater)
                update_game(user_id=user_id, amount=status, status="status")
                text = f"❌ Ваше предсказание для игры в 🔢 Угадай число не верное.\n🏆 Сумма проигрыша составит *{get_games(user_id=user_id).get('bet')} $ADREF*."

        elif user_game_state == "lucky_ticket":
            result_value = random.randint(1, 999)
            index = 100
            win_value = get_games(user_id=user_id).get('bet') * index
            if result_value == int(data['predict']):
                status = True
                updater = int(get_games(user_id=user_id).get('bet'))
                update_balance(user_id=user_id, amount=updater)
                text = f"✅ Ваше предсказание для игры в 🎟️ Счасливый билет верное.\n🏆 Сумма выигрыша составит *{win_value} $ADREF* с коефициентом *x{index}*!"
                update_game(user_id=user_id, amount=status, status="status")
            else:
                status = False
                updater = 0 - int(get_games(user_id=user_id).get('bet'))
                update_balance(user_id=user_id, amount=updater)
                update_game(user_id=user_id, amount=status, status="status")
                text = f"❌ Ваше предсказание для игры в 🎟️ Счасливый билет не верное.\n🏆 Сумма проигрыша составит *{get_games(user_id=user_id).get('bet')} $ADREF*."

        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=data.get('id_to_edit'),
            text=text,
            reply_markup=back_button,
            parse_mode='Markdown',
        )
        delete_games(user_id=user_id)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await state.reset_state()

#payment callback
@dp.callback_query_handler(lambda c: c.data == "payment")
async def payment_callback(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    text_warning = (
            f"⚠️ *Для вывода средств установите Telegram Username!*\n\n"
            f"🎉 Спасибо, что вы с нами!"
        )

    if username is None:
        await bot.edit_message_text(
                chat_id=chat_id,
                message_id=callback_query.message.message_id,
                text=text_warning,
                reply_markup=back_menu(),
                parse_mode="Markdown"
            )
    else:
        if find_user(user_id=user_id):
            chat_id = callback_query.message.chat.id
            user_data = get_info(user_id)

            first_name = callback_query.from_user.first_name
            balance = user_data["balance"]
            payment_message = (
                f"👋 *Здравствуйте, {first_name}!*\n\n"
                f"💰 Средства доступные к выводу: *{balance} $ADREF*\n"
                f"🎉 Спасибо, что вы с нами!"
            )

            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=callback_query.message.message_id,
                    text=payment_message,
                    reply_markup=payment(),
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Ошибка при редактировании сообщения: {e}")
                await bot.answer_callback_query(
                    callback_query.id,
                    text="Произошла ошибка при отображении кабинета. Попробуйте позже.",
                    show_alert=True
                )
        else:
            insert_user(user_id=user_id)
            chat_id = callback_query.message.chat.id
            user_data = get_info(user_id)

            first_name = callback_query.from_user.first_name
            balance = user_data["balance"]
            payment_message = (
                f"👋 *Здравствуйте, {first_name}!*\n\n"
                f"💰 Средства доступные к выводу: *{balance} $ADREF*\n"
                f"Вывод возможен только от *1000 $ADREF*\n"
                f"1000 $ADREF = 3 $USDT\n"
                f"🎉 Спасибо, что вы с нами!"
            )

            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=callback_query.message.message_id,
                    text=payment_message,
                    reply_markup=payment(),
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Ошибка при редактировании сообщения: {e}")
                await bot.answer_callback_query(
                    callback_query.id,
                    text="Произошла ошибка при отображении кабинета. Попробуйте позже.",
                    show_alert=True
                )

@dp.callback_query_handler(lambda c: c.data == "payment_form")
async def payment_callback(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    user_data = get_info(user_id)
    username = callback_query.from_user.username

    if user_data:

        balance = user_data["balance"]

        if balance >= 1000:
            ticket_id = generate_ticket_id(username)
            first_name = callback_query.from_user.username
            status = "opened"

            payment_ticket = (
                f"👋 №{ticket_id}\n\n"
                f"👁️ Инициатор : @{first_name}\n"
                f"🪙 Сумма : {balance}\n"
                f"🎉 Статус заявки: {status}"
            )
            text = (
                f"👋 *Здравствуйте, {first_name}!*\n\n"
                f"✅ На вашем балансе : *{balance} $ADREF*\n"
                f"Вы отправили заявку на вывод, она будет рассмотрена в течении 72 часов, администрация свяжеться с вами\n"
                f"*1000 $ADREF = 3 $USDT*\n"
                f"🎉 Спасибо, что вы с нами!"
            )

            try:
                admin_id = administrators.get("developer")
                await bot.send_message(admin_id, payment_ticket, reply_markup=payment_admin(ticket_id=ticket_id, user_id=user_id, balance=balance))
            except Exception as e:
                print(e)
            
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=callback_query.message.message_id,
                text=text,
                reply_markup=back_menu(),
                parse_mode="Markdown"
            )

        else:
            first_name = callback_query.from_user.first_name
            text = (
                f"👋 *Здравствуйте, {first_name}!*\n\n"
                f"❌ На вашем балансе недостаточно средств: *{balance} $ADREF*\n\n"
                f"Вывод возможен только от *1000 $ADREF*\n"
                f"1000 $ADREF = 3 $USDT\n\n"
                f"🎉 Спасибо, что вы с нами!"
            )
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=callback_query.message.message_id,
                text=text,
                reply_markup=back_menu(),
                parse_mode="Markdown"
            )

#payment admin
@dp.callback_query_handler(lambda c: c.data.startswith("answered_"))
async def payment_admin_callback(callback_query: CallbackQuery):

    ticket_id = callback_query.data.split('_')[1]
    user_id = int(callback_query.data.split('_')[2])
    balance = int(callback_query.data.split('_')[3])
    balance_set = balance - balance
    try:
        delete_ticket(ticket_id=ticket_id)
        set_balance(user_id=user_id, amount=balance_set)
        await bot.answer_callback_query(callback_query.id, text=f"Тикет №{ticket_id} был исполнен и удален.")
        await bot.send_message(callback_query.from_user.id, f"Тикет №{ticket_id} был исполнен и удален.")

    except Exception as e:
        print(e)

#tasks callback
@dp.callback_query_handler(lambda c: c.data == "tasks")
async def payment_callback(callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id

    tasks = get_tasks()
    
    if count_tasks() != 0:
        text = f"Активно {count_tasks()} заданий!"
        keyboard = InlineKeyboardMarkup(row_width=1)
        for task in tasks:
            button = InlineKeyboardButton(task['name'], callback_data=f"task_{str(task['ticket_id'])}")
            keyboard.add(button)
        back_button = InlineKeyboardButton("⬅️ Назад", callback_data="main_menu_admin")
        keyboard.add(back_button)
    else:
        text = "На данный момент нет активных заданий!"
        keyboard = back_menu()
    
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=callback_query.message.message_id,
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

#admin callback
@dp.callback_query_handler(lambda c: c.data == "admin")
async def payment_callback(callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=callback_query.message.message_id,
        text="Функции:",
        reply_markup=admin_panel(),
        parse_mode="Markdown"
    )

#tasks admin
@dp.callback_query_handler(lambda c: c.data == "tasks_admin")
async def tasks_admin_callback(callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id

    if count_tasks() != 0:
        text = f"Активно {count_tasks()} заданий!"
    else:
        text = "На данный момент нет активных заданий!"
    
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=callback_query.message.message_id,
        text=text,
        reply_markup=admin_panel_tasks(),
        parse_mode="Markdown"
    )

# list admin
@dp.callback_query_handler(lambda c: c.data == "list_admin")
async def list_admin_callback(callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id

    tasks = get_tasks()
    
    if count_tasks() != 0:
        text = f"Активно {count_tasks()} заданий!"
        keyboard = InlineKeyboardMarkup(row_width=1)
        for task in tasks:
            button = InlineKeyboardButton(task['name'], callback_data=f"task_{str(task['ticket_id'])}")
            keyboard.add(button)
        back_button = InlineKeyboardButton("⬅️ Назад", callback_data="main_menu_admin")
        keyboard.add(back_button)
    else:
        text = "На данный момент нет активных заданий!"
        keyboard = back_menu_admin()

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=callback_query.message.message_id,
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query_handler(lambda c: c.data.startswith("task_"))
async def task_detail_callback(callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    task_id = callback_query.data.split('_')[1]

    task = get_task(int(task_id))

    if task:
        text = f"Задание: {task['name']}\n"
        text += f"Описание: {task.get('description', 'Нет описания')}\n"
        text += f"Ссылка: {task.get('link', 'Нет ссылки')}\n"
        keyboard = task_keyboard(task_id)
    else:
        text = "Задание не найдено."
        keyboard = back_menu_admin()

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=callback_query.message.message_id,
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# check sub
@dp.callback_query_handler(lambda c: c.data.startswith("check_subscription_"))
async def check_subscription(callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    task_id = callback_query.data.split('_')[2]
    user_id = callback_query.from_user.id

    try:
        user_status = await bot.get_chat_member(CHANNEL_ID, chat_id)

        if user_status.status in ['member', 'administrator', 'creator']:
            if get_completed_tasks(user_id=user_id):
                if get_task_private(user_id=user_id, ticket_id=task_id):
                    text = "Вам уже было начислено 100 $ADREF."
                else:
                    text = "Вы успешно подписаны на канал! Вам начислено 100 $ADREF."
                    update_completed(user_id=user_id, ticket_id=task_id)
                    update_balance(user_id=user_id, amount=100)
            else:
                insert_completed(user_id=user_id, ticket_id=task_id)
                text = "Вы успешно подписаны на канал! Вам начислено 100 $ADREF."
                update_balance(user_id=user_id, amount=100)

        else:
            text = "Вы не подписаны на канал. Пожалуйста, подпишитесь, чтобы выполнить задание."
    
    except Exception as e:
        print(e)
        text = "Произошла ошибка. Пожалуйста, попробуйте снова."

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=callback_query.message.message_id,
        text=text,
        reply_markup=task_keyboard(task_id),
        parse_mode="Markdown"
    )

#add task
@dp.callback_query_handler(lambda c: c.data == "add_task")
async def add_task_callback(callback_query: types.CallbackQuery, state:FSMContext):
    async with state.proxy() as data:
        await ClientStates.name.set()
        msg = await callback_query.message.edit_text(
            text=f"Введите имя задания:",
            reply_markup=back_button_form,
            parse_mode='MarkdownV2',
        )
        data['id_to_edit'] = msg.message_id

@dp.message_handler(state=ClientStates.name)
async def name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text.strip()
        chat_id = message.chat.id
        if data['name']:
            data['random_id'] = add_task(data['name'])
        else:
            print('ERROR TASK')
        
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=data.get('id_to_edit'),
            text=f"Успешно!\n\nТеперь отправьте ссылку:",
            reply_markup=back_button_form_admin,
            parse_mode='Markdown',
        )
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await ClientStates.link.set()
        
@dp.message_handler(state=ClientStates.link)
async def link(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['link'] = message.text.strip()
        chat_id = message.chat.id
        if data['link']:
            set_link(data['link'], data.get('random_id'))
        else:
            print('ERROR TASK')
        
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=data.get('id_to_edit'),
            text=f"Успешно!",
            reply_markup=back_menu_admin(),
            parse_mode='Markdown',
        )
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await state.finish()

#delete task
@dp.callback_query_handler(lambda c: c.data == "delete_task")
async def delete_task_callback(callback_query: types.CallbackQuery, state:FSMContext):
    chat_id = callback_query.message.chat.id

    tasks = get_tasks()
    
    if count_tasks() != 0:
        text = f"Активно {count_tasks()} заданий!"
        keyboard = InlineKeyboardMarkup(row_width=1)
        for task in tasks:
            button = InlineKeyboardButton(task['name'], callback_data=f"show_{str(task['ticket_id'])}")
            keyboard.add(button)
        back_button = InlineKeyboardButton("⬅️ Назад", callback_data="main_menu_admin")
        keyboard.add(back_button)
    else:
        text = "На данный момент нет активных заданий!"
        keyboard = back_menu_admin()

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=callback_query.message.message_id,
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query_handler(lambda c: c.data.startswith("show_"))
async def delete_task_detail_callback(callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    task_id = callback_query.data.split('_')[1]

    task = get_task(int(task_id))

    if task:
        text = f"Задание: {task['name']}\n"
        text += f"Описание: {task.get('description', 'Нет описания')}\n"
        text += f"Ссылка: {task.get('link', 'Нет ссылки')}\n"
        keyboard = task_keyboard_delete(task_id)
    else:
        text = "Задание не найдено."
        keyboard = back_menu_admin()

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=callback_query.message.message_id,
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query_handler(lambda c: c.data.startswith("0x0_"))
async def check_subscription(callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    task_id = str(callback_query.data.split('_')[1])
    user_id = callback_query.from_user.id

    try:
        delete_task(ticket_id=task_id, user_id=user_id)
        text = f"Задание с идентификатором {task_id} удалено."
    except Exception as e:
        print(e)
        text = "Произошла ошибка при удалении задания."

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=callback_query.message.message_id,
        text=text,
        reply_markup=task_keyboard_delete(task_id),
        parse_mode="Markdown"
    )

#referals
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types

@dp.callback_query_handler(lambda c: c.data == "ref")
async def tasks_admin_callback(callback_query: types.CallbackQuery):

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🖇️ Получить реферальную ссылку", callback_data="get_ref"),
        InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")
    )

    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="🎉 Добро пожаловать в реферальную систему!\n\n"
             "🔹 Нажмите на кнопку ниже, чтобы получить свою реферальную ссылку.",
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data == "get_ref")
async def get_referral_link(callback_query: types.CallbackQuery):
    referrer_id = callback_query.from_user.id
    bot_username = (await bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start={referrer_id}"

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")
    )

    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=f"Ваша реферальная ссылка: {referral_link}",
        reply_markup=keyboard
    )

#back
@dp.callback_query_handler(lambda c: c.data == "back")
async def back_to_games(callback_query: CallbackQuery):

    await bot.edit_message_text(
        text="Выберите игру:",
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=games_keyboard()
    )

#back to list admin
@dp.callback_query_handler(lambda c: c.data == "back_to_list_admin")
async def back_to_games(callback_query: CallbackQuery):

    tasks = get_tasks()
    
    if count_tasks() != 0:
        text = f"Активно {count_tasks()} заданий!"
        keyboard = InlineKeyboardMarkup(row_width=1)
        for task in tasks:
            button = InlineKeyboardButton(task['name'], callback_data=f"task_{str(task['ticket_id'])}")
            keyboard.add(button)
        back_button = InlineKeyboardButton("⬅️ Назад", callback_data="main_menu_admin")
        keyboard.add(back_button)
    else:
        text = "На данный момент нет активных заданий!"
        keyboard = back_menu_admin()

    await bot.edit_message_text(
        text=text,
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=keyboard
    )

#back form
@dp.callback_query_handler(lambda query: query.data == 'back_form', state='*')
async def back_button_callback(callback_query: types.CallbackQuery, state: FSMContext):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=callback_query.message.message_id,
        text='Выберите мини-игру 🎮:',
        reply_markup=games_keyboard(),
        parse_mode='Markdown',
    )
    delete_games(user_id=user_id)
    await state.reset_state()

#back form admin
@dp.callback_query_handler(lambda query: query.data == 'back_form_admin', state='*')
async def back_button_callback(callback_query: types.CallbackQuery, state: FSMContext):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=callback_query.message.message_id,
        text='Функции:',
        reply_markup=admin_panel_tasks(),
        parse_mode='Markdown',
    )
    delete_games(user_id=user_id)
    await state.reset_state()

#main menu
@dp.callback_query_handler(lambda c: c.data == "main_menu")
async def back_to_main_menu(callback_query: CallbackQuery):
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Вы вернулись в главное меню.",
        reply_markup=main_keyboard()
    )

#main menu admin
@dp.callback_query_handler(lambda c: c.data == "main_menu_admin")
async def back_to_main_menu(callback_query: CallbackQuery):
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Вы вернулись в главное меню.",
        reply_markup=main_keyboard_admin()
    )

#boot
async def main():
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling()
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
