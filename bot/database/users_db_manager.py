from typing import Any

from database.models import User


async def user_get_or_create(telegram_id: int) -> User:
    user, created = await User.get_or_create(telegram_id=telegram_id)
    return user


async def user_get_or_none(telegram_id: int) -> User | None:
    user = await User.get_or_none(telegram_id=telegram_id)
    return user


async def user_update(telegram_id: int, **kwargs) -> User:
    user = await User.filter(telegram_id=telegram_id).first()
    if not user:
        raise ValueError(
            f'User with {telegram_id} does not exist.'
        )

    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)

    await user.save()

    return user


async def user_delete(telegram_id: int) -> None:
    user = await User.filter(telegram_id=telegram_id).first()
    if not user:
        raise ValueError(
            f'User with {telegram_id} does not exist.'
        )
    await user.delete()


async def is_callsign_taken(callsign: str) -> bool:
    return await User.filter(callsign=callsign).exists()


async def get_all_users() -> list[dict[str, Any]]:
    users = await User.all()
    sorted_users = sorted(
        [
            {
                'telegram_id': user.telegram_id,
                'name': user.name,
                'callsign': user.callsign
            }
            for user in users
            if user.name and user.callsign
        ],
        key=lambda user: user['callsign'],
    )
    return sorted_users
