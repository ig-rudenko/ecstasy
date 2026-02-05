from typing import TypedDict


class RemoteCommandCondition(TypedDict):
    expect: str
    command: str


class RemoteCommand(TypedDict):
    command: str
    conditions: list[RemoteCommandCondition]
