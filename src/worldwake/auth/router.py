"""HTTP endpoints for WorldWake authentication."""



from fastapi import (
    APIRouter,
    HTTPException,
    Response,
    status,
)

from worldwake.auth.cookies import (
    clear_authentication_cookies,
    set_authentication_cookies,
)

from worldwake.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    UserResponse,
    ChangePasswordRequest,
)

from worldwake.auth.service import (
    ACCOUNT_CONFLICT_MESSAGE,
    INCORRECT_CURRENT_PASSWORD_MESSAGE,
    INVALID_CREDENTIALS_MESSAGE,
    AccountConflictError,
    IncorrectCurrentPasswordError,
    InvalidCredentialsError,
    authenticate_user,
    change_user_password,
    register_user,
)

from worldwake.auth.sessions import (
    create_auth_session,
    revoke_all_auth_sessions,
    revoke_auth_session,
)



router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)

from worldwake.auth.dependencies import (
    CsrfProtectedSession,
    CurrentUser,
    DatabaseSession,
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_account(
    registration: RegisterRequest,
    response: Response,
    database_session: DatabaseSession,
) -> UserResponse:
    """Create an account and sign in the new user."""

    try:
        user = register_user(
            database_session,
            registration,
        )
        issued_session = create_auth_session(
            database_session,
            user,
        )
    except AccountConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ACCOUNT_CONFLICT_MESSAGE,
        ) from error

    set_authentication_cookies(
        response,
        issued_session,
    )

    return UserResponse.model_validate(user)

@router.post(
    "/login",
    response_model=UserResponse,
)
def login_account(
    login: LoginRequest,
    response: Response,
    database_session: DatabaseSession,
) -> UserResponse:
    """Authenticate an account and create a browser session."""

    try:
        user = authenticate_user(
            database_session,
            login,
        )
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS_MESSAGE,
        ) from error

    issued_session = create_auth_session(
        database_session,
        user,
    )

    set_authentication_cookies(
        response,
        issued_session,
    )

    return UserResponse.model_validate(user)

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout_account(
    response: Response,
    auth_session: CsrfProtectedSession,
) -> None:
    """Revoke the current browser session and clear its cookies."""

    revoke_auth_session(auth_session)

    clear_authentication_cookies(response)

@router.post(
    "/change-password",
    response_model=UserResponse,
)
def change_password(
    request: ChangePasswordRequest,
    response: Response,
    auth_session: CsrfProtectedSession,
    database_session: DatabaseSession,
) -> UserResponse:
    """Replace a password and invalidate every existing session."""

    user = auth_session.user

    try:
        change_user_password(
            database_session,
            user,
            request.current_password.get_secret_value(),
            request.new_password.get_secret_value(),
        )
    except IncorrectCurrentPasswordError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INCORRECT_CURRENT_PASSWORD_MESSAGE,
        ) from error

    revoke_all_auth_sessions(
        database_session,
        user.id,
    )

    fresh_session = create_auth_session(
        database_session,
        user,
    )

    set_authentication_cookies(
        response,
        fresh_session,
    )

    return UserResponse.model_validate(user)    

@router.get(
    "/me",
    response_model=UserResponse,
)
def read_current_account(
    current_user: CurrentUser,
) -> UserResponse:
    """Return the safely exposed signed-in account."""

    return UserResponse.model_validate(
        current_user
    )