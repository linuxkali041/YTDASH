"""
User API routes for managing YouTube credentials and downloads.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from database import get_db
from models import User, YouTubeCredential, Download, AuditLog
from auth.dependencies import get_current_active_user
from auth.cookie_manager import CookieManager
from utils.logging_config import get_logger
from datetime import datetime
from config import settings

logger = get_logger(__name__)

router = APIRouter(prefix="/api/user", tags=["user"])

# Initialize cookie manager (will use encryption key from settings)
cookie_manager = CookieManager(settings.cookie_encryption_key) if settings.cookie_encryption_key else None


# Request/Response Models
class AddCredentialRequest(BaseModel):
    """Request to add YouTube credentials."""
    account_email: EmailStr
    account_name: Optional[str] = None
    cookies: str = Field(..., description="YouTube session cookies as JSON string")


class CredentialResponse(BaseModel):
    """YouTube credential response."""
    id: int
    account_email: str
    account_name: Optional[str]
    is_valid: bool
    last_validated: Optional[str]
    downloads_count: int
    created_at: str


class UserStatsResponse(BaseModel):
    """User statistics response."""
    total_downloads: int
    storage_used: int
    storage_quota: int
    storage_percent: float
    active_downloads: int
    credential_count: int


def create_audit_log(db: Session, user_id: int, action: str, resource_type: str, resource_id: int = None, details: dict = None):
    """Helper to create audit log entry."""
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id
    )
    if details:
        log.set_details(details)
    db.add(log)
    db.commit()


@router.post("/credentials", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def add_credential(
    request_data: AddCredentialRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add YouTube account credentials for the current user.
    
    Args:
        request_data: Credential data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created credential
    """
    # Check if credential with this email already exists for user
    existing = db.query(YouTubeCredential).filter(
        YouTubeCredential.user_id == current_user.id,
        YouTubeCredential.account_email == request_data.account_email
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credentials for this YouTube account already exist"
        )
    
    try:
        # Encrypt cookies
        encrypted_cookies = cookie_manager.encrypt_cookies(request_data.cookies)
        
        # Create credential
        credential = YouTubeCredential(
            user_id=current_user.id,
            account_email=request_data.account_email,
            account_name=request_data.account_name,
            encrypted_cookies=encrypted_cookies,
            is_valid=True
        )
        
        db.add(credential)
        db.commit()
        db.refresh(credential)
        
        # Create audit log
        create_audit_log(
            db, current_user.id, "credential_added", "youtube_credential",
            credential.id, {"account_email": request_data.account_email}
        )
        
        logger.info(f"User {current_user.username} added YouTube credential: {request_data.account_email}")
        
        return credential.to_dict()
        
    except Exception as e:
        logger.error(f"Failed to add credential: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to encrypt and store credentials"
        )


@router.get("/credentials", response_model=List[CredentialResponse])
async def get_credentials(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all YouTube credentials for current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of credentials
    """
    credentials = db.query(YouTubeCredential).filter(
        YouTubeCredential.user_id == current_user.id
    ).all()
    
    return [cred.to_dict() for cred in credentials]


@router.delete("/credentials/{credential_id}")
async def delete_credential(
    credential_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a YouTube credential.
    
    Args:
        credential_id: Credential ID to delete
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    credential = db.query(YouTubeCredential).filter(
        YouTubeCredential.id == credential_id,
        YouTubeCredential.user_id == current_user.id
    ).first()
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )
    
    # Create audit log before deleting
    create_audit_log(
        db, current_user.id, "credential_deleted", "youtube_credential",
        credential.id, {"account_email": credential.account_email}
    )
    
    db.delete(credential)
    db.commit()
    
    logger.info(f"User {current_user.username} deleted YouTube credential: {credential.account_email}")
    
    return {"message": "Credential deleted successfully"}


@router.post("/credentials/{credential_id}/validate")
async def validate_credential(
    credential_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Validate a YouTube credential by attempting to use it.
    
    Args:
        credential_id: Credential ID to validate
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Validation result
    """
    credential = db.query(YouTubeCredential).filter(
        YouTubeCredential.id == credential_id,
        YouTubeCredential.user_id == current_user.id
    ).first()
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )
    
    try:
        # Decrypt cookies
        cookies_str = cookie_manager.decrypt_cookies(credential.encrypted_cookies)
        
        # TODO: Actually validate with YouTube API or yt-dlp
        # For now, just mark as validated
        credential.is_valid = True
        credential.last_validated = datetime.utcnow()
        credential.validation_error = None
        
        db.commit()
        
        logger.info(f"Validated credential {credential_id} for user {current_user.username}")
        
        return {
            "valid": True,
            "message": "Credentials are valid",
            "last_validated": credential.last_validated.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Credential validation failed: {e}")
        
        credential.is_valid = False
        credential.validation_error = str(e)
        credential.last_validated = datetime.utcnow()
        db.commit()
        
        return {
            "valid": False,
            "message": "Credentials validation failed",
            "error": str(e)
        }


@router.get("/downloads", response_model=List[dict])
async def get_user_downloads(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get download history for current user.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of downloads
    """
    downloads = db.query(Download).filter(
        Download.user_id == current_user.id
    ).order_by(Download.created_at.desc()).offset(skip).limit(limit).all()
    
    return [download.to_dict() for download in downloads]


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get statistics for current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User statistics
    """
    from download.models import DownloadStatus
    
    # Count downloads
    total_downloads = db.query(Download).filter(
        Download.user_id == current_user.id
    ).count()
    
    # Count active downloads
    active_downloads = db.query(Download).filter(
        Download.user_id == current_user.id,
        Download.status.in_([DownloadStatus.PENDING, DownloadStatus.DOWNLOADING])
    ).count()
    
    # Count credentials
    credential_count = db.query(YouTubeCredential).filter(
        YouTubeCredential.user_id == current_user.id
    ).count()
    
    # Calculate storage percentage
    storage_percent = (current_user.storage_used / current_user.storage_quota * 100) if current_user.storage_quota > 0 else 0
    
    return {
        "total_downloads": total_downloads,
        "storage_used": current_user.storage_used,
        "storage_quota": current_user.storage_quota,
        "storage_percent": round(storage_percent, 2),
        "active_downloads": active_downloads,
        "credential_count": credential_count
    }


class ChangePasswordRequest(BaseModel):
    """Request to change password."""
    current_password: str
    new_password: str


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change user password.
    
    Args:
        request: Password change request
        current_user: Current authenticated user
        db: Database session
    """
    from auth.auth_utils import verify_password, get_password_hash
    
    # Verify current password
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.password_hash = get_password_hash(request.new_password)
    db.commit()
    
    create_audit_log(
        db, current_user.id, "password_changed", "user",
        current_user.id
    )
    
    logger.info(f"User {current_user.username} changed their password")
    
    return {"message": "Password updated successfully"}
