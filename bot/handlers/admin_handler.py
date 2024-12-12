from datetime import datetime

from aiogram import types, Router, F
from aiogram.enums import ParseMode
from aiogram.filters import Command

from utils.decorators import is_admin
from utils.keyboards import (
    generate_edit_user_keyboard,
    generate_all_users_keyboard,
    generate_admin_keyboard,
    generate_back_to_admin_keyboard
)

from handlers.user_edit_handler import router as user_edit_router

from database.users_db_manager import (
    get_all_users,
    user_get_or_none,
)

router = Router()
router.include_router(user_edit_router)

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
        text='Все пользователи',
        reply_markup=generate_all_users_keyboard(users=users)
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
