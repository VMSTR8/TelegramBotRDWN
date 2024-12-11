import re
from datetime import datetime

from typing import Tuple

from aiogram import types, Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from utils.decorators import check_user_existence
from utils.text_utils import merge_message_parts

from database.users_db_manager import (
    user_update,
    is_callsign_taken,
)

from utils.text_answers import answers

router = Router()

CANCEL_REMINDER = answers.get('CANCEL_REMINDER')

LATIN_REGEX = r'[^a-zA-Z]'


class User(StatesGroup):
    new_name = State()
    new_callsign = State()


async def prepare_for_editing(
        callback: types.CallbackQuery,
        state: FSMContext,
        user: dict,
        new_state,
        editing_field: str,
        field_name: str,
        field_value: str
) -> None:
    telegram_id = user.telegram_id
    await state.clear()
    await state.set_state(new_state)
    await state.update_data(telegram_id=telegram_id, **{field_name: field_value})
    await callback.message.answer(
        text=f'Введи новое значение для поля '
             f'<b>{editing_field}</b> '
             f'пользователя <b>{field_value}</b>\n\n'
             f'{CANCEL_REMINDER}',
        parse_mode=ParseMode.HTML
    )


def parse_callback_data(callback_data: str, user: dict) -> Tuple[int, int]:
    parts = callback_data.split('-')
    print(parts)
    page = parts[1]
    telegram_id = user.telegram_id
    return telegram_id, page


@router.callback_query(F.data.startswith('user_edit:имя'))
@check_user_existence
async def edit_user_name(callback: types.CallbackQuery, state: FSMContext, user: dict) -> None:
    await prepare_for_editing(
        callback=callback,
        state=state,
        user=user,
        new_state=User.new_name,
        editing_field='ФИО',
        field_name='callsign',
        field_value=user.callsign.capitalize()
    )


@router.message(User.new_name)
async def validate_new_name(message: types.Message, state: FSMContext) -> None:
    new_name = await merge_message_parts(message=message, state=state, key='new_name')

    if not new_name:
        return

    if len(new_name) > 100:
        await message.answer(
            text='Превышена длинна в 100 символов, '
                 'введи имя заново не превышая лимит.\n\n'
                 f'{CANCEL_REMINDER}',
            parse_mode=ParseMode.HTML
        )
        return

    data = await state.get_data()
    telegram_id = data.get('telegram_id')

    await user_update(telegram_id=telegram_id, name=new_name.lower())
    await message.answer(
        text=f'Для <b>{data.get("callsign").capitalize()}</b> '
             f'установлено новые ФИО: '
             f'<b>{" ".join(name.capitalize() for name in new_name.split())}</b>',
        parse_mode=ParseMode.HTML
    )
    await state.clear()


@router.callback_query(F.data.startswith('user_edit:позывной'))
@check_user_existence
async def edit_user_callsign(callback: types.CallbackQuery, state: FSMContext, user: dict) -> None:
    await prepare_for_editing(
        callback=callback,
        state=state,
        user=user,
        new_state=User.new_callsign,
        editing_field='Позывной',
        field_name='callsign',
        field_value=user.callsign.capitalize()
    )


@router.message(User.new_callsign)
async def validate_new_callsign(message: types.Message, state: FSMContext) -> None:
    new_callsign = await merge_message_parts(message=message, state=state, key='new_callsign')

    if not new_callsign:
        return

    new_callsign = new_callsign.lower()

    if len(new_callsign) > 10:
        await message.answer(
            text='Превышена длина позывного в 10 символов, '
                 'введи позывной заново не превышая лимит.\n\n'
                 f'{CANCEL_REMINDER}',
        )
        return

    sanitized_callsign = re.sub(LATIN_REGEX, '', new_callsign)

    if not sanitized_callsign:
        await message.answer(
            text='Неверный формат позывного. Текст должен содержать '
                 'только латинские символы.\n\n'
                 f'{CANCEL_REMINDER}',
        )
        return

    callsign_taken = await is_callsign_taken(callsign=sanitized_callsign)

    if callsign_taken:
        await message.answer(
            text=f'Позывной <b>{sanitized_callsign.capitalize()}</b> '
                 'уже занят, придется выбрать другой позывной.\n\n'
                 f'{CANCEL_REMINDER}',
            parse_mode=ParseMode.HTML
        )
        return

    data = await state.get_data()
    telegram_id = data.get('telegram_id')
    await user_update(telegram_id=telegram_id, callsign=sanitized_callsign)
    await message.answer(
        text=f'Для <b>{data.get("callsign").capitalize()}</b> '
             f'установлен новый позывной: '
             f'<b>{new_callsign.capitalize()}</b>',
        parse_mode=ParseMode.HTML
    )
    await state.clear()


@router.callback_query(F.data.startswith('user_edit:возраст'))
async def edit_user_age(callback: types.CallbackQuery) -> None:
    pass


@router.callback_query(F.data.startswith('user_edit:авто'))
@check_user_existence
async def edit_user_car(callback: types.CallbackQuery, state: FSMContext, user: dict) -> None:
    if await state.get_state() is not None:
        await callback.message.answer(
            text='Выполнение команды прекращено.'
        )
    await state.clear()
    telegram_id = user.telegram_id
    new_car_value = not user.car

    await user_update(telegram_id=telegram_id, car=new_car_value)

    await callback.answer(
        text=f'Для пользователя {user.callsign.capitalize()} '
             f'изменено НАЛИЧИЕ АВТО на '
             f'"{"Есть" if new_car_value else "Нет"}"',
        show_alert=True
    )


@router.callback_query(F.data.startswith('user_edit:бронь'))
@check_user_existence
async def edit_user_reserved(callback: types.CallbackQuery, state: FSMContext, user: dict) -> None:
    if await state.get_state() is not None:
        await callback.message.answer(
            text='Выполнение команды прекращено.'
        )
    if user.approved is None or user.approved is False:
        await callback.answer(
            text='Пользователь не состоит в команде.',
            show_alert=True
        )
        return
    await state.clear()
    telegram_id = user.telegram_id
    new_reserved_value = not user.reserved

    await user_update(telegram_id=telegram_id, reserved=new_reserved_value)

    await callback.answer(
        text=f'Для пользователя {user.callsign.capitalize()} '
             f'изменено ОСВОБОЖДЕНИЕ ОТ ОПРОСОВ на '
             f'"{"Освобожден" if new_reserved_value else "Не освобожден"}"',
        show_alert=True
    )


@router.callback_query(F.data.startswith('user_edit:пользователя'))
async def delete_user(callback: types.CallbackQuery) -> None:
    pass
