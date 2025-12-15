from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Header
from ..services.user_service import UserService
from ..models.user import RegisterRequest, LoginRequest, UpdateProfileRequest, LoginResponse, UserProfileResponse

user_router = APIRouter(prefix='/users', tags=['Users'])


def get_current_user(authorization: str | None = Header(default=None),user_service: UserService = Depends(UserService)) -> UUID:
    if not authorization:
        raise HTTPException(status_code=403, detail="Authorization header missing")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization[7:]

    try:
        return user_service.verify_token(token)
    except ValueError as e:
        # Например, "Token expired" или "Invalid token"
        raise HTTPException(status_code=401, detail=str(e))


@user_router.post('/register', response_model=UserProfileResponse)
def register_user(
        request: RegisterRequest,
        user_service: UserService = Depends(UserService)
):
    try:
        return user_service.register_user(request)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")


@user_router.post('/login', response_model=LoginResponse)
def login_user(
        request: LoginRequest,
        user_service: UserService = Depends(UserService)
):
    try:
        return user_service.login_user(request)
    except ValueError as e:
        raise HTTPException(401, str(e))
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")


@user_router.put('/profile', response_model=UserProfileResponse)
def update_profile(
        request: UpdateProfileRequest,
        current_user: UUID = Depends(get_current_user),
        user_service: UserService = Depends(UserService)
):
    try:
        return user_service.update_profile(current_user, request)
    except KeyError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")


@user_router.get('/profile', response_model=UserProfileResponse)
def get_profile(
        current_user: UUID = Depends(get_current_user),
        user_service: UserService = Depends(UserService)
):
    try:
        return user_service.get_user_profile(current_user)
    except KeyError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")


@user_router.get('/{user_id}', response_model=UserProfileResponse)
def get_user_by_id(
        user_id: UUID,
        user_service: UserService = Depends(UserService)
):
    try:
        return user_service.get_user_profile(user_id)
    except KeyError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")