from aiogram import types, Router
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from handlers.cancel_handler import cancel_handler

from utils.text_answers import answers
from utils.text_utils import merge_message_parts, calculate_age
from utils.decorators import (
    is_text,
    survey_completion_status,
)

from database.users_db_manager import (
    user_update,
    user_get_or_create,
    is_callsign_taken,
)

from validators.user_validators import general_user_validation

router = Router()

CANCEL_REMINDER = answers.get('CANCEL_REMINDER')


class Form(StatesGroup):
    name = State()
    callsign = State()
    age = State()
    about = State()
    experience = State()
    car = State()
    frequency = State()
    agreement = State()


@router.message(Command(commands=['join']))
@survey_completion_status
async def join_command(message: types.Message, state: FSMContext) -> None:
    await user_get_or_create(telegram_id=message.from_user.id)
    await state.set_state(Form.name)
    await message.answer(
        text='Представься, пожалуйста. Желательно полное ФИО.\n\n'
             '<i>Твои данные никуда не попадут за пределы этого бота.\n'
             'Доступ к данным имеет только командир команды.</i>\n\n'
             f'{CANCEL_REMINDER}',
        parse_mode=ParseMode.HTML,
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(Form.name)
@is_text
async def validate_name(message: types.Message, state: FSMContext) -> None:
    name = await merge_message_parts(message=message, state=state, key='name')

    if not name:
        return

    validated_input = await general_user_validation(message=message, state=state, name=name)

    if not validated_input:
        return

    await state.update_data(name=validated_input.name.lower())
    await state.set_state(Form.callsign)
    await message.answer(
        text='У тебя есть позывной? Если да, напиши какой. '
             'Если нет, то просто поставь прочерк. '
             'После принятия в команду ты сможешь отредактировать свой позывной.\n\n'
             '<i>Позывной пишется на латинице. Так же недопустимы любые символы, '
             'цифры и пробелы в позывном.</i>\n\n'
             f'{CANCEL_REMINDER}',
        parse_mode=ParseMode.HTML
    )


@router.message(Form.callsign)
@is_text
async def validate_callsign(message: types.Message, state: FSMContext) -> None:
    callsign = await merge_message_parts(message=message, state=state, key='callsign')

    if not callsign:
        return

    validated_input = await general_user_validation(message=message, state=state, callsign=callsign)

    if not validated_input:
        return

    not_unique_callsign = await is_callsign_taken(callsign=validated_input.callsign)

    if callsign.lower() == '-':
        user = await user_get_or_create(telegram_id=message.from_user.id)
        validated_input.callsign = f'rd{user.id}'

    if not_unique_callsign:
        await state.update_data(callsign='')
        await message.answer(
            text='Ошибка: К сожалению такой позывной уже занят. '
                 'Придумай себе другой позывной.\n\n'
                 f'{CANCEL_REMINDER}',
        )
        return

    await state.update_data(callsign=validated_input.callsign.lower())
    await state.set_state(Form.age)
    await message.answer(
        text='Напиши свою настоящую дату рождения в формате ДД.ММ.ГГГГ, например:\n\n'
             '<b>01.01.1990</b>\n\n'
             '<i>Учти, мы не принимаем в команду лица младше 21 года.</i>\n\n'
             f'{CANCEL_REMINDER}',
        parse_mode=ParseMode.HTML
    )


@router.message(Form.age)
@is_text
async def validate_age(message: types.Message, state: FSMContext) -> None:
    date = await merge_message_parts(message=message, state=state, key='age')

    if not date:
        return

    validated_input = await general_user_validation(message=message, state=state, age=date)

    if not validated_input:
        return

    validated_input = validated_input.age
    age = calculate_age(birth_date=validated_input)

    if age < 21:
        await state.update_data(age=validated_input)
        data = await state.get_data()
        data['approved'] = False
        await user_update(telegram_id=message.from_user.id, **data)
        await message.answer(
            text='К сожалению мы не можем принять тебя в команду, так как твой возраст меньше 21 года.\n\n'
                 'Попробуй обратиться к нам в будущем, когда тебе исполнится 21 год.'
        )
        await state.clear()
        return

    await state.update_data(age=validated_input)
    await state.set_state(Form.about)
    await message.answer(
        text='Расскажи в паре предложений о себе. Чем занимаешься по жизни, как созрел '
             'заниматься страйкболом и т.д.\n\n'
             '<i>Максимальная длина сообщения в данном пункте - 1000 символов.</i>\n\n'
             f'{CANCEL_REMINDER}',
        parse_mode=ParseMode.HTML
    )


@router.message(Form.about)
@is_text
async def validate_about(message: types.Message, state: FSMContext) -> None:
    about = await merge_message_parts(message=message, state=state, key='about')
    if not about:
        return
    if len(about) > 1000:
        await state.update_data(about='')
        await message.answer(
            text='Слишком длинный текст! Пожалуйста, сократи рассказ о себе до 1000 символов.\n\n'
                 '<i>Попробуй написать более кратко, изложи только самую главную суть.</i>\n\n'
                 f'{CANCEL_REMINDER}',
            parse_mode=ParseMode.HTML
        )
        return

    await state.update_data(about=message.text)
    await state.set_state(Form.experience)
    await message.answer(
        text='А теперь более подробно расскажи нам о своем опыте в страйкболе. Состоял(а) ли ты '
             'до этого в другой команде и если да, то в какой? Сколько в целом уже играешь или '
             'только начинаешь заниматься хобби? Этот пункт даст нам понимание, какой подход подбирать '
             'к желающему присоединиться к коллективу.\n\n'
             '<i>Максимальная длина сообщения в данном пункте - 1000 символов.</i>\n\n'
             f'{CANCEL_REMINDER}',
        parse_mode=ParseMode.HTML
    )


@router.message(Form.experience)
@is_text
async def validate_experience(message: types.Message, state: FSMContext) -> None:
    experience = await merge_message_parts(message=message, state=state, key='experience')
    if not experience:
        return
    if len(experience) > 1000:
        await state.update_data(experience='')
        await message.answer(
            text='Слишком длинный текст! Пожалуйста, сократи рассказ о себе до 1000 символов.\n\n'
                 '<i>Напиши тезисно о своем опыте. Подробности, это, конечно, хорошо, но уж точно '
                 'не стоит НАСТОЛЬКО подробно рассказывать об опыте :)\n\n</i>'
                 f'{CANCEL_REMINDER}',
            parse_mode=ParseMode.HTML
        )
        return

    await state.update_data(experience=message.text)
    await state.set_state(Form.car)
    await message.answer(
        text='Скажи, у тебя есть свой личный автотранспорт?\n\n'
             f'{CANCEL_REMINDER}',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text='Да'),
                    KeyboardButton(text='Нет')
                ]
            ],
            resize_keyboard=True
        )
    )


@router.message(Form.car)
@is_text
async def validate_car(message: types.Message, state: FSMContext) -> None:
    car = await merge_message_parts(message=message, state=state, key='car')
    if not car:
        return

    if car.lower() == 'да':
        car_status = True
    elif car.lower() == 'нет':
        car_status = False
    else:
        await state.update_data(car='')
        await message.answer(
            text='Пожалуйста, нажми на "Да" или "Нет" на вопрос о наличие автомобиля.\n\n'
                 f'{CANCEL_REMINDER}',
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text='Да'),
                        KeyboardButton(text='Нет')
                    ]
                ],
                resize_keyboard=True
            )
        )
        return

    await state.update_data(car=car_status)

    await state.set_state(Form.frequency)
    await message.answer(
        text='Как часто ты готов участвовать в тренировках и играх?\n\n'
             f'{CANCEL_REMINDER}',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text='1 раз в месяц'),
                    KeyboardButton(text='2 раза в месяц')
                ],
                [
                    KeyboardButton(text='3 раза в месяц'),
                    KeyboardButton(text='4 раза в месяц')
                ]
            ],
            resize_keyboard=True
        )
    )


@router.message(Form.frequency)
@is_text
async def validate_frequency(message: types.Message, state: FSMContext) -> None:
    frequency = await merge_message_parts(message=message, state=state, key='frequency')
    if not frequency:
        return

    if frequency.lower() not in [
        '1 раз в месяц',
        '2 раза в месяц',
        '3 раза в месяц',
        '4 раза в месяц'
    ]:
        await state.update_data(frequency='')
        await message.answer(
            text='Пожалуйста, выбери один из вариантов.\n\n'
                 'Как часто ты готов участвовать в тренировках и играх?\n\n'
                 f'{CANCEL_REMINDER}',
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text='1 раз в месяц'),
                        KeyboardButton(text='2 раза в месяц')
                    ],
                    [
                        KeyboardButton(text='3 раза в месяц'),
                        KeyboardButton(text='4 раза в месяц')
                    ]
                ],
                resize_keyboard=True
            )
        )
        return

    await state.update_data(frequency=frequency.lower())

    await state.set_state(Form.agreement)
    # TODO Пункты должны быть динамические. Подтягивать их из базы, вдруг надо будет
    # TODO в будущем их изменять
    await message.answer(
        text='Итак, последний пункт анкеты. Даешь ли ты свое согласие по всем '
             'следующим пунктам:\n\n'
             '1. Обязуюсь посещать минимум 1 мероприятие в месяц\n'
             '2. Понимаю, что за систематические пропуски без уважительной '
             'причины меня исключат из команды БЕЗ права возврата\n'
             '3. Обязуюсь проходить все командные опросы о возможности/невозможности '
             'посетить мероприятие (опросы публикует этот же бот)\n'
             '4. Короче бла бла бла, дописать пункты тут\n\n'
             f'{CANCEL_REMINDER}',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text='Даю согласие'),
                    KeyboardButton(text='Не даю согласие')
                ]
            ],
            resize_keyboard=True
        )
    )


@router.message(Form.agreement)
@is_text
async def validate_agreement(message: types.Message, state: FSMContext) -> None:
    agreement = await merge_message_parts(message=message, state=state, key='agreement')
    if not agreement:
        return
    valid_response = {
        'даю согласие': True,
        'не даю согласие': False
    }

    if agreement.lower() not in valid_response:
        await state.update_data(agreement='')
        await message.answer(
            text='Нужно выбрать один из вариантов ответа.\n\n'
                 f'{CANCEL_REMINDER}',
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text='Даю согласие'),
                        KeyboardButton(text='Не даю согласие')
                    ]
                ],
                resize_keyboard=True
            )
        )
        return

    agreement_status = valid_response.get(agreement.lower())

    if not agreement_status:
        await cancel_handler(message=message, state=state)
        await message.answer(
            text='Без согласия с вышеуказанными пунктам, увы, вступить '
                 'в нашу команду не получится.'
        )
        await state.clear()
        return

    await state.update_data(agreement=agreement_status)
    data = await state.get_data()
    await user_update(telegram_id=message.from_user.id, **data)
    await message.answer(
        text='Опрос пройден! Спасибо!',
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()
