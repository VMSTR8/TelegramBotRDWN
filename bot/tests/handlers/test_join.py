import pytest

from aiogram.types import ReplyKeyboardRemove

from unittest.mock import patch

from handlers.join_handler import (
    Form,
    join_handler,
    validate_name
)

from utils.text_answers import answers

CANCEL_REMINDER = answers.get('CANCEL_REMINDER')


@pytest.mark.asyncio
async def test_join_handler(message, state):
    await join_handler(message, state)

    state.set_state.assert_called_once_with(Form.name)

    message.answer.assert_called_once()
    send_message = message.answer.call_args[1]

    assert "Представься, пожалуйста" in send_message["text"]
    assert "Твои данные никуда не попадут" in send_message["text"]
    assert send_message["parse_mode"] == "HTML"
    assert isinstance(send_message["reply_markup"], ReplyKeyboardRemove)


@pytest.mark.asyncio
async def test_validate_name_empty_message(message, state_name):
    # Эмулируем случай, когда текст сообщения пустой
    message.text = ''  # Пустое сообщение

    with patch(
            'handlers.join_handler.merge_message_parts',
            return_value='dummy'
    ) as mock_merge:
        await validate_name(message, state_name)

        # Проверяем, что merge_message_parts не вызывается
        mock_merge.assert_not_called()

        # Проверяем, что message.answer вызывается с предупреждением
        message.answer.assert_called_once_with(
            text='Неправильный тип данных. Необходимо отправить '
                 'текстовое сообщение (или нажать на одну из кнопок, '
                 'если они есть).\n\n'
                 f'{CANCEL_REMINDER}'
        )

        # Проверяем, что состояние не обновляется
        state_name.update_data.assert_not_called()


@pytest.mark.asyncio
async def test_validate_name_valid(message, state_name):
    message.text = 'John Doe'

    await validate_name(message, state_name)

    state_name.update_data.assert_called_once_with(name='John Doe')


@pytest.mark.asyncio
async def test_validate_name_long_message(message, state_name):
    # Эмулируем сообщение с длиной > 100 символов
    message.text = 'A' * 101  # Длинное сообщение

    with patch(
            'handlers.join_handler.merge_message_parts',
            return_value='A' * 101
    ) as mock_merge:
        await validate_name(message, state_name)

        # Проверяем, что merge_message_parts вызывается
        mock_merge.assert_called_once_with(message=message, state=state_name, key='name')

        # Проверяем, что состояние сбрасывается
        state_name.update_data.assert_called_once_with(name='')

        # Проверяем, что отправлено сообщение об ошибке
        message.answer.assert_called_once_with(
            text='Превышен лимит в 100 символов. Напиши свои ФИО заново.\n\n'
                 f'{CANCEL_REMINDER}',
            parse_mode='HTML'
        )


@pytest.mark.asyncio
async def test_validate_name_very_long_message(message, state_name):
    # Эмулируем сообщение с длиной > 4000 символов
    long_text = 'A' * 4001
    message.text = long_text

    with patch(
            'handlers.join_handler.merge_message_parts',
            return_value=False
    ) as mock_merge:
        await validate_name(message, state_name)

        # Проверяем, что merge_message_parts вызывается
        mock_merge.assert_called_once_with(message=message, state=state_name, key='name')

        # Проверяем, что состояние не обновляется
        state_name.update_data.assert_not_called()

        # Убедимся, что сообщение об ошибке не отправляется
        message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_validate_name_non_text_message(message, state_name):
    # Эмулируем случай, когда сообщение не содержит текста (например, стикер)
    message.text = None  # Устанавливаем текст в None

    with patch(
            'handlers.join_handler.merge_message_parts',
            return_value='dummy'
    ) as mock_merge:
        await validate_name(message, state_name)

        # Проверяем, что merge_message_parts не вызывается
        mock_merge.assert_not_called()

        # Проверяем, что message.answer вызывается с предупреждением
        message.answer.assert_called_once_with(
            text='Неправильный тип данных. Необходимо отправить '
                 'текстовое сообщение (или нажать на одну из кнопок, '
                 'если они есть).\n\n'
                 f'{CANCEL_REMINDER}'
        )

        # Убедимся, что состояние не обновляется
        state_name.update_data.assert_not_called()
