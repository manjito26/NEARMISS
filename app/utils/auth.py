"""
Authentication utilities for NEARMISS System
Handles user authentication and session management
"""
import logging
from ..models.database import NearMissDatabase

logger = logging.getLogger(__name__)

class AuthManager:
    def __init__(self):
        self.db = NearMissDatabase()
    
    def authenticate(self, username: str, password: str) -> dict:
        """
        Authenticate user with username and password
        Returns user dict if successful, None otherwise
        """
        try:
            user = self.db.get_user_by_username(username)
            
            if user and user.get('password_hash'):
                # Verify password for users with password hash (supervisors/admins)
                if self.db.verify_password(password, user['password_hash']):
                    logger.info(f"User {username} authenticated successfully")
                    return user
                else:
                    logger.warning(f"Password verification failed for {username}")
                    return None
            else:
                logger.warning(f"User {username} not found or no password set")
                return None
                
        except Exception as e:
            logger.error(f"Authentication error for {username}: {e}")
            return None
    
    def get_user_privileges(self, username: str) -> dict:
        """Get user privilege information"""
        try:
            user = self.db.get_user_by_username(username)
            if user:
                return {
                    'is_admin': user.get('is_admin', False),
                    'is_supervisor': user.get('is_supervisor', False),
                    'plant': user.get('plant', 'Red Oak')
                }
            return {}
        except Exception as e:
            logger.error(f"Error getting privileges for {username}: {e}")
            return {}
    
    def can_edit_report(self, user_id: int, report_creator_id: int, is_admin: bool = False, is_supervisor: bool = False) -> bool:
        """Check if user can edit a specific report"""
        # Users can edit their own reports
        if user_id == report_creator_id:
            return True
        
        # Supervisors and admins can edit all reports
        if is_admin or is_supervisor:
            return True
        
        return False
    
    def can_access_admin_features(self, is_admin: bool = False) -> bool:
        """Check if user can access admin features"""
        return is_admin
    
    def can_access_supervisor_features(self, is_admin: bool = False, is_supervisor: bool = False) -> bool:
        """Check if user can access supervisor features"""
        return is_admin or is_supervisor
    
    def get_all_users(self) -> list:
        """Get all users for display purposes"""
        try:
            return self.db.get_all_users()
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []