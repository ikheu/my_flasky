# -*- coding: utf-8 -*-

from flask import Blueprint

main = Blueprint('main', __name__)

from . import views, errors

from ..models import Permission

@main.app_context_processor
def inject_permissions():
    ''' 注入函数 '''
    return dict(Permission=Permission, str=str)