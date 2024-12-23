from aiogram import types, Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode

from utils.decorators import is_text
from utils.text_answers import answers
from utils.text_utils import merge_message_parts
from validators.events_validators import general_event_validation
# from bot.utils.text_utils import merge_message_parts

router = Router()

CANCEL_REMINDER = answers.get('CANCEL_REMINDER')


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
    #TODO добавить запись в БД
    await state.set_state(Event.name)
    await callback.message.answer(
        text='Напиши название мероприятия\n\n'
             f'{CANCEL_REMINDER}',
        parse_mode=ParseMode.HTML
    )


@router.message(Event.name)
@is_text
async def validate_event_name(message: types.Message, state: FSMContext):
    event_name = await merge_message_parts(message=message, state=state, key='name')
    if not event_name:
        return

    validated_input = await general_event_validation(message=message, state=state, name=event_name)
    if not validated_input:
        return

    await state.update_data(name=validated_input.name)
    await state.set_state(Event.organization)
    await message.answer(
        text='Напиши кто организатор мероприятия'
             f'{CANCEL_REMINDER}',
        parse_mode=ParseMode.HTML
    )


@router.message(Event.organization)
async def validate_event_organization(message: types.Message, state: FSMContext):
    event_organization = await merge_message_parts(message=message, state=state, key='organization')
    if not event_organization:
        return

    validated_input = await general_event_validation(message=message, state=state, organization=event_organization)
    if not validated_input:
        return

    await state.update_data(organization=validated_input.organization)
    await state.set_state(Event.price)
    await message.answer(
        text='Укажи стоимость мероприятия'
             f'{CANCEL_REMINDER}',
        parse_mode=ParseMode.HTML
    )


@router.message(Event.price)
async def validate_event_price(message: types.Message, state: FSMContext):
    input_price = await merge_message_parts(message=message, state=state, key='price')
    if not input_price:
        return

    validated_input = await general_event_validation(message=message, state=state, price=input_price)
    if not validated_input:
        return

    validated_input = validated_input.price
    event_price = int(validated_input)

    await state.update_data(price=event_price)
    await state.set_state(Event.coordinates)
    await message.answer(
        text='Введи широту и доглготу через запятую.\n\n'
             'Например: 98.63672, 95.37739\n\n'
             'Допустим ввод широты в диапазоне от -90 до 90, и долготы в диапазоне от -180 до 180\n\n'
             f'{CANCEL_REMINDER}',
        parse_mode=ParseMode.HTML
    )


@router.message(Event.coordinates)
async def validate_event_coordinates(message: types.Message, state: FSMContext):
    # input_coordinates = await merge_message_parts(message=message, state=state, key='coordinates')
    input_coordinates = (98.123123, 120.456123)
    if not input_coordinates:
        return

    # TODO добавить парсинг строки в список

    validated_input = await general_event_validation(message=message, state=state, coordinates=input_coordinates)
    if not validated_input:
        return

    await state.update_data(coordinates=validated_input.coordinates)
    await state.set_state(Event.description)
    await message.answer(
        text='Добавь описание мероприятия\n\n'
             '<i>Максимальная длина сообщения в данном пункте - 3000 символов.</i>\n\n'
             f'{CANCEL_REMINDER}',
        parse_mode=ParseMode.HTML
    )


@router.message(Event.description)
async def validate_event_description(message: types.Message, state: FSMContext):
    input_description = await merge_message_parts(message=message, state=state, key='description')
    if not input_description:
        return

    validated_input = await general_event_validation(message=message, state=state, description=input_description)
    if not validated_input:
        return

    await state.update_data(description=validated_input.description)
    await state.set_state(Event.datetime_event_start_end)
    await message.answer(
        text='Укажи дату и время начала и окончания мероприятия\n\n'
             'Дату и время вводить в формате "ДД.ММ.ГГГГ ЧЧ:ММ", через запятую\n\n'
             'Например: 10.12.2024 09:00, 10.12.2024 19:00\n\n'
             f'{CANCEL_REMINDER}',
        parse_mode=ParseMode.HTML
    )

@router.message(Event.datetime_event_start_end)
async def datetime_event_start_end(message: types.Message, state: FSMContext):
    # input_expire = await merge_message_parts(message=message, state=state, key='datetime_event_start_end')
    #TODO прикрутить парсер input_expire
    if not input_datetime_event_start_end:
        return

    validated_input = await general_event_validation(message=message, state=state, expire=input_datetime_event_start_end)
    if not validated_input:
        return

    await state.update_data(expire=validated_input.expire)
    await state.set_state(Event.expire)
    await message.answer(
        text='Укажи дату и время окончания опроса\n\n'
             'Дату и время вводить в формате "ДД.ММ.ГГГГ ЧЧ:ММ"\n\n'
             'Например: 10.01.2025 18:00\n\n'
             f'{CANCEL_REMINDER}',
        parse_mode=ParseMode.HTML
    )

@router.message(Event.expire)
async def validate_event_expire(message: types.Message, state: FSMContext):
    # TODO
    pass
