import re

from datetime import datetime

from aiogram import types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext

from pydantic import BaseModel, field_validator, ValidationError

from utils.text_answers import answers

CANCEL_REMINDER = answers.get('CANCEL_REMINDER')
LATIN_REGEX = r"[^a-zA-Z-]"
CYRILLIC_REGEX = r"[^а-яА-ЯёЁ\s]"


class UserValidator(BaseModel):
    name: str | None = None
    callsign: str | None = None
    age: datetime | None = None

    @field_validator('name', mode='before')
    def validate_name(cls, value):
        if not value or not value.strip():
            raise ValueError('Имя не может быть пустым.')
        if len(value) > 100:
            raise ValueError('Превышен лимит в 100 символов для имени.')
        if not all(word.isalpha() for word in value.split()) or len(value.split()) < 2:
            raise ValueError(
                'Имя должно содержать минимум два слова '
                '(хотя бы Имя и Отчество) и написано кириллицей.'
            )
        if re.search(CYRILLIC_REGEX, value):
            raise ValueError('Имя должно содержать только буквы кириллицы.')
        return value.lower()

    @field_validator('callsign', mode='before')
    def validate_callsign(cls, value):
        if not value or not value.strip():
            raise ValueError('Позывной не может быть пустым.')
        if len(value) > 10:
            raise ValueError('Длина позывного не должна превышать 10 символов.')
        if re.search(LATIN_REGEX, value):
            raise ValueError(
                'Позывной должен быть написан исключительно латинскими буквами, '
                'без символов, цифр и пробелов. '
                'Если позывного еще нет, то просто отправь "-" в чат.'
            )
        return value.lower()

    @field_validator('age', mode='before')
    def validate_age(cls, value):
        if not value or not value.strip():
            raise ValueError('Дата рождения не может быть пустой.')
        if len(value) > 10:
            raise ValueError('Длина сообщения с датой рождения не должна превышать 10 символов.')
        try:
            birth_date = datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            raise ValueError('Неверный формат даты. Укажите дату в формате ДД.ММ.ГГГГ.')
        if birth_date.year < 1900:
            raise ValueError('Дата рождения не может быть ранее 1900 года.')
        return birth_date


async def general_user_validation(message: types.Message, state: FSMContext, **kwargs):
    try:
        validated_input = UserValidator(**kwargs)
    except ValidationError as exc:
        key_with_error = exc.errors()[0]['loc'][0]
        error_message = exc.errors()[0]['msg'].lstrip('Value error, ')
        await state.update_data(**{key_with_error: ''})
        await message.answer(
            text=f'Ошибка: {error_message}\n\n'
                 f'{CANCEL_REMINDER}',
            parse_mode=ParseMode.HTML
        )
        return
    return validated_input
