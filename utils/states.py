from enum import Enum


class States(Enum):
    (
        STATE_MOTHER_NAME,
        STATE_BIRTH_DATE,
        STATE_DEATH_DATE,
        STATE_DEATH_CAUSE,
        STATE_RESIDENCE,
        STATE_PHOTO,
        STATE_NOTES,
        STATE_CONFIRM,
        STATE_EDIT,
        STATE_DISPLAY,
        PROCESS_ADMIN_ACTION,
        PROCESS_SEARCH_MARTYR,
        CHECK_MARTYR_EXISTS,
        EDIT_FIELD,
        HANDLE_PENDING_MARTYR_SELECTION,
    ) = range(15)
