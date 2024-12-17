from datetime import datetime

from aiogram import types, Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from utils.decorators import (
    check_user_existence,
    is_text,
)
from utils.text_utils import merge_message_parts, calculate_age

from database.users_db_manager import (
    user_update,
    is_callsign_taken,
    user_delete,
    get_all_users,
    user_get_or_none,
)

from utils.text_answers import answers
from utils.keyboards import (
    generate_delete_user_keyboard,
    generate_all_users_keyboard,
    generate_back_to_admin_keyboard,
    generate_edit_user_keyboard,
)

from validators.user_validators import general_user_validation

router = Router()

CANCEL_REMINDER = answers.get('CANCEL_REMINDER')

EDIT_USER_MENU_BUTTONS = [
    'Ред. имя',
    'Ред. позывной',
    'Ред. возраст',
    'Ред. авто',
    'Ред. бронь'
]


class User(StatesGroup):
    """
    State group for managing user data updates in the FSM.

    Attributes:
        new_name (State): State for editing the user's name.
        new_callsign (State): State for editing the user's callsign.
        new_age (State): State for editing the user's age.
    """
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
    """
    Prepares the FSM state and context for editing a specific user field.

    Args:
        callback (types.CallbackQuery): Callback query instance triggering the edit.
        state (FSMContext): Finite state machine context.
        user (dict): User data dictionary.
        new_state: FSM state to transition to.
        editing_field (str): Display name of the field being edited.
        field_name (str): Key of the field in the user data.
        field_value (str): Current value of the field.

    Returns:
        None
    """
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


@router.callback_query(F.data.startswith('users_page-'))
async def change_users_page(callback: types.CallbackQuery) -> None:
    page = int(callback.data.split('-')[1])
    users = await get_all_users()
    if not users:
        await callback.message.edit_text(
            text='Нет сохраненных пользователей чат-бота',
            reply_markup=generate_back_to_admin_keyboard()
        )

    await callback.message.edit_text(
        text='Все пользователи',
        reply_markup=generate_all_users_keyboard(users=users, page=page)
    )


@router.callback_query(F.data.startswith('user:'))
async def show_user_info(callback: types.CallbackQuery) -> None:
    parts = callback.data.split('-')
    telegram_id = int(parts[0].split(':')[1])
    page = int(parts[1]) if len(parts) > 1 else 1

    user = await user_get_or_none(telegram_id=telegram_id)
    if not user:
        await callback.answer(
            text='Пользователь не был найден. Сейчас откроется '
                 'меню со всеми пользователями.',
            show_alert=True
        )
        await callback.message.edit_text(
            text='Все пользователи',
            reply_markup=generate_all_users_keyboard(users=await get_all_users(), page=page)
        )
        return
    name = ' '.join(word.capitalize() for word in user.name.split())
    callsign = user.callsign.capitalize()

    birthdate = user.age
    today = datetime.today()
    try:
        age = (
                today.year -
                birthdate.year -
                ((today.month, today.day) < (birthdate.month, birthdate.day))
        )
    except AttributeError:
        age = 'Что-то пошло не так'
    about = user.about
    experience = user.experience
    car = 'Есть' if user.car else 'Нет'
    approved = (
        'Принят в команду' if user.approved is True
        else 'Отказано' if user.approved is False
        else 'На рассмотрении'
    )
    reserved = (
        'Освобожден' if user.reserved is True
        else 'Не освобожден' if user.reserved is False
        else 'Еще не в команде'
    )
    await callback.message.edit_text(
        text=f'<b>1. ФИО:</b> {name}\n'
             f'<b>2. ПОЗЫВНОЙ:</b> {callsign}\n'
             f'<b>3. ВОЗРАСТ:</b> {age}\n'
             f'<b>4. О СЕБЕ:</b> {about}\n'
             f'<b>5. ОБ ОПЫТЕ:</b> {experience}\n'
             f'<b>6. НАЛИЧИЕ АВТО:</b> {car}\n'
             f'<b>7. ЧЛЕНСТВО В КОМАНДЕ:</b> {approved}\n'
             f'<b>8. ОСОБОЖДЕНИЕ ОТ ОПРОСОВ:</b> {reserved}',
        reply_markup=generate_edit_user_keyboard(
            telegram_id=telegram_id,
            page=page,
            array=EDIT_USER_MENU_BUTTONS
        ),
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data.startswith('back:users_page-'))
async def back_to_users_page(callback: types.CallbackQuery) -> None:
    page = int(callback.data.split('-')[1])

    users = await get_all_users()

    await callback.message.edit_text(
        text='Все пользователи:',
        reply_markup=generate_all_users_keyboard(users=users, page=page)
    )


@router.callback_query(F.data.startswith('user_edit:имя'))
@check_user_existence
async def edit_user_name(callback: types.CallbackQuery, state: FSMContext, user: dict) -> None:
    """
    Handles the callback for editing a user's name.

    Args:
        callback (types.CallbackQuery): Callback query instance triggering the edit.
        state (FSMContext): Finite state machine context.
        user (dict): User data dictionary.

    Returns:
        None
    """
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
@is_text
async def validate_new_name(message: types.Message, state: FSMContext) -> None:
    """
    Validates and updates the user's name.

    Args:
        message (types.Message): Incoming message with the new name.
        state (FSMContext): Finite state machine context.

    Returns:
        None
    """
    new_name = await merge_message_parts(message=message, state=state, key='new_name')

    if not new_name:
        return

    validated_input = await general_user_validation(message=message, state=state, name=new_name)

    if not validated_input:
        return

    data = await state.get_data()
    telegram_id = data.get('telegram_id')

    try:
        await user_update(telegram_id=telegram_id, name=validated_input.name.lower())
    except ValueError:
        await state.clear()
        await message.answer(
            text='Пользователь не был найден. Изменение ФИО '
                 'было отменено.'
        )
        return
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
    """
    Handles the callback for editing a user's callsign.

    Args:
        callback (types.CallbackQuery): Callback query instance triggering the edit.
        state (FSMContext): Finite state machine context.
        user (dict): User data dictionary.

    Returns:
        None
    """
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
@is_text
async def validate_new_callsign(message: types.Message, state: FSMContext) -> None:
    """
    Validates and updates the user's callsign.

    Args:
        message (types.Message): Incoming message with the new callsign.
        state (FSMContext): Finite state machine context.

    Returns:
        None
    """
    new_callsign = await merge_message_parts(message=message, state=state, key='new_callsign')

    if not new_callsign:
        return

    validated_input = await general_user_validation(message=message, state=state, callsign=new_callsign)

    if not validated_input:
        return

    validated_input = validated_input.callsign.lower()

    callsign_taken = await is_callsign_taken(callsign=validated_input)

    if callsign_taken:
        await message.answer(
            text=f'Ошибка: Позывной <b>{validated_input.capitalize()}</b> '
                 'уже занят, придется выбрать другой позывной.\n\n'
                 f'{CANCEL_REMINDER}',
            parse_mode=ParseMode.HTML
        )
        return

    data = await state.get_data()
    telegram_id = data.get('telegram_id')
    try:
        await user_update(telegram_id=telegram_id, callsign=validated_input)
    except ValueError:
        await state.clear()
        await message.answer(
            text='Пользователь не найден. Изменение позывного '
                 'было отменено.'
        )
        return
    await message.answer(
        text=f'Для <b>{data.get("callsign").capitalize()}</b> '
             f'установлен новый позывной: '
             f'<b>{validated_input.capitalize()}</b>',
        parse_mode=ParseMode.HTML
    )
    await state.clear()


@router.callback_query(F.data.startswith('user_edit:возраст'))
@check_user_existence
async def edit_user_age(callback: types.CallbackQuery, state: FSMContext, user: dict) -> None:
    """
    Handles the callback for editing a user's age.

    Args:
        callback (types.CallbackQuery): Callback query instance triggering the edit.
        state (FSMContext): Finite state machine context.
        user (dict): User data dictionary.

    Returns:
        None
    """
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
@is_text
async def validate_new_age(message: types.Message, state: FSMContext) -> None:
    """
    Validates and updates the user's age.

    Args:
        message (types.Message): Incoming message with the new age.
        state (FSMContext): Finite state machine context.

    Returns:
        None
    """
    new_date = await merge_message_parts(message=message, state=state, key='new_age')

    if not new_date:
        return

    validated_input = await general_user_validation(message=message, state=state, age=new_date)

    if not validated_input:
        return

    validated_input = validated_input.age
    age = calculate_age(birth_date=validated_input)

    if age < 18:
        await message.answer(
            text='Ошибка: Возраст меньше 18 лет установить нельзя.\n\n'
                 f'{CANCEL_REMINDER}',
        )
        return

    data = await state.get_data()
    telegram_id = data.get('telegram_id')
    try:
        await user_update(telegram_id=telegram_id, age=validated_input)
    except ValueError:
        await state.clear()
        await message.answer(
            text='Пользователь не был найден. Изменение даты рождения '
                 'было отменено.'
        )
        return
    await message.answer(
        text=f'Для пользователя {data.get("callsign").capitalize()} '
             f'установлена новая дата рождения: '
             f'<b>{validated_input.strftime("%d.%m.%Y")}</b> [Возраст:<b>{age}</b>]'
    )
    await state.clear()


@router.callback_query(F.data.startswith('user_edit:авто'))
@check_user_existence
async def edit_user_car(callback: types.CallbackQuery, state: FSMContext, user: dict) -> None:
    """
    Toggles the "car" attribute of a user.

    Args:
        callback (types.CallbackQuery): Callback query instance triggering the update.
        state (FSMContext): Finite state machine context.
        user (dict): User data dictionary.

    Returns:
        None
    """
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
    """
    Toggles the "reserved" attribute of a user.

    Args:
        callback (types.CallbackQuery): Callback query instance triggering the update.
        state (FSMContext): Finite state machine context.
        user (dict): User data dictionary.

    Returns:
        None
    """
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
@check_user_existence
async def delete_user(callback: types.CallbackQuery, state: FSMContext, user: dict) -> None:
    """
    Initiates the process of deleting a user by prompting for confirmation.

    Args:
        callback (types.CallbackQuery): Callback query instance containing the user's Telegram ID
            and the current page in the callback data.
        state (FSMContext): Finite state machine context to manage ongoing commands.
        user (dict): Dictionary containing user data, such as the callsign.

    Returns:
        None
    """
    telegram_id = int(callback.data.split(':')[1].split('-')[0])
    page = int(callback.data.split('-')[1])
    if await state.get_state() is not None:
        await callback.message.answer(
            text='Выполнение команды прекращено.'
        )
    await state.clear()
    await callback.message.edit_text(
        text=f'Уверены, что хотите удалить пользователя '
             f'{user.callsign.capitalize()}?',
        reply_markup=generate_delete_user_keyboard(telegram_id=telegram_id, page=page)
    )


@router.callback_query(F.data.startswith('confirm_user_deletion'))
async def confirm_user_deletion(callback: types.CallbackQuery) -> None:
    """
    Confirms and performs the deletion of a user.

    Args:
        callback (types.CallbackQuery): Callback query instance containing the user's Telegram ID
            and the current page in the callback data.

    Returns:
        None
    """
    telegram_id = int(callback.data.split(':')[1].split('-')[0])
    page = int(callback.data.split('-')[1])

    try:
        await user_delete(telegram_id=telegram_id)
    except ValueError:
        await callback.answer(
            text='Пользователь не найден, удаление отменено.',
            show_alert=True
        )

        await callback.message.edit_text(
            text='Все пользователи',
            reply_markup=generate_all_users_keyboard(users=await get_all_users(), page=page),
        )
        return

    await callback.answer(
        text='Пользователь удален',
        show_alert=True
    )

    await callback.message.edit_text(
        text='Все пользователи',
        reply_markup=generate_all_users_keyboard(users=await get_all_users(), page=page)
    )
