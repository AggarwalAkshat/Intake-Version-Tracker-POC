from .models import User

def get_mock_users():
    """
    For the POC, we hard-code a few users with different roles.
    Later, this will be replaced by Easy Auth / Entra ID integration.
    """
    return [
        User(
            id="user-1",
            display_name="Akshat (User)",
            email="akshat.user@example.com",
            role="user",
        ),
        User(
            id="user-2",
            display_name="OPS Admin",
            email="admin@example.com",
            role="admin",
        ),
        User(
            id="user-3",
            display_name="OPS Viewer (Read-only)",
            email="viewer@example.com",
            role="viewer",
        ),
    ]