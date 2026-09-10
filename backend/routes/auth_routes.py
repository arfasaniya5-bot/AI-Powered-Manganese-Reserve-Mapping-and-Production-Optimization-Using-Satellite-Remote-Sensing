"""
Authentication and User Management Routes
-----------------------------------------
Endpoints for Admin login, User login, logout, and Admin User Management CRUD.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Depends, status
from pydantic import BaseModel, Field
from services.auth_service import auth_service

router = APIRouter(tags=["Authentication & Users"])


# Pydantic Schemas
class AdminLoginRequest(BaseModel):
    admin_id: str = Field(..., description="Administrator identifier")
    password: str = Field(..., description="Admin password")


class UserLoginRequest(BaseModel):
    employee_id: str = Field(..., description="Employee identifier e.g. MOIL001")
    password: str = Field(..., description="User password")


class CreateUserRequest(BaseModel):
    employee_id: str = Field(..., description="Unique Employee ID")
    name: str = Field(..., description="Full employee name")
    password: str = Field(..., description="Initial password")


class UpdateUserRequest(BaseModel):
    name: Optional[str] = Field(None, description="Updated full name")
    status: Optional[str] = Field(None, description="Account status: ACTIVE or INACTIVE")
    password: Optional[str] = Field(None, description="New password (optional)")


# Admin Authorization Dependency
def verify_admin_auth(authorization: Optional[str] = Header(None)):
    """Verifies that the request has a valid Admin session token."""
    # If authorization header is omitted or invalid, return 401
    # Note: For seamless development testing or if frontend passes token, verify token
    if authorization:
        # Check against active tokens
        if auth_service.verify_admin_token(authorization):
            return True
    # If token check fails, reject
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized. Admin authentication required."
    )


# ------------------------------------------------------------------------------
# 1. Authentication Endpoints
# ------------------------------------------------------------------------------

@router.post("/auth/admin/login", summary="Admin Login")
async def admin_login_endpoint(payload: AdminLoginRequest):
    """
    Authenticates an administrator with Admin ID and Password.
    On success, records a row into MySQL login_logs.
    """
    result = auth_service.admin_login(payload.admin_id, payload.password)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.get("message", "Invalid Admin ID or password.")
        )
    return result


@router.post("/auth/user/login", summary="User Login")
async def user_login_endpoint(payload: UserLoginRequest):
    """
    Authenticates a user with Employee ID and Password.
    Enforces account approval: status must be 'ACTIVE'.
    If 'INACTIVE', access is strictly denied with a pending approval message.
    On success, records a row into MySQL login_logs.
    """
    result = auth_service.user_login(payload.employee_id, payload.password)
    if not result.get("success"):
        if result.get("code") == "PENDING_APPROVAL":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=result.get("message", "Your account is pending administrator approval.")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.get("message", "Invalid Employee ID or password.")
            )
    return result


@router.post("/auth/logout", summary="Logout Session")
async def logout_endpoint(authorization: Optional[str] = Header(None)):
    """Logs out active session."""
    auth_service.logout_admin(authorization)
    return {"success": True, "message": "Logged out successfully."}


# ------------------------------------------------------------------------------
# 2. User Management Endpoints (Admin Operations)
# ------------------------------------------------------------------------------

@router.get("/users", summary="Get all users for Admin User Management")
async def list_users_endpoint():
    """
    Returns list of all users.
    Password column is masked with fixed '••••••' placeholder for security.
    """
    users = auth_service.get_users()
    return {"success": True, "users": users}


@router.post("/users", status_code=status.HTTP_201_CREATED, summary="Create a new user")
async def create_user_endpoint(payload: CreateUserRequest):
    """
    Creates a new user. Initial status is strictly set to INACTIVE
    pending Admin approval.
    """
    result = auth_service.create_user(
        employee_id=payload.employee_id,
        name=payload.name,
        password=payload.password
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Could not create user.")
        )
    return result


@router.put("/users/{user_id}", summary="Update user details, status, or password")
async def update_user_endpoint(user_id: int, payload: UpdateUserRequest):
    """
    Updates user account: name, status (ACTIVE or INACTIVE), or password.
    """
    result = auth_service.update_user(
        user_id=user_id,
        name=payload.name,
        status=payload.status,
        password=payload.password
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Could not update user.")
        )
    return result


@router.delete("/users/{user_id}", summary="Delete user account")
async def delete_user_endpoint(user_id: int):
    """
    Permanently removes a user account.
    """
    result = auth_service.delete_user(user_id)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("message", "User not found.")
        )
    return result
