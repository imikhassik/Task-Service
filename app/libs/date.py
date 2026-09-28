from enum import StrEnum, IntEnum
from datetime import datetime, timedelta, timezone
from pydantic import BeforeValidator
from typing_extensions import Annotated
from pydantic_core import core_schema

__version__ = "1.1.0"

#   Base date config class
class DateSettings:
    #   String values of date-time format
    class Format(StrEnum):
        DATE    = "%Y-%m-%d"
        DEFAULT = "%Y-%m-%d %H:%M:%S %z"

    #   Integer configuration (for example, timezone)
    class Timezone(IntEnum):
        DEFAULT = 3  # UTC+3 (Moscow)


#   Date transformation from Unix-time to usual representation
def make_date(unix_timestamp, format = None, tzone = None):
    f = format if format else DateSettings.Format.DEFAULT

    # Transform timestamp to datetime object
    dt = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)

    # Transform into required timezone. Moscow timezone is default
    tz = DateSettings.Timezone.DEFAULT if not tzone else int(tzone)
    target_tz = timezone(timedelta(hours=tz))
    converted_dt = dt.astimezone(target_tz)

    # Format date to required format
    return converted_dt.strftime(f)


# Transforms input value into ISO-string datetime with timezone.
# Input parameters:
#   value: datetime | str | None - value to transform
# Output parameters:
#   str | None - datetime ISO-string with timezone or None
def parse_datetime(value: datetime | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        # Transform to UTC or back to ISO-string
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, str):
        try:
            # Parse string into datetime and tranform to UTC
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return dt.astimezone(timezone.utc).isoformat()
        except ValueError:
            return None
    return None


#   Parsing processor for datetime string with timezone
def parse_datetime_with_timezone(value) -> datetime:
    if isinstance(value, str):
        # Parse from string of our format
        return datetime.strptime(value, DateSettings.Format.DEFAULT)
    elif isinstance(value, (int, float)):
        # Parse from timestamp
        return datetime.fromtimestamp(value, tz=timezone.utc)
    elif isinstance(value, datetime):
        # Already a datetime object
        return value
    else:
        raise ValueError(f"Unsupported type for datetime parsing: {type(value)}")


#   Datetime serialization function
def serialize_datetime(dt: datetime) -> str:
    return dt.strftime(DateSettings.Format.DEFAULT)


#   Look for midnight n days more/less than specified
def get_midnight(date_str, days):
    #   Добавляем нужное число дней
    day_delta = date_str + timedelta(days=days)

    #   Set time to midnight
    midnight = day_delta.replace(hour=0, minute=0, second=0, microsecond=0)

    return midnight.strftime("%Y-%m-%d %H:%M:%S")


# Function to compare full timestamp (date+time)
def compare_datetimes(dt1, dt2):
    result = 0
    if isinstance(dt1, str):
        dt1 = datetime.fromisoformat(dt1)  # Parse ISO timestamp
    if isinstance(dt2, str):
        dt2 = datetime.fromisoformat(dt2)  # Same for the second argument

    # Transform both objecdts to UTC
    dt1_utc = dt1.astimezone(timezone.utc)
    dt2_utc = dt2.astimezone(timezone.utc)

    if dt1_utc < dt2_utc:
        result = -1
    elif dt1_utc > dt2_utc:
        result = 1
    return result


# Custom date and time type with correct validation and serialization
class DatetimeWithTimezoneType:
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):

        def validate_value(value: any, handler: core_schema.ValidatorFunctionWrapHandler) -> datetime:
            # If already datetime -- pass
            if isinstance(value, datetime):
                return value
            # If string or number -- parse
            return parse_datetime_with_timezone(value)

        def serialize_value(value: datetime) -> str:
            return serialize_datetime(value)

        return core_schema.general_after_validator_function(
            validate_value,
            core_schema.union_schema([
                core_schema.datetime_schema(),
                core_schema.str_schema(),
                core_schema.int_schema(),
                core_schema.float_schema()
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize_value,
                info_arg=False,
                return_schema=core_schema.str_schema()
            )
        )


DatetimeWithTimezone = Annotated[
    datetime,
    DatetimeWithTimezoneType
]
