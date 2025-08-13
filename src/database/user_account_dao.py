from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .db_schema import SessionLocal, UserAccount
from ..core.enums import AccountPermissionEnum

from typing import List

# 创建用户
def create_user(username: str, password: str, permission: str ) -> int:
    with SessionLocal() as db:
        exists = db.query(UserAccount).filter_by(username=username).first()
        if exists:
            print("用户名已存在")
            return -1
        user = UserAccount(username=username, password=password, permission=permission)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.user_id

# 读取用户（通过用户名）
def get_user_by_username(username: str) -> UserAccount:
    with SessionLocal() as db:
        return db.query(UserAccount).filter_by(username=username).first()

# 读取所有用户
def list_users() -> List[UserAccount]:
    with SessionLocal() as db:
        return db.query(UserAccount).order_by(UserAccount.username).all()

# 更新密码或权限
def update_user(user_id: int, password: str = None, permission: str = None) -> bool:
    with SessionLocal() as db:
        user = db.get(UserAccount, user_id)
        if not user:
            return False
        if password:
            user.password = password
        if permission:
            user.permission = permission
        db.commit()
        return True

# 删除用户
def delete_user(user_id: int) -> bool:
    with SessionLocal() as db:
        user = db.get(UserAccount, user_id)
        if not user:
            return False
        db.delete(user)
        db.commit()
        return True

# 验证用户名密码
def check_password(username: str, password: str) -> bool:
    with SessionLocal() as db:
        user = db.query(UserAccount).filter_by(username=username, password=password).first()
        return user is not None

# 获取用户账户对象
def get_user(username: str) -> UserAccount:
    with SessionLocal() as db:
        return db.query(UserAccount).filter_by(username=username).first()

if __name__ == "__main__":
    from .db_schema import AccountPermissionEnum

    uid = create_user("admin1", "admin123", AccountPermissionEnum.Admin)
    print(f"用户创建成功，ID={uid}")

    user = get_user_by_username("admin1")
    print("权限等级：", user.permission)

    # update_user(user.user_id, password="newpass456", permission=AccountPermissionEnum.Advanced)
    # print("更新成功")

    # delete_user(user.user_id)
    # print("用户已删除")