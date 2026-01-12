"""
Authentication API routes for user registration, login, and logout.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from database import get_db
from models import User, UserRole, AuditLog
from auth.auth_utils import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    validate_password_strength
)
from auth.dependencies import get_current_user, get_current_active_user
from utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


# Request/Response Models
class RegisterRequest(BaseModel):
    """User registration request."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    """User login request."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    """User info response."""
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    storage_used: int
    storage_quota: int


def create_audit_log(db: Session, user_id: int, action: str, details: dict, request: Request = None):
    """Helper to create audit log entry."""
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type="auth",
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    log.set_details(details)
    db.add(log)
    db.commit()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request_data: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    Args:
        request_data: Registration data
        request: HTTP request
        db: Database session
        
    Returns:
        Access token and user info
        
    Raises:
        HTTPException: If username/email already exists or validation fails
    """
    # Check if registration is enabled (from settings)
    from models import AppSetting
    reg_setting = db.query(AppSetting).filter(AppSetting.key == "registration_enabled").first()
    if reg_setting and not reg_setting.get_value():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is currently disabled"
        )
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(request_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == request_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == request_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Get default storage quota from settings
    quota_setting = db.query(AppSetting).filter(AppSetting.key == "default_storage_quota_gb").first()
    default_quota = int(quota_setting.get_value()) * 1073741824 if quota_setting else 10737418240  # 10GB
    
    # Create new user
    user = User(
        username=request_data.username,
        email=request_data.email,
        password_hash=get_password_hash(request_data.password),
        role=UserRole.USER,
        is_active=True,
        storage_quota=default_quota
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create audit log
    create_audit_log(
        db, user.id, "user_registered",
        {"username": user.username, "email": user.email},
        request
    )
    
    # Generate tokens
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    logger.info(f"New user registered: {user.username}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user.to_dict()
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    request_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    User login.
    
    Args:
        request_data: Login credentials
        request: HTTP request
        db: Database session
        
    Returns:
        Access token and user info
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user
    user = db.query(User).filter(User.username == request_data.username).first()
    
    # Verify password
    if not user or not verify_password(request_data.password, user.password_hash):
        # Create failed login audit log
        if user:
            create_audit_log(
                db, user.id, "login_failed",
                {"username": request_data.username, "reason": "invalid_password"},
                request
            )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        create_audit_log(
            db, user.id, "login_failed",
            {"username": request_data.username, "reason": "account_suspended"},
            request
        )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create audit log
    create_audit_log(
        db, user.id, "login_success",
        {"username": user.username},
        request
    )
    
    # Generate tokens
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    logger.info(f"User logged in: {user.username}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user.to_dict()
    }


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    User logout.
    
    Note: With stateless JWT, logout is handled client-side by discarding the token.
    This endpoint is mainly for audit logging.
    
    Args:
        request: HTTP request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    # Create audit log
    create_audit_log(
        db, current_user.id, "logout",
        {"username": current_user.username},
        request
    )
    
    logger.info(f"User logged out: {current_user.username}")
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User information
    """
    return current_user.to_dict()


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_token: Refresh token
        db: Database session
        
    Returns:
        New access token
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    from auth.auth_utils import decode_token
    
    # Decode refresh token
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get user
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Generate new tokens
    new_access_token = create_access_token(data={"sub": user.username})
    new_refresh_token = create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": user.to_dict()
    }
