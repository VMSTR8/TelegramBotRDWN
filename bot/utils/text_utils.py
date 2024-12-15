from datetime import datetime

from aiogram import types
from aiogram.fsm.context import FSMContext


async def merge_message_parts(
        message: types.Message,
        state: FSMContext,
        key: str,
) -> bool | str:
    data = await state.get_data()
    data_text = data.get(key, '')
    text = message.text
    if len(text) > 4000:
        data_text += f' {text}'
        await state.update_data(**{key: data_text})
        return False

    return f'{data_text} {text}'.strip()


def calculate_age(birth_date: datetime) -> int:
    today = datetime.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age
