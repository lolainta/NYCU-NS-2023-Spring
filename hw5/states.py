from enum import Enum, auto


class ClientState(Enum):
    IDLE = auto()
    SYN_SENT = auto()
    ESTABLISHED = auto()


class ServerState(Enum):
    IDLE = auto()
    SYN_RCVD = auto()
    ESTABLISHED = auto()
