# subscription_middleware.py

from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler

class SubscriptionMiddleware(BaseMiddleware):
    def __init__(self, channel_id: str, subscribe_keyboard):
        super().__init__()
        self.channel_id = channel_id
        self.subscribe_keyboard = subscribe_keyboard

    async def on_pre_process_message(self, message: types.Message, data: dict):
        user_id = message.from_user.id
        member = await message.bot.get_chat_member(chat_id=self.channel_id, user_id=user_id)

        if member.status in ('left', 'kicked'):
            await message.answer(
                "Пожалуйста, подпишитесь на наш канал, чтобы использовать бота.",
                reply_markup=self.subscribe_keyboard()
            )
            raise CancelHandler()
