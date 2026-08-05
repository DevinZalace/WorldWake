"""Authentication utilities for WorldWake."""

from worldwake.auth.passwords import (
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    PasswordValidationError,
    hash_password,
    password_hash_needs_rehash,
    validate_password,
    verify_password,
)

from worldwake.auth.identities import (
    MAX_USERNAME_LENGTH,
    MIN_USERNAME_LENGTH,
    IdentityValidationError,
    PreparedIdentity,
    prepare_email,
    prepare_username,
)

from worldwake.auth.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)

from worldwake.auth.service import (
    ACCOUNT_CONFLICT_MESSAGE,
    AccountConflictError,
    register_user,
)

from worldwake.auth.sessions import (
    SESSION_LIFETIME,
    TOKEN_ENTROPY_BYTES,
    IssuedAuthSession,
    create_auth_session,
    generate_opaque_token,
    hash_token,
)


__all__ = [
    "MAX_PASSWORD_LENGTH",
    "MIN_PASSWORD_LENGTH",
    "PasswordValidationError",
    "hash_password",
    "password_hash_needs_rehash",
    "validate_password",
    "verify_password",
    "MAX_USERNAME_LENGTH",
    "MIN_USERNAME_LENGTH",
    "IdentityValidationError",
    "PreparedIdentity",
    "prepare_email",
    "prepare_username",
    "ChangePasswordRequest",
    "LoginRequest",
    "RegisterRequest",
    "UserResponse",
    "ACCOUNT_CONFLICT_MESSAGE",
    "AccountConflictError",
    "register_user",
    "SESSION_LIFETIME",
    "TOKEN_ENTROPY_BYTES",
    "IssuedAuthSession",
    "create_auth_session",
    "generate_opaque_token",
    "hash_token",
]