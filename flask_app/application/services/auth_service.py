from passlib.hash import argon2
from flask_app.application.services.user_service import UserService
from flask_app.domain.entities.user import User, Role
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)


class AuthService:

    def __init__(self, user_service: UserService):
        self.user_service = user_service

    @staticmethod
    def _hash_password(plain_password: str) -> str:
        return argon2.hash(plain_password)

    @staticmethod
    def _verify_password(plain_password: str, hashed_password: str) -> bool:
        return argon2.verify(plain_password, hashed_password)

    @staticmethod
    def _create_tokens(user: User):

        claims = {"role": user.role.value}
        user_id_str = str(user.id)

        access = create_access_token(
            identity=user_id_str,
            additional_claims=claims
        )
        refresh = create_refresh_token(
            identity=user_id_str,
            additional_claims=claims
        )

        return {"access_token": access, "refresh_token": refresh}

    def refresh_access_token(self) -> dict:
        """Issue a new access token; must run inside a refresh JWT request (uses request context)."""
        user_id = get_jwt_identity()
        claims = get_jwt()

        custom_claims = {"role": claims.get("role")}

        new_access_token = create_access_token(
            identity=user_id,
            additional_claims=custom_claims
        )

        return {"access_token": new_access_token}

    def register(self, user_name: str, password: str, role: Role) -> User:
        hashed = self._hash_password(password)

        return self.user_service.create_user(
            user_name=user_name,
            password_hash=hashed,
            role=role
        )

    def login(self, username: str, password: str) -> dict:
        user = self.user_service.get_user_by_username(username)

        if user is None:
            raise ValueError("User does not exist")
        if not self._verify_password(password, user.password_hash):
            raise ValueError("Incorrect password")

        return self._create_tokens(user)

