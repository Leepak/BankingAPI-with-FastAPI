
from fastapi import Depends, HTTPException, status

from app.core.auth import get_current_user
from app.models.user import User, UserRole




def is_active_user(
    current_user: User = Depends(get_current_user)
):
    """
    Ensure user account is active.
    """

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return current_user


def is_admin(
    current_user: User = Depends(is_active_user)
):
    """
    Allow only ADMIN users.
    """
   
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user


def is_customer(
    current_user: User = Depends(is_active_user)
):
    """
    Allow only CUSTOMER users.
    """


    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer access required"
        )

    return current_user


# Also check using string comparison
    user_role_str = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    logger.info(f"Role as string: {user_role_str}")
    
    if current_user.role != UserRole.CUSTOMER:
        logger.error(f"Customer access denied for {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Customer access required. Your role: {current_user.role}"
        )

    return current_user




def admin_or_customer(
    current_user: User = Depends(is_active_user)
):
    """
    Allow both ADMIN and CUSTOMER users.
    Useful for authenticated endpoints.
    """
    

    if current_user.role not in [
        UserRole.ADMIN,
        UserRole.CUSTOMER
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return current_user




