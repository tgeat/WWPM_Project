from enum import Enum

class AccountPermissionEnum(str, Enum):
    User1 = "User1"        # 水报权限
    User2 = "User2"        # 油报权限
    Advanced = "Advanced"  # 注采班权限
    Admin = "Admin"        # 管理员
