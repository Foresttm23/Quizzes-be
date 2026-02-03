from typing import Any, Sequence, Type

from pydantic import BaseModel as BaseSchema


def sanitize[U: BaseSchema, A: BaseSchema](
    data: Any,
    schema: Type[U],
    admin_schema: Type[A] | None = None,
    is_admin: bool = False,
) -> U | A | Sequence[U] | Sequence[A]:
    """
    Every caching method saves the admin model, so it won't be sanitized.
    So only the smaller/user schema should be passed.
    """
    if is_admin and admin_schema is not None:
        return admin_schema.model_validate(data)
    if isinstance(data, Sequence):
        return [schema.model_validate(item) for item in data]
    return schema.model_validate(data)
