from __future__ import annotations

import json
from typing import Any, Type

from pydantic import TypeAdapter
from pydantic_core import to_jsonable_python

from src.core.schemas import Base as BaseSchema


def serialize(obj: Any) -> str:
    return json.dumps(to_jsonable_python(obj))


def deserialize[S: BaseSchema](obj: str, response_schema: Type[S] | None) -> S | Any:
    if not obj:
        return None

    data = json.loads(obj)
    if response_schema is None:
        return data

    # Use TypeAdapter to handle both single models and lists of models automatically
    return TypeAdapter(S | list[S]).validate_python(data)
