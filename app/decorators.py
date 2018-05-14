# -*- coding: utf-8 -*-

from functools import wraps
from flask import abort
from flask_login import current_user
from .models import Permission

# 修饰器-权限
def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*arg, **kw):
            if not current_user.can(permission):
                abort(403)
            return f(*arg, **kw)
        return decorated_function
    return decorator

# 修饰器-管理员权限
def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)