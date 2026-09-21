# Package entry (包入口) — importing this file registers every model on Base.metadata.
# main.py only needs `from app import models`; a model missing here would silently get no table.
from app.models.user import User
from app.models.account import Account
from app.models.role import Role
from app.models.session import UserSession
from app.models.otp import OTPCode