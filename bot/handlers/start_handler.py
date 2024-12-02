from aiogram import types, Router
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext


router = Router()


# TODO: При нажатии на старт id пользователя сразу попадает в базу
@router.message(CommandStart())
async def start_router(message: types.Message, state: FSMContext) -> None:

    await state.clear()

    user = message.from_user.first_name
    await message.answer(
        text=f'<b>{user}</b>, приветствую тебя в нашем командном чат-боте!\n\n'
             f'Доступные команды\n'
             f'==================\n'
             f'/about_team - все о нашей команде\n'
             f'/join - подать заявку на вступление\n'
             f'/profile - посмотреть свой профиль*\n'
             f'/events - предстоящие мероприятия*\n\n'
             f'<i>* - доступно только для тех, кто уже вступил в наш коллектив</i>',
        parse_mode=ParseMode.HTML,
        reply_markup=ReplyKeyboardRemove()
    )
