import re
from datetime import datetime

from aiogram import types, Router, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from utils.decorators import is_admin, check_user_existence
from utils.text_utils import merge_message_parts

from database.users_db_manager import (
    get_all_users,
    user_get_or_none,
    user_update,
    is_callsign_taken,
)

from utils.text_answers import answers

router = Router()

ADMIN_MENU_BUTTONS = [
    'Создать мероприятие',
    'Показать мероприятия',
    'Заявки на вступление',
    'Все пользователи'
]
EDIT_USER_MENU_BUTTONS = [
    'Ред. имя',
    'Ред. позывной',
    'Ред. возраст',
    'Ред. авто',
    'Ред. бронь',
    'Удалить пользователя'
]

CANCEL_REMINDER = answers.get('CANCEL_REMINDER')

LATIN_REGEX = r'[^a-zA-Z]'


class User(StatesGroup):
    new_name = State()
    new_callsign = State()


def generate_admin_keyboard(array: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index in array:
        builder.button(
            text=str(index),
            callback_data=f'admin:{str(index).split(" ")[0].lower()}'
        )

    builder.adjust(2, 1, 1)

    return builder.as_markup()


def generate_all_users_keyboard(users: list, page: int = 1) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    start_index = (page - 1) * 9
    end_index = start_index + 9
    user_buttons = users[start_index:end_index]

    for user in user_buttons:
        callsign = user.get('callsign')
        telegram_id = user.get('telegram_id')
        builder.button(
            text=callsign.capitalize(),
            callback_data=f'user:{telegram_id}-{page}'
        )

    nav_buttons = []
    if page > 1:
        nav_buttons.append(("<<", f'users_page-{page - 1}'))
    if end_index < len(users):
        nav_buttons.append((">>", f'users_page-{page + 1}'))

    for text, callback_data in nav_buttons:
        builder.button(text=text, callback_data=callback_data)

    builder.button(text='В админ меню', callback_data='back:админ')

    rows = [3] * (len(user_buttons) // 3)
    if len(user_buttons) % 3 > 0:
        rows.append(len(user_buttons) % 3)
    if nav_buttons:
        rows.append(len(nav_buttons))
    rows.append(1)

    builder.adjust(*rows)

    return builder.as_markup()


def generate_edit_user_keyboard(telegram_id: int, page: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for index in EDIT_USER_MENU_BUTTONS:
        builder.button(
            text=index,
            callback_data=f'user_edit:{index.split()[1]}:{telegram_id}'
        )

    builder.button(text='Назад к пользователям', callback_data=f'back:users_page-{page}')
    builder.button(text='В админ меню', callback_data='back:админ')

    builder.adjust(3, 2, 1, 1, 1)

    return builder.as_markup()


def generate_back_to_admin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='В админ меню', callback_data=f'back:админ')
    return builder.as_markup()


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


@router.message(Command(commands=['cancel']))
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer(
        text='Выполнение команды прекращено.',
    )


@router.message(Command(commands=['admin']))
@router.callback_query(F.data == 'back:админ')
@is_admin
async def admin_command(interaction: types.Message | types.CallbackQuery) -> None:
    text = 'Админ меню'
    if isinstance(interaction, types.CallbackQuery):
        await interaction.message.edit_text(
            text=text,
            reply_markup=generate_admin_keyboard(ADMIN_MENU_BUTTONS)
        )
    else:
        await interaction.answer(
            text=text,
            reply_markup=generate_admin_keyboard(ADMIN_MENU_BUTTONS)
        )


@router.callback_query(F.data == 'admin:показать')
async def show_events(callback: types.CallbackQuery) -> None:
    await callback.message.edit_text(
        text='Нет добавленных мероприятий',
        reply_markup=generate_back_to_admin_keyboard()
    )


@router.callback_query(F.data == 'admin:заявки')
async def show_surveys(callback: types.CallbackQuery) -> None:
    await callback.message.edit_text(
        text='Новых заявок нет',
        reply_markup=generate_back_to_admin_keyboard()
    )


@router.callback_query(F.data == 'admin:все')
async def show_all_users(callback: types.CallbackQuery) -> None:
    users = await get_all_users()
    if not users:
        await callback.message.edit_text(
            text='Нет сохраненных пользователей чат-бота',
            reply_markup=generate_back_to_admin_keyboard()
        )
        return
    await callback.message.edit_text(
        text='Все пользователи:',
        reply_markup=generate_all_users_keyboard(users=users)
    )


@router.callback_query(F.data.startswith('users_page-'))
async def change_users_page(callback: types.CallbackQuery) -> None:
    page = int(callback.data.split('-')[1])
    users = await get_all_users()

    await callback.message.edit_text(
        text='Все пользователи:',
        reply_markup=generate_all_users_keyboard(users=users, page=page)
    )


@router.callback_query(F.data.startswith('user:'))
async def show_user_info(callback: types.CallbackQuery) -> None:
    parts = callback.data.split('-')
    telegram_id = int(parts[0].split(':')[1])
    page = int(parts[1]) if len(parts) > 1 else 1

    user = await user_get_or_none(telegram_id=telegram_id)
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
        text=f'<b>ФИО</b>: {name}\n'
             f'<b>Позывной</b>: {callsign}\n'
             f'<b>Возраст</b>: {age}\n\n'
             f'<b>О себе</b>: {about}\n\n'
             f'<b>О своем опыте</b>: {experience}\n\n'
             f'<b>Наличие авто</b>: {car}\n'
             f'<b>Членство в команде</b>: {approved}\n'
             f'<b>Освобожден от опросов</b>: {reserved}',
        reply_markup=generate_edit_user_keyboard(telegram_id=telegram_id, page=page),
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

    callsign_taken = await is_callsign_taken(callsign=new_callsign)

    if callsign_taken:
        await message.answer(
            text=f'Позывной <b>{new_callsign.capitalize()}</b> '
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
async def edit_user_car(callback: types.CallbackQuery) -> None:
    pass


@router.callback_query(F.data.startswith('user_edit:бронь'))
async def edit_user_reserved(callback: types.CallbackQuery) -> None:
    pass


@router.callback_query(F.data.startswith('user_edit:пользователя'))
async def delete_user(callback: types.CallbackQuery) -> None:
    pass


@router.callback_query(F.data.startswith('back:users_page-'))
async def back_to_users_page(callback: types.CallbackQuery) -> None:
    page = int(callback.data.split('-')[1])

    users = await get_all_users()

    await callback.message.edit_text(
        text='Все пользователи:',
        reply_markup=generate_all_users_keyboard(users=users, page=page)
    )
