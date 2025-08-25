import os
from dotenv import load_dotenv

load_dotenv()


class AuthManager:
    def __init__(self):
        self.authorized_users = set()
        # Load from environment or config file
        auth_users = os.getenv("AUTHORIZED_USERS", "")
        if auth_users:
            self.authorized_users.update(map(int, auth_users.split(",")))
    
    def is_authorized(self, user_id: int) -> bool:
        return user_id in self.authorized_users or len(self.authorized_users) == 0
    
    def add_user(self, user_id: int):
        self.authorized_users.add(user_id)
    
    def remove_user(self, user_id: int):
        self.authorized_users.discard(user_id)
