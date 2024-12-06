from datetime import datetime

from aiogram import types, Router, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup

from utils.decorators import is_admin
from database.users_db_manager import get_all_users, user_get_or_none

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
    'Ред. бронь'
]


def admin_keyboard_generate(array: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index in array:
        builder.button(
            text=str(index),
            callback_data=f'admin:{str(index).split(" ")[0].lower()}'
        )

    builder.adjust(2, 1, 1)

    return builder.as_markup()


def all_users_keyboard_generate(users: list, page: int = 1) -> InlineKeyboardMarkup:
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


def edit_users_keyboard_generate(telegram_id: int, page: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for index in EDIT_USER_MENU_BUTTONS:
        builder.button(
            text=index,
            callback_data=f'user_edit:{index.split()[1]}:{telegram_id}'
        )

    builder.button(text='Назад к пользователям', callback_data=f'back:users_page-{page}')
    builder.button(text='В админ меню', callback_data='back:админ')

    builder.adjust(3, 2, 1, 1)

    return builder.as_markup()


def back_to_admin_keyboard_generate() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='В админ меню', callback_data=f'back:админ')
    return builder.as_markup()


@router.message(Command(commands=['admin']))
@router.callback_query(F.data == 'back:админ')
@is_admin
async def admin_command(interaction: types.Message | types.CallbackQuery) -> None:
    text = 'Админ меню'
    if isinstance(interaction, types.CallbackQuery):
        await interaction.message.edit_text(
            text=text,
            reply_markup=admin_keyboard_generate(ADMIN_MENU_BUTTONS)
        )
    else:
        await interaction.answer(
            text=text,
            reply_markup=admin_keyboard_generate(ADMIN_MENU_BUTTONS)
        )


@router.callback_query(F.data == 'admin:показать')
async def show_events(callback: types.CallbackQuery) -> None:
    await callback.message.edit_text(
        text='Нет добавленных мероприятий',
        reply_markup=back_to_admin_keyboard_generate()
    )


@router.callback_query(F.data == 'admin:заявки')
async def show_surveys(callback: types.CallbackQuery) -> None:
    await callback.message.edit_text(
        text='Новых заявок нет',
        reply_markup=back_to_admin_keyboard_generate()
    )


@router.callback_query(F.data == 'admin:все')
async def show_all_users(callback: types.CallbackQuery) -> None:
    users = await get_all_users()
    if not users:
        await callback.message.edit_text(
            text='Нет сохраненных пользователей чат-бота',
            reply_markup=back_to_admin_keyboard_generate()
        )
        return
    await callback.message.edit_text(
        text='Все пользователи:',
        reply_markup=all_users_keyboard_generate(users=users)
    )


@router.callback_query(F.data.startswith('users_page-'))
async def change_users_page(callback: types.CallbackQuery) -> None:
    page = int(callback.data.split('-')[1])
    users = await get_all_users()

    await callback.message.edit_text(
        text='Все пользователи:',
        reply_markup=all_users_keyboard_generate(users=users, page=page)
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
        reply_markup=edit_users_keyboard_generate(telegram_id=telegram_id, page=page),
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data.startswith('user_edit:имя'))
async def edit_user_name(callback: types.CallbackQuery) -> None:
    pass


@router.callback_query(F.data.startswith('user_edit:позывной'))
async def edit_user_callsign(callback: types.CallbackQuery) -> None:
    pass


@router.callback_query(F.data.startswith('user_edit:возраст'))
async def edit_user_callsign(callback: types.CallbackQuery) -> None:
    pass


@router.callback_query(F.data.startswith('user_edit:авто'))
async def edit_user_callsign(callback: types.CallbackQuery) -> None:
    pass


@router.callback_query(F.data.startswith('user_edit:бронь'))
async def edit_user_callsign(callback: types.CallbackQuery) -> None:
    pass


@router.callback_query(F.data.startswith('back:users_page-'))
async def back_to_users_page(callback: types.CallbackQuery) -> None:
    page = int(callback.data.split('-')[1])

    users = await get_all_users()

    await callback.message.edit_text(
        text='Все пользователи:',
        reply_markup=all_users_keyboard_generate(users=users, page=page)
    )
