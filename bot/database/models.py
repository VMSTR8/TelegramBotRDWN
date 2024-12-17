from tortoise.models import Model
from tortoise import fields
from tortoise.validators import MinValueValidator, MaxValueValidator


class User(Model):
    id = fields.IntField(pk=True)
    telegram_id = fields.IntField(unique=True)
    name = fields.CharField(max_length=100, null=True, default=None)
    callsign = fields.CharField(max_length=255, unique=True, null=True, default=None)
    age = fields.DateField(null=True, default=None)
    about = fields.TextField(max_length=1000, null=True, default=None)
    experience = fields.TextField(max_length=1000, null=True, default=None)
    car = fields.BooleanField(null=True, default=None)
    frequency = fields.CharField(max_length=255, null=True, default=None)
    agreement = fields.BooleanField(null=True, default=None)
    approved = fields.BooleanField(null=True, default=None)
    reserved = fields.BooleanField(null=True, default=None)

    class Meta:
        table = "users"


class Event(Model):
    id = fields.IntField(pk=True)
    event_name = fields.CharField(max_length=255)
    organization = fields.CharField(max_length=255)
    price = fields.IntField()
    latitude = fields.FloatField(validators=[
        MinValueValidator(-90),
        MaxValueValidator(90),
    ]
    )
    longitude = fields.FloatField(validators=[
        MinValueValidator(-180),
        MaxValueValidator(180),
    ]
    )
    description = fields.TextField(max_length=3000, null=True)
    datetime_event_start = fields.DatetimeField(null=True)
    datetime_event_end = fields.DatetimeField(null=True)
    expire = fields.DatetimeField()

    class Meta:
        table = "events"


class Poll(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="polls")
    event = fields.ForeignKeyField("models.Event", related_name="polls")
    is_attending = fields.BooleanField()
    reason_not_attending = fields.TextField(null=True)
    can_provide_ride = fields.BooleanField(null=True, default=None)
    car_capacity = fields.IntField(null=True)
    start_location = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "polls"


class RideShare(Model):
    id = fields.IntField(pk=True)
    driver = fields.ForeignKeyField(
        "models.User",
        related_name="rides_as_driver",
        on_delete=fields.CASCADE
    )
    passenger = fields.ForeignKeyField(
        "models.User",
        related_name="rides_as_passenger",
        on_delete=fields.CASCADE
    )
    event = fields.ForeignKeyField(
        "models.Event",
        related_name="ride_shares",
        on_delete=fields.CASCADE
    )

    class Meta:
        table = "ride_shares"
