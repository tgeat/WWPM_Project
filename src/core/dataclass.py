from dataclasses import dataclass

from core.enums import AccountPermissionEnum

@dataclass(frozen=True)  # 去掉 slots=True，Python 3.8 不支持
class Account:
    username: str = ""
    password: str = ""
    permissions: AccountPermissionEnum = AccountPermissionEnum.User

    def to_dict(self):
        return {
            "username": self.username,
            "password": self.password,
            "permissions": self.permissions.value  # 序列化为字符串
        }

    @classmethod
    def from_dict(cls, account_dict):
        # 手动将字符串还原为枚举类型
        permission_str = account_dict.get("permissions", "User")
        try:
            permission_enum = AccountPermissionEnum(permission_str)
        except ValueError:
            permission_enum = AccountPermissionEnum.User
        return cls(
            username=account_dict.get("username", ""),
            password=account_dict.get("password", ""),
            permissions=permission_enum
        )