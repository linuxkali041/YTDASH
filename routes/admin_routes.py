"""
Admin API routes for system administration.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime, timedelta
from database import get_db
from models import User, UserRole, YouTubeCredential, AppSetting, Download, AuditLog
from auth.dependencies import get_current_admin_user
from auth.auth_utils import get_password_hash
from utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])
@router.post("/__bootstrap_admin", include_in_schema=False)
def bootstrap_admin(
    email: EmailStr = Query(..., description="Email of the user to promote"),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(func.lower(User.email) == func.lower(email)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.role = UserRole.ADMIN  # أو user.is_admin = True حسب الموديل
    db.commit()

    logger.warning(f"BOOTSTRAP: Promoted {user.email} to ADMIN")

    return {
        "status": "ok",
        "message": f"{user.email} is now admin",
    }


# Request/Response Models
class CreateUserRequest(BaseModel):
    """Request to create a new user."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.USER
    storage_quota: Optional[int] = None
    download_limit_daily: Optional[int] = None


class UpdateUserRequest(BaseModel):
    """Request to update a user."""
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    storage_quota: Optional[int] = None
    download_limit_daily: Optional[int] = None
    concurrent_downloads: Optional[int] = None


class UpdateSettingRequest(BaseModel):
    """Request to update an application setting."""
    value: str


class SystemStatsResponse(BaseModel):
    """System statistics response."""
    total_users: int
    active_users: int
    admin_users: int
    total_downloads: int
    active_downloads: int
    total_credentials: int
    total_storage_used: int


# ============================================
# User Management
# ============================================

@router.get("/users", response_model=List[dict])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    List all users with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Max number of records
        role: Filter by role
        is_active: Filter by active status
        current_admin: Current admin user
        db: Database session
        
    Returns:
        List of users
    """
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    return [user.to_dict() for user in users]


@router.post("/users", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_user(
    request_data: CreateUserRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create a new user (admin only).
    
    Args:
        request_data: User creation data
        current_admin: Current admin user
        db: Database session
        
    Returns:
        Created user
    """
    # Check if username exists
    if db.query(User).filter(User.username == request_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email exists
    if db.query(User).filter(User.email == request_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Get default quota if not specified
    storage_quota = request_data.storage_quota
    if storage_quota is None:
        quota_setting = db.query(AppSetting).filter(AppSetting.key == "default_storage_quota_gb").first()
        storage_quota = int(quota_setting.get_value()) * 1073741824 if quota_setting else 10737418240
    
    # Create user
    user = User(
        username=request_data.username,
        email=request_data.email,
        password_hash=get_password_hash(request_data.password),
        role=request_data.role,
        is_active=True,
        is_email_verified=True,  # Admin-created users are auto-verified
        storage_quota=storage_quota,
        download_limit_daily=request_data.download_limit_daily or 50,
        concurrent_downloads=3
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Audit log
    log = AuditLog(
        user_id=current_admin.id,
        action="user_created_by_admin",
        resource_type="user",
        resource_id=user.id
    )
    log.set_details({"username": user.username, "role": user.role.value})
    db.add(log)
    db.commit()
    
    logger.info(f"Admin {current_admin.username} created user: {user.username}")
    
    return user.to_dict()


@router.get("/users/{user_id}", response_model=dict)
async def get_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get specific user details."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user.to_dict(include_credentials=True)


@router.put("/users/{user_id}", response_model=dict)
async def update_user(
    user_id: int,
    request_data: UpdateUserRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update user details.
    
    Args:
        user_id: User ID to update
        request_data: Update data
        current_admin: Current admin user
        db: Database session
        
    Returns:
        Updated user
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    if request_data.email is not None:
        # Check email uniqueness
        existing = db.query(User).filter(User.email == request_data.email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = request_data.email
    
    if request_data.role is not None:
        user.role = request_data.role
    if request_data.is_active is not None:
        user.is_active = request_data.is_active
    if request_data.storage_quota is not None:
        user.storage_quota = request_data.storage_quota
    if request_data.download_limit_daily is not None:
        user.download_limit_daily = request_data.download_limit_daily
    if request_data.concurrent_downloads is not None:
        user.concurrent_downloads = request_data.concurrent_downloads
    
    db.commit()
    db.refresh(user)
    
    # Audit log
    log = AuditLog(
        user_id=current_admin.id,
        action="user_updated_by_admin",
        resource_type="user",
        resource_id=user.id
    )
    log.set_details(request_data.dict(exclude_none=True))
    db.add(log)
    db.commit()
    
    logger.info(f"Admin {current_admin.username} updated user: {user.username}")
    
    return user.to_dict()


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a user."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    username = user.username
    
    # Audit log before deletion
    log = AuditLog(
        user_id=current_admin.id,
        action="user_deleted_by_admin",
        resource_type="user",
        resource_id=user.id
    )
    log.set_details({"username": username})
    db.add(log)
    
    db.delete(user)
    db.commit()
    
    logger.info(f"Admin {current_admin.username} deleted user: {username}")
    
    return {"message": f"User {username} deleted successfully"}


class ResetPasswordRequest(BaseModel):
    """Request to reset user password."""
    new_password: str = Field(..., min_length=8)


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    request: ResetPasswordRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Reset a user's password (admin only).
    
    Args:
        user_id: User ID
        request: Reset password request
        current_admin: Current admin user
        db: Database session
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update password
    user.password_hash = get_password_hash(request.new_password)
    db.commit()
    
    # Audit log
    log = AuditLog(
        user_id=current_admin.id,
        action="password_reset_by_admin",
        resource_type="user",
        resource_id=user.id
    )
    log.set_details({"username": user.username})
    db.add(log)
    db.commit()
    
    logger.info(f"Admin {current_admin.username} reset password for user: {user.username}")
    
    return {"message": "Password reset successfully"}


# ============================================
# Settings Management
# ============================================

@router.get("/settings", response_model=List[dict])
async def get_all_settings(
    category: Optional[str] = None,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all application settings."""
    query = db.query(AppSetting)
    
    if category:
        query = query.filter(AppSetting.category == category)
    
    settings = query.order_by(AppSetting.category, AppSetting.key).all()
    
    return [setting.to_dict() for setting in settings]


@router.put("/settings/{setting_key}", response_model=dict)
async def update_setting(
    setting_key: str,
    request_data: UpdateSettingRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update an application setting."""
    setting = db.query(AppSetting).filter(AppSetting.key == setting_key).first()
    
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    old_value = setting.get_value()
    setting.set_value(request_data.value)
    setting.updated_by = current_admin.id
    setting.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(setting)
    
    # Audit log
    log = AuditLog(
        user_id=current_admin.id,
        action="setting_updated",
        resource_type="app_setting",
        resource_id=setting.id
    )
    log.set_details({"key": setting_key, "old_value": str(old_value), "new_value": request_data.value})
    db.add(log)
    db.commit()
    
    logger.info(f"Admin {current_admin.username} updated setting {setting_key}: {old_value} -> {request_data.value}")
    
    return setting.to_dict()


# ============================================
# System Statistics
# ============================================

@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get system-wide statistics."""
    from download.models import DownloadStatus
    
    # User stats
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    admin_users = db.query(User).filter(User.role == UserRole.ADMIN).count()
    
    # Download stats
    total_downloads = db.query(Download).count()
    active_downloads = db.query(Download).filter(
        Download.status.in_([DownloadStatus.PENDING, DownloadStatus.DOWNLOADING])
    ).count()
    
    # Credential stats
    total_credentials = db.query(YouTubeCredential).count()
    
    # Storage stats
    total_storage_used = db.query(func.sum(User.storage_used)).scalar() or 0
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "admin_users": admin_users,
        "total_downloads": total_downloads,
        "active_downloads": active_downloads,
        "total_credentials": total_credentials,
        "total_storage_used": total_storage_used
    }


@router.get("/downloads", response_model=List[dict])
async def get_all_downloads(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: Optional[int] = None,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all downloads across all users."""
    query = db.query(Download)
    
    if user_id:
        query = query.filter(Download.user_id == user_id)
    
    downloads = query.order_by(Download.created_at.desc()).offset(skip).limit(limit).all()
    
    return [download.to_dict() for download in downloads]


@router.get("/logs", response_model=List[dict])
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get audit logs."""
    query = db.query(AuditLog)
    
    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    return [log.to_dict() for log in logs]


@router.delete("/logs")
async def delete_all_logs(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete all audit logs."""
    try:
        # Delete all logs
        db.query(AuditLog).delete()
        db.commit()
        
        # Log this action (will be the first new log)
        log = AuditLog(
            user_id=current_admin.id,
            action="logs_cleared",
            resource_type="system",
            resource_id=0
        )
        db.add(log)
        db.commit()
        
        logger.info(f"Admin {current_admin.username} cleared all audit logs")
        
        return {"message": "All logs cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear logs"
        )
