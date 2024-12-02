from functools import wraps

from aiogram import types

from settings.settings import ADMINS

from utils.text_answers import answers

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
