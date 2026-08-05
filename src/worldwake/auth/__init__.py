"""Authentication utilities for WorldWake."""

from worldwake.auth.passwords import (
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    PasswordValidationError,
    hash_password,
    password_hash_needs_rehash,
    rehash_verified_password,
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
    INVALID_CREDENTIALS_MESSAGE,
    AccountConflictError,
    InvalidCredentialsError,
    authenticate_user,
    find_user_by_identifier,
    register_user,
)

from worldwake.auth.sessions import (
    SESSION_LIFETIME,
    TOKEN_ENTROPY_BYTES,
    IssuedAuthSession,
    create_auth_session,
    ensure_utc,
    find_active_auth_session,
    generate_opaque_token,
    hash_token,
    revoke_auth_session,
)

from worldwake.auth.cookies import (
    COOKIE_MAX_AGE_SECONDS,
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
    SESSION_COOKIE_NAME,
    clear_authentication_cookies,
    secure_cookies_enabled,
    set_authentication_cookies,
)


__all__ = [
    "MAX_PASSWORD_LENGTH",
    "MIN_PASSWORD_LENGTH",
    "PasswordValidationError",
    "hash_password",
    "password_hash_needs_rehash",
    "rehash_verified_password",
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
    "COOKIE_MAX_AGE_SECONDS",
    "CSRF_COOKIE_NAME",
    "CSRF_HEADER_NAME",
    "SESSION_COOKIE_NAME",
    "secure_cookies_enabled",
    "set_authentication_cookies",
    "ensure_utc",
    "find_active_auth_session",
    "INVALID_CREDENTIALS_MESSAGE",
    "InvalidCredentialsError",
    "authenticate_user",
    "find_user_by_identifier",
    "clear_authentication_cookies",
    "revoke_auth_session",
]