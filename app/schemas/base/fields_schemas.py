from pydantic import BaseModel, Field
from enum import StrEnum, IntEnum
from datetime import datetime, date


#   Key-value field
class FieldTitleValue(BaseModel):
    title: str
    value: str



#   Object description field
class FieldDescription(BaseModel):
    full: str | None = None
    preview: str | None = None



#   Object image information field
class FieldImage(BaseModel):
    main: str | None = None
    preview: str | None = None
    cover: str | None = None
    icon: str | None = None
    emoji: str | None = None



#   Address description field (postal, legal, etc.)
class FieldAddress(BaseModel):
    country: str | None = None
    region: str | None = None
    district: str | None = None
    settlement: str | None = None
    quarter: str | None = None
    street: str | None = None
    postcode: str | None = None
    house: str | None = None
    apartments: str | None = None
    room: str | None = None
    office: str | None = None
    entrance: str | None = None
    floor: str | None = None
    lat: str | None = None
    lon: str | None = None



#   Video conference description field
class FieldVideoConference(BaseModel):
    platform: str | None = None         #   Video communication system
    url: str | None = None              #   Broadcast URL
    conference_id: str | None = None    #   Broadcast ID in the video communication system
    password: str | None = None         #   Access code for the broadcast



#   Action type field
class FieldActionType(StrEnum):
    BUTTON = "button"
    LINK = "link"



#   Action description
class FieldAction(BaseModel):
    url: str
    title: str
    type: FieldActionType



#   Title and description
class FieldTitleDescriptionSimple(BaseModel):
    title: str | None = None
    description: str | None = None



#   Start and end dates of something
class FieldDates(BaseModel):
    start:  datetime | None = None
    finish: datetime | None = None



#   Hints for objects
class FieldHint(BaseModel):
    text: str | None = None                 #   Hint text
    url: str| None = None                   #   Help URL
    action_header: str | None = None        #   Button title or link text
    action: FieldActionType | None = None   #   Action type for getting a detailed hint
    