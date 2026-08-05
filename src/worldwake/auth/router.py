"""HTTP endpoints for WorldWake authentication."""



from fastapi import (
    APIRouter,
    HTTPException,
    Response,
    status,
)


from worldwake.auth.cookies import (
    set_authentication_cookies,
)
from worldwake.auth.schemas import (
    RegisterRequest,
    UserResponse,
)
from worldwake.auth.service import (
    ACCOUNT_CONFLICT_MESSAGE,
    AccountConflictError,
    register_user,
)
from worldwake.auth.sessions import create_auth_session



router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)

from worldwake.auth.dependencies import (
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