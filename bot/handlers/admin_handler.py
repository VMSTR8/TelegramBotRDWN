from aiogram import types, Router, F
from aiogram.filters import Command

from utils.decorators import is_admin
from utils.keyboards import (
    generate_all_users_keyboard,
    generate_admin_keyboard,
    generate_back_to_admin_keyboard
)

from handlers.manage_users_handler import router as manage_users_router
from handlers.create_event_handler import router as create_event_router

from database.users_db_manager import (
    get_all_users,
)

router = Router()
router.include_router(manage_users_router)
router.include_router(create_event_router)

ADMIN_MENU_BUTTONS = [
    'Создать мероприятие',
    'Показать мероприятия',
    'Заявки на вступление',
    'Все пользователи'
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
