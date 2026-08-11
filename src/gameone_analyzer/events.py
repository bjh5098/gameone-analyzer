from enum import Enum, auto


class EventType(Enum):
    HIT_SINGLE = auto()
    HIT_DOUBLE = auto()
    HIT_TRIPLE = auto()
    HOME_RUN = auto()
    WALK = auto()
    INTENTIONAL_WALK = auto()
    HBP = auto()
    STRIKEOUT = auto()
    GROUNDOUT = auto()
    FLYOUT = auto()
    LINEOUT = auto()
    DOUBLE_PLAY = auto()
    SAC_FLY = auto()
    SAC_BUNT = auto()
    FIELDERS_CHOICE = auto()
    ERROR = auto()
    STOLEN_BASE = auto()
    CAUGHT_STEALING = auto()
    RUNNER_OUT = auto()
    WILD_PITCH = auto()
    BALK = auto()
    CATCHER_INTERFERENCE = auto()
    PASSED_BALL = auto()
    NOT_A_PLATE_APPEARANCE = auto()
    UNKNOWN = auto()


OUT_EVENTS = {
    EventType.STRIKEOUT,
    EventType.GROUNDOUT,
    EventType.FLYOUT,
    EventType.LINEOUT,
    EventType.DOUBLE_PLAY,
    EventType.SAC_FLY,
    EventType.SAC_BUNT,
    EventType.FIELDERS_CHOICE,
    EventType.CAUGHT_STEALING,
    EventType.RUNNER_OUT,
}

EXACT_CODE_TABLE = {
    "4구": EventType.WALK,
    "고의4구": EventType.INTENTIONAL_WALK,
    "사구": EventType.HBP,
    "삼진": EventType.STRIKEOUT,
    "낫아웃-": EventType.STRIKEOUT,
    "낫아웃+": EventType.STRIKEOUT,
    "병살": EventType.DOUBLE_PLAY,
    "유땅병살": EventType.DOUBLE_PLAY,
    "희타": EventType.SAC_BUNT,
    "희비": EventType.SAC_BUNT,
    "투야선": EventType.FIELDERS_CHOICE,
    "3야선": EventType.FIELDERS_CHOICE,
    "실책": EventType.ERROR,
    "송구실책": EventType.ERROR,
    "도루": EventType.STOLEN_BASE,
    "도루자": EventType.CAUGHT_STEALING,
    "주자아웃": EventType.RUNNER_OUT,
    "견제사": EventType.RUNNER_OUT,
    "런다운": EventType.RUNNER_OUT,
    "폭투": EventType.WILD_PITCH,
    "보크": EventType.BALK,
    "포일": EventType.PASSED_BALL,
    "타격방해": EventType.CATCHER_INTERFERENCE,
    "대주자": EventType.NOT_A_PLATE_APPEARANCE,
    "대수비": EventType.NOT_A_PLATE_APPEARANCE,
}

HOME_RUN_SUFFIXES = ("홈",)
TRIPLE_SUFFIXES = ("3",)
DOUBLE_SUFFIXES = ("2",)
SINGLE_SUFFIXES = ("안",)
GROUND_OUT_SUFFIX = "땅"
FIELDERS_CHOICE_SUFFIX = "땅R"
FLY_OUT_SUFFIX = "플"
SAC_FLY_INFIX = "희플"
LINE_OUT_SUFFIX = "직"
ERROR_SUFFIX = "실"


def parse_cell(cell_text: str) -> list:
    if not cell_text:
        return []
    return [part.strip() for part in cell_text.split(",") if part.strip()]


def classify(code: str) -> EventType:
    if code in EXACT_CODE_TABLE:
        return EXACT_CODE_TABLE[code]
    if code.endswith(SAC_FLY_INFIX) or code == "유희플":
        return EventType.SAC_FLY
    if code.endswith(FIELDERS_CHOICE_SUFFIX):
        return EventType.FIELDERS_CHOICE
    if code.endswith(HOME_RUN_SUFFIXES):
        return EventType.HOME_RUN
    if code.endswith(TRIPLE_SUFFIXES) and not code.endswith(FIELDERS_CHOICE_SUFFIX):
        return EventType.HIT_TRIPLE
    if code.endswith(DOUBLE_SUFFIXES) and not code.endswith(FIELDERS_CHOICE_SUFFIX):
        return EventType.HIT_DOUBLE
    if code.endswith(SINGLE_SUFFIXES):
        return EventType.HIT_SINGLE
    if code.endswith(LINE_OUT_SUFFIX):
        return EventType.LINEOUT
    if code.endswith(FLY_OUT_SUFFIX):
        return EventType.FLYOUT
    if code.endswith(GROUND_OUT_SUFFIX):
        return EventType.GROUNDOUT
    if code.endswith(ERROR_SUFFIX) and code != "실책":
        return EventType.ERROR
    return EventType.UNKNOWN


def is_out(event_type: EventType) -> bool:
    return event_type in OUT_EVENTS
