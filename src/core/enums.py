from enum import Enum


class AccountPermissionEnum(str, Enum):
    User = "User"
    Advanced = "Advanced"
    Admin = "Admin"