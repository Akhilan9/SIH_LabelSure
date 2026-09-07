from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import verify_password, create_access_token, get_password_hash
from backend.app.core.exceptions import AppException
from backend.app.models import User, UserRole
from backend.app.schemas import LoginRequest, TokenResponse, UserResponse, UserCreate
from backend.app.api.deps import get_current_user, require_role

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == creds.username).first()
    if not user or not verify_password(creds.password, user.hashed_password):
        raise AppException(
            code="INVALID_CREDENTIALS",
            message="Invalid username or password provided.",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    if not user.is_active:
        raise AppException(
            code="INACTIVE_ACCOUNT",
            message="This account has been deactivated.",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    token = create_access_token(data={"sub": user.id, "role": user.role})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        badge_number=user.badge_number
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/register", response_model=UserResponse, dependencies=[Depends(require_role([UserRole.ADMIN]))])
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(
        (User.username == user_in.username) | (User.email == user_in.email)
    ).first()
    if existing:
        raise AppException(
            code="USER_ALREADY_EXISTS",
            message="A user with this username or email already exists.",
            status_code=status.HTTP_409_CONFLICT
        )
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        badge_number=user_in.badge_number
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/users", response_model=List[UserResponse], dependencies=[Depends(require_role([UserRole.ADMIN, UserRole.SUPERVISOR]))])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.created_at.desc()).all()

@router.get("/admin-area")
def admin_area(current_user: User = Depends(require_role([UserRole.ADMIN]))):
    return {
        "message": f"Welcome to the Administrative Control Area, {current_user.full_name}.",
        "role": current_user.role,
        "access_level": "ADMIN_FULL"
    }

@router.get("/supervisor-area")
def supervisor_area(current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPERVISOR]))):
    return {
        "message": f"Welcome to the Supervisory Audit Area, {current_user.full_name}.",
        "role": current_user.role,
        "access_level": "SUPERVISOR_AUDIT"
    }

@router.get("/inspector-area")
def inspector_area(current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.INSPECTOR]))):
    return {
        "message": f"Welcome to the Field Inspection Operations Area, {current_user.full_name}.",
        "role": current_user.role,
        "access_level": "INSPECTOR_FIELD"
    }

@router.get("/viewer-area")
def viewer_area(current_user: User = Depends(get_current_user)):
    return {
        "message": f"Welcome to the Read-Only Observer Area, {current_user.full_name}.",
        "role": current_user.role,
        "access_level": "VIEWER_READONLY"
    }
