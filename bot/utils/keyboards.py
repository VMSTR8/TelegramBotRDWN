from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


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


def generate_edit_user_keyboard(telegram_id: int, page: int, array: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for index in array:
        builder.button(
            text=index,
            callback_data=f'user_edit:{index.split()[1]}:{telegram_id}'
        )

    builder.button(text='Удалить пользователя', callback_data=f'delete_user:{telegram_id}-{page}')
    builder.button(text='Назад к пользователям', callback_data=f'back:users_page-{page}')
    builder.button(text='В админ меню', callback_data='back:админ')

    builder.adjust(3, 2, 1, 1, 1)

    return builder.as_markup()


def generate_delete_user_keyboard(telegram_id: int, page: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text='Да', callback_data=f'confirm_user_deletion:{telegram_id}-{page}')
    builder.button(text='Нет', callback_data=f'user:{telegram_id}-{page}')

    builder.adjust(2)

    return builder.as_markup()


def generate_back_to_admin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='В админ меню', callback_data=f'back:админ')
    return builder.as_markup()
