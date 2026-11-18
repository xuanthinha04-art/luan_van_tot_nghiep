from flask_login import UserMixin


class AuthUser(UserMixin):
    def __init__(
        self,
        user_id: int,
        full_name: str,
        email: str,
        password_hash: str,
        avatar_url: str | None,
        role_id: int,
        role_name: str,
        account_status: str,
    ):
        self.user_id = int(user_id)
        self.full_name = full_name
        self.email = email
        self.password_hash = password_hash
        self.avatar_url = avatar_url
        self.role_id = int(role_id)
        self.role_name = role_name
        self.account_status = account_status

    def get_id(self):
        return str(self.user_id)

    @property
    def is_active(self):
        return self.account_status == "ACTIVE"
