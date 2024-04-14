import datetime
import os

import jwt
from dotenv import load_dotenv
from service.common.repository import User


load_dotenv()
secret_key = os.environ.get("JWT_SECRET_KEY")


class Token:
    def create_token_by_user(user: User):
        payload = {
            "id": user.id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30),
        }
        token = jwt.encode(payload, secret_key)
        return token

    def get_user_id_by_token(token):
        try:
            token_info = jwt.decode(token, secret_key, algorithms="HS256")
        except jwt.exceptions.DecodeError:
            raise Exception("잘못된 JWT")
        token_user_id = token_info.get("id")
        return token_user_id
