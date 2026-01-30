from typing import Any, Sequence, Type, TypeVar

from pydantic import BaseModel as BaseSchema

UserSchema = TypeVar("UserSchema", bound=BaseSchema)
AdminSchema = TypeVar("AdminSchema", bound=BaseSchema)


def sanitize(
    data: Any,
    schema: Type[UserSchema],
    admin_schema: Type[AdminSchema] | None = None,
    is_admin: bool = False,
) -> UserSchema | AdminSchema | Sequence[UserSchema] | Sequence[AdminSchema]:
    """
    Every caching method saves the admin model, so it won't be sanitized.
    So only the smaller/user schema should be passed.
    """
    if is_admin and admin_schema is not None:
        return admin_schema.model_validate(data)
    if isinstance(data, Sequence):
        return [schema.model_validate(item) for item in data]
    return schema.model_validate(data)
