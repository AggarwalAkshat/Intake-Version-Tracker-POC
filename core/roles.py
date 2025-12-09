USER = "user"
ADMIN = "admin"
VIEWER = "viewer"  # optional, read-only role for testing

def is_user(user) -> bool:
    return user.role == USER

def is_admin(user) -> bool:
    return user.role == ADMIN

def is_viewer(user) -> bool:
    return user.role == VIEWER