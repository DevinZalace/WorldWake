"""Pydantic schemas for authentication requests and safe responses."""

from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    SecretStr,
    field_validator,
)

from worldwake.auth.identities import (
    prepare_email,
    prepare_username,
)
from worldwake.auth.passwords import (
    MAX_PASSWORD_LENGTH,
    validate_password,
)


class AuthenticationRequest(BaseModel):
    """Shared configuration for authentication request bodies."""

    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
    )


class RegisterRequest(AuthenticationRequest):
    """Data required to create a WorldWake account."""

    username: str
    email: str
    password: SecretStr

    @field_validator("username")
    @classmethod
    def prepare_username_value(cls, value: str) -> str:
        """Validate and clean the submitted username."""

        return prepare_username(value).value

    @field_validator("email")
    @classmethod
    def prepare_email_value(cls, value: str) -> str:
        """Validate and normalize the submitted email."""

        return prepare_email(value).value

    @field_validator("password")
    @classmethod
    def validate_new_password(
        cls,
        value: SecretStr,
    ) -> SecretStr:
        """Enforce the password policy for a new account."""

        validate_password(value.get_secret_value())

        return value


class LoginRequest(AuthenticationRequest):
    """Credentials submitted when signing into WorldWake."""

    identifier: str
    password: SecretStr

    @field_validator("identifier")
    @classmethod
    def prepare_identifier(cls, value: str) -> str:
        """Clean a submitted username-or-email identifier."""

        cleaned_identifier = value.strip()

        if not cleaned_identifier:
            raise ValueError(
                "Enter your username or email."
            )

        if len(cleaned_identifier) > 320:
            raise ValueError(
                "Username or email is too long."
            )

        return cleaned_identifier

    @field_validator("password")
    @classmethod
    def validate_submitted_password(
        cls,
        value: SecretStr,
    ) -> SecretStr:
        """Reject empty or unreasonably large login passwords."""

        password_length = len(value.get_secret_value())

        if (
            password_length == 0
            or password_length > MAX_PASSWORD_LENGTH
        ):
            raise ValueError("Invalid login request.")

        return value


class ChangePasswordRequest(AuthenticationRequest):
    """Passwords required to replace an account password."""

    current_password: SecretStr
    new_password: SecretStr

    @field_validator("current_password")
    @classmethod
    def validate_current_password(
        cls,
        value: SecretStr,
    ) -> SecretStr:
        """Reject an empty or oversized current password."""

        password_length = len(value.get_secret_value())

        if (
            password_length == 0
            or password_length > MAX_PASSWORD_LENGTH
        ):
            raise ValueError("Invalid password request.")

        return value

    @field_validator("new_password")
    @classmethod
    def validate_replacement_password(
        cls,
        value: SecretStr,
    ) -> SecretStr:
        """Enforce the current policy on a replacement password."""

        validate_password(value.get_secret_value())

        return value


class UserResponse(BaseModel):
    """Public account information safe to return to a client."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: str
    created_at: datetime
    updated_at: datetime