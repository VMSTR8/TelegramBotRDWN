from aiogram import types, Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

router = Router()


class Event(StatesGroup):
    name = State()
    organization = State()
    price = State()
    coordinates = State()
    description = State()
    datetime_event_start_end = State()
    expire = State()


@router.callback_query(F.data == 'admin:создать')
async def create_event(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Event.name)
    await callback.message.answer(
        text='Введи название мероприятия'
    )


@router.message(Event.name)
async def validate_event_name(message: types.Message, state: FSMContext):
    pass


@router.message(Event.organization)
async def validate_event_organization(message: types.Message, state: FSMContext):
    pass


@router.message(Event.price)
async def validate_event_price(message: types.Message, state: FSMContext):
    pass


@router.message(Event.coordinates)
async def validate_event_coordinates(message: types.Message, state: FSMContext):
    pass


@router.message(Event.description)
async def validate_event_description(message: types.Message, state: FSMContext):
    pass


@router.message(Event.datetime_event_start_end)
async def validate_event_expire(message: types.Message, state: FSMContext):
    pass


@router.message(Event.expire)
async def validate_event_expire(message: types.Message, state: FSMContext):
    pass
