import hashlib
import json
import os

from core.constant import ACCOUNT_FILE
from core.enums import AccountPermissionEnum
from core.dataclass import Account


class LoginModel:
    def __init__(self):
        self._account_dict = self._load_account()
        self._accounts = [
            Account.from_dict(account) for account in self._account_dict.values()
        ]

    def add_user(self, username, password, permission=AccountPermissionEnum.Admin):
        account = Account(username, self._password_hash(password), permissions=permission)
        self._accounts.append(account)
        self._account_dict[account.username] = account.to_dict()
        self._save_account()

    def get_user(self, username):
        return next(
            (account for account in self._accounts if account.username == username),
            None,
        )

    def get_all_users(self):
        return self._accounts

    def check_password(self, username, password):
        account = self.get_user(username)
        if account is None:
            return False
        return account.password == self._password_hash(password)

    def delete_user(self, username):
        self._accounts = [account for account in self._accounts if account.username != username]
        if username in self._account_dict:
            self._account_dict.pop(username)
            self._save_account()

    def _password_hash(self, password):
        return hashlib.md5(password.encode()).hexdigest()

    def _save_account(self):
        with open(ACCOUNT_FILE, "w", encoding="utf-8") as f:
            json.dump(self._account_dict, f, ensure_ascii=False, indent=2)

    def _load_account(self):
        try:
            if not os.path.exists(ACCOUNT_FILE):
                return {}
            with open(ACCOUNT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            try:
                os.remove(ACCOUNT_FILE)
            except Exception:
                pass
            return {}

# ✅ 测试入口
if __name__ == "__main__":
    login_model = LoginModel()
    login_model.add_user("admin", "123")
    print("用户：超级管理员", login_model.get_user("超级管理员"))
    print("用户：admin1", login_model.get_user("admin1"))
    print("用户：admin", login_model.get_user("admin"))
