from functools import wraps

from aiogram import types
from aiogram.fsm.context import FSMContext

from settings.settings import ADMINS

from utils.text_answers import answers

from database.users_db_manager import user_get_or_none

CANCEL_REMINDER = answers.get('CANCEL_REMINDER')


def is_admin(func):
    @wraps(func)
    async def wrapper(message: types.Message, *args, **kwargs):
        admins = [int(admin) for admin in str(ADMINS).split(',')]
        if message.from_user.id not in admins:
            not_admin = 'Команда доступна только администраторам.'
            await message.answer(not_admin)
            return
        return await func(message, *args, **kwargs)

    return wrapper


def is_private_chat(func):
    @wraps(func)
    async def wrapper(message: types.Message, *args, **kwargs):
        pass

    return wrapper


def is_text(func):
    @wraps(func)
    async def wrapper(message: types.Message, *args, **kwargs):
        if not message.text:
            await message.answer(
                text='Неправильный тип данных. Необходимо отправить '
                     'текстовое сообщение (или нажать на одну из кнопок, '
                     'если они есть).\n\n'
                     f'{CANCEL_REMINDER}'
            )
            return
        return await func(message, *args, **kwargs)

    return wrapper


def survey_completion_status(func):
    @wraps(func)
    async def wrapper(message: types.Message, *args, **kwargs):
        user = await user_get_or_none(telegram_id=message.from_user.id)
        if user:
            if user.approved is True:
                await message.answer(
                    text='Ты уже в команде, зачем еще раз проходить опрос?'
                )
                return
            if user.approved is False:
                await message.answer(
                    text='Во вступлении в команду отказано. Больше опрос '
                         'пройти нельзя.'
                )
                return
            if user.callsign:
                await message.answer(
                    text='Твоя анкета уже зарегистрирована. Как только '
                         'командир команды с ней ознакомится, он свяжется с тобой '
                         'через бота.\n\n'
                         'Командир команды имеет право отказать во вступлении в команду '
                         'без объяснения причин.\n\n'
                         'В случае отказа уведомление так же придет в диалог с чат-ботом.'
                )
                return
        return await func(message, *args, **kwargs)
    return wrapper


def check_user_existence(func):
    @wraps(func)
    async def wrapper(callback: types.CallbackQuery, state: FSMContext, *args, **kwargs):
        try:
            telegram_id = int(callback.data.split(':')[2])
        except IndexError:
            telegram_id = int(callback.data.split(':')[1].split('-')[0])
        user = await user_get_or_none(telegram_id=telegram_id)

        if not user:
            await callback.answer(
                text='Пользователь не найден',
                show_alert=True
            )
            return
        return await func(callback, state, user, *args, **kwargs)
    return wrapper
