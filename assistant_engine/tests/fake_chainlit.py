from __future__ import annotations

import types
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class Message:
    author: str
    content: str
    id: str = field(default_factory=lambda: str(uuid4()))

    async def send(self) -> None:
        pass

    async def update(self) -> None:
        pass


@dataclass
class Step:
    name: str | None = None
    type: str | None = None
    parent_id: str | None = None
    show_input: bool | str | None = None
    start: str | None = None
    end: str | None = None
    input: Any | None = None
    output: Any | None = None
    id: str = field(default_factory=lambda: str(uuid4()))

    async def send(self) -> None:
        pass

    async def update(self) -> None:
        pass


class Context:
    def __init__(self, current_step_id: str = "parent") -> None:
        self.current_step = types.SimpleNamespace(id=current_step_id)
