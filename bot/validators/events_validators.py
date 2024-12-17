from datetime import datetime

from pydantic import BaseModel, field_validator, ValidationError


class EventValidator(BaseModel):
    name: str | None = None
    organization: str | None = None
    price: int | None = None
    coordinates: tuple[float, float] | None = None
    description: str | None = None
    datetime_event_start_end: tuple[datetime, datetime] | None = None
    expire: datetime | None = None

    @field_validator("name", mode='before')
    def validate_name(cls, value):
        if not value or value.strip():
            raise ValueError('Название мероприятия не может быть пустым')
        if len(value) > 255:
            raise ValueError('Превышен лимит в 255 символов для названия мероприятия')
        return value.lower()

    @field_validator("organization", mode='before')
    def validate_organization(cls, value):
        if not value or value.strip():
            raise ValueError('Имя организатора мероприятия не может быть пустым')
        if len(value) > 255:
            raise ValueError(
                'Превышен лимит в 255 символов при добавлении '
                'имени организатора'
            )
        return value.lower()

    @field_validator("price", mode='before')
    def validate_price(cls, value):
        if not value or value.strip():
            raise ValueError('Значение цены не может быть пустым')
        if not value.isnumeric():
            raise ValueError('Цена должна быть целым и не отрицательным числом')
        return value

    @field_validator("coordinates", mode='before')
    def validate_coordinates(cls, value):
        if not value:
            raise ValueError('Значение координат не может быть пустым')
        latitude, longitude = value
        if -90 <= latitude <= 90 and -180 <= longitude <= 180:
            raise ValueError(
                'Широта не может меньше -90.0 и больше 90.0, а долгота не '
                'может быть меньше -180.0 и больше 180.0'
            )
        return latitude, longitude

    @field_validator("description", mode='before')
    def validate_description(cls, value):
        if not value or value.strip():
            raise ValueError('Описание мероприятия не может быть пустым')
        if len(value) > 3000:
            raise ValueError('Превышен лимит в 3000 символов для описания мероприятия')
        return value

    @field_validator("datetime_event_start_end", mode='before')
    def validate_datetime_event_start_end(cls, value):
        if not value:
            raise ValueError(
                'Значение старта и окончания даты и времени мероприятия '
                'не может быть пустым'
            )
        start, end = value
        try:
            start = datetime.strptime(start, '%d.%m.%Y %H:%M')
            end = datetime.strptime(end, '%d.%m.%Y %H:%M')
        except ValueError:
            raise ValueError(
                'Передан неверный формат даты. Проверь правильность '
                'заполнения, даты старта и окончания мероприятия. '
                'Обязательно укажи часы и минуты. Пример:\n\n'
                '01.01.1990 12:00, 01.01.1990 19:00'
            )
        if datetime.now() > start:
            raise ValueError(
                'Дата и время старта мероприятия не могут быть раньше '
                'текущего времени'
            )
        if datetime.now() > end:
            raise ValueError(
                'Дата и время окончания мероприятия не могут быть раньше'
                'текущего времени'
            )
        if end < start:
            raise ValueError(
                'Дата и время окончания мероприятия не могут быть раньше '
                'времени и даты старта мероприятия'
            )
        return start, end

    @field_validator("expire", mode='before')
    def validate_expire(cls, value):
        if not value:
            raise ValueError('Значение окончания времени опроса не может быть пустым')
        try:
            value = datetime.strptime(value, '%d.%m.%Y %H:%M')
        except ValueError:
            raise ValueError('Неверный формат даты и времени окончания опроса. '
                             'Заполни графу правильно. Пример:\n\n'
                             '01.01.1990 18:00')
        if datetime.now() > value:
            raise ValueError('Нельзя устанавливать прошедшие дату и время.')
        return value
