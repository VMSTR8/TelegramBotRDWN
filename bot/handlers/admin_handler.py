from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup

from utils.decorators import is_admin

router = Router()

admin_menu_buttons = [
    'Создать мероприятие',
    'Показать мероприятия',
    'Заявки на вступление',
    'Все пользователи'
]


def admin_keyboard_generate(array: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index in array:
        builder.button(text=str(index), callback_data=f'admin:{str(index).split(" ")[0].lower()}')

    builder.adjust(2, 1, 1)

    return builder.as_markup()


def back_to_admin_keyboard_generate() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='К админ меню', callback_data=f'back:админ')
    return builder.as_markup()


@router.message(Command(commands=['admin']))
@router.callback_query(F.data == 'back:админ')
@is_admin
async def admin_router(interaction: types.Message | types.CallbackQuery) -> None:
    text = 'Админ меню'
    if isinstance(interaction, types.CallbackQuery):
        await interaction.message.edit_text(
            text=text,
            reply_markup=admin_keyboard_generate(admin_menu_buttons)
        )
    else:
        await interaction.answer(
            text=text,
            reply_markup=admin_keyboard_generate(admin_menu_buttons)
        )


@router.callback_query(F.data == 'admin:показать')
async def event(callback: types.CallbackQuery) -> None:
    await callback.message.edit_text(
        text='Нет добавленных мероприятий',
        reply_markup=back_to_admin_keyboard_generate()
    )


@router.callback_query(F.data == 'admin:заявки')
async def event(callback: types.CallbackQuery) -> None:
    await callback.message.edit_text(
        text='Новых заявок нет',
        reply_markup=back_to_admin_keyboard_generate()
    )


@router.callback_query(F.data == 'admin:все')
async def event(callback: types.CallbackQuery) -> None:
    await callback.message.edit_text(
        text='Нет сохраненных пользователей чат-бота',
        reply_markup=back_to_admin_keyboard_generate()
    )
