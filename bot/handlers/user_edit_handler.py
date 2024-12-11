import re
from datetime import datetime

from aiogram import types, Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from utils.decorators import check_user_existence
from utils.text_utils import merge_message_parts

from database.users_db_manager import (
    user_update,
    is_callsign_taken,
    user_get_or_none,
    user_delete,
    get_all_users,
)

from utils.text_answers import answers
from utils.keyboards import (
    generate_delete_user_keyboard,
    generate_all_users_keyboard
)

router = Router()

CANCEL_REMINDER = answers.get('CANCEL_REMINDER')

LATIN_REGEX = r'[^a-zA-Z]'


class User(StatesGroup):
    new_name = State()
    new_callsign = State()
    new_age = State()


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
        await state.update_data(new_name='')
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
        await state.update_data(new_callsign='')
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
@check_user_existence
async def edit_user_age(callback: types.CallbackQuery, state: FSMContext, user: dict) -> None:
    await prepare_for_editing(
        callback=callback,
        state=state,
        user=user,
        new_state=User.new_age,
        editing_field='ВОЗРАСТ',
        field_name='callsign',
        field_value=user.callsign.capitalize()
    )


@router.message(User.new_age)
async def validate_new_age(message: types.Message, state: FSMContext) -> None:
    new_date = await merge_message_parts(message=message, state=state, key='new_age')

    if not new_date:
        return

    if len(new_date) > 10:
        await state.update_data(new_age='')
        await message.answer(
            text='Превышена максимальная длина сообщения в 10 '
                 'символов. Надо ввести корректную дату.\n'
                 'Формат: ДД.ММ.ГГГГ (10 символов ровно)\n\n'
                 f'{CANCEL_REMINDER}',
        )
        return
    try:
        birth_date = datetime.strptime(new_date, '%d.%m.%Y')
    except ValueError:
        await message.answer(
            text='Неверный формат даты! Нужно указать дату рождения '
                 'в формате ДД.ММ.ГГГГ, например:\n\n'
                 '<b>01.01.1990</b>\n\n'
                 f'{CANCEL_REMINDER}',
        )
        return

    today = datetime.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    if age < 18:
        await message.answer(
            text='Возраст меньше 18 лет установить нельзя.\n\n'
                 f'{CANCEL_REMINDER}',
        )
        return

    data = await state.get_data()
    telegram_id = data.get('telegram_id')
    await user_update(telegram_id=telegram_id, age=birth_date)
    await message.answer(
        text=f'Для пользователя {data.get("callsign").capitalize()} '
             f'установлена новая дата рождения: '
             f'<b>{birth_date.strftime("%d.%m.%Y")}</b> [Возраст:<b>{age}</b>]'
    )
    await state.clear()


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


@router.callback_query(F.data.startswith('delete_user'))
async def delete_user(callback: types.CallbackQuery) -> None:
    telegram_id = int(callback.data.split(':')[1].split('-')[0])
    page = int(callback.data.split('-')[1])

    user = await user_get_or_none(telegram_id=telegram_id)
    await callback.message.edit_text(
        text=f'Уверены, что хотите удалить пользователя '
             f'{user.callsign.capitalize()}?',
        reply_markup=generate_delete_user_keyboard(telegram_id=telegram_id, page=page)
    )


@router.callback_query(F.data.startswith('confirm_user_deletion'))
async def confirm_user_deletion(callback: types.CallbackQuery) -> None:
    telegram_id = int(callback.data.split(':')[1].split('-')[0])
    page = int(callback.data.split('-')[1])

    await user_delete(telegram_id=telegram_id)

    await callback.answer(
        text='Пользователь удален',
        show_alert=True
    )

    users = await get_all_users()

    await callback.message.edit_text(
        text='Все пользователи',
        reply_markup=generate_all_users_keyboard(users=users, page=page)
    )
