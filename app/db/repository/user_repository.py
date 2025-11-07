from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PasswordReuseException
from app.db.models.user_model import User as UserModel
from app.schemas.user_schemas.user_request_schema import UserPasswordUpdateRequest
from app.utils.password_utils import hash_password, verify_password
from .base_repository import BaseRepository


class UserRepository(BaseRepository[UserModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=UserModel, db=db)

    @staticmethod
    def apply_password_updates(instance: UserModel, new_password_info: UserPasswordUpdateRequest) -> bool:
        """
        Helper function for updating password and keeping track of changes.
        Takes user and new_password_info.
        """
        current_password = new_password_info.current_password.get_secret_value()
        new_password = new_password_info.new_password.get_secret_value()

        # As long as current and new are the same, we raise exception.
        if current_password == new_password:
            raise PasswordReuseException()

        if not verify_password(current_password, instance.hashed_password):
            return False

        instance.hashed_password = hash_password(new_password)
        return True
