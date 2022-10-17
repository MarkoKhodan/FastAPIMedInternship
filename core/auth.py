import os
import jwt
from fastapi import HTTPException
from datetime import datetime, timedelta


class Auth:
    secret = os.getenv("APP_SECRET_STRING")

    def encode_token(self, email):
        payload = {
            "exp": datetime.utcnow() + timedelta(days=0, minutes=30),
            "iat": datetime.utcnow(),
            "sub": email,
        }
        return jwt.encode(payload, self.secret, algorithm="HS256")

    def decode_token(self, token):
        try:
            payload = jwt.decode(token, self.secret, algorithms=["HS256"])
            return payload["sub"]
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    def refresh_token(self, expired_token):
        try:
            payload = jwt.decode(
                expired_token,
                self.secret,
                algorithms=["HS256"],
                options={"verify_exp": False},
            )
            username = payload["sub"]
            new_token = self.encode_token(username)
            return {"token": new_token}
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
