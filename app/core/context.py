# app/core/context.py
from contextvars import ContextVar

# Biến này sẽ chứa user_id, mặc định là None
user_id_context: ContextVar[int] = ContextVar("user_id", default=None)

def get_current_user_id():
    return user_id_context.get()

def set_current_user_id(user_id: int):
    return user_id_context.set(user_id)