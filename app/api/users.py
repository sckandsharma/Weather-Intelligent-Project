from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin
from app.database.models import User, UserRole
from app.database.session import get_db
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


class UserRoleUpdate(BaseModel):
    role: UserRole


@router.get("/me", response_model=UserResponse)
def read_my_profile(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


@router.get("/", response_model=list[UserResponse])
def list_users(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)).all())


@router.patch("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user