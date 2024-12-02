import pytest
from aiogram import types
from unittest.mock import AsyncMock


@pytest.fixture
def message():
    msg = AsyncMock(spec=types.Message)
    msg.text = '/join'
    msg.from_user = AsyncMock(id=1234567890)
    msg.answer = AsyncMock()
    return msg


@pytest.fixture
def state():
    return AsyncMock()


@pytest.fixture
def state_name():
    state = AsyncMock()
    state.get_data.return_value = {'name': ''}
    return state
