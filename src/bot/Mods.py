from enum import Enum, StrEnum


class BotActionMode(Enum):
    DIALOG = 1
    REACTION = 2


class ActivityMode(StrEnum):
    TYPING = "typing"
    AUDIOMESSAGE = "audiomessage"
    PHOTO = "photo"
    VIDEOMESSAGE = "videomessage"


ACTIVITIES = [mode for mode in ActivityMode]