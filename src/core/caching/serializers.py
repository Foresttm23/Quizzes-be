from __future__ import annotations

import json
from typing import Any, Type

from src.core.schemas import Base as BaseSchema


def serialize(obj: Any) -> str:
    """
    Serializes Pydantic models, Lists of models, or raw dicts.
    Handles UUIDs and Datetime automatically.
    """
    if isinstance(obj, BaseSchema):
        return obj.model_dump_json()

    if isinstance(obj, list):
        data_list = [
            item.model_dump(mode="json") if isinstance(item, BaseSchema) else item
            for item in obj
        ]
        return json.dumps(data_list, default=str)

    return json.dumps(obj, default=str)


def deserialize(obj: Any, schema: Type[BaseSchema] | None) -> Any:
    """Deserialize obj into a passed schema."""
    json_data = json.loads(obj)  # Only schemas here, no plain dict or list
    if schema is None:
        return json_data

    if isinstance(json_data, list):
        return [schema.model_validate(item) for item in json_data]
    return schema.model_validate(json_data)
