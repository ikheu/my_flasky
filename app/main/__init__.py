from flask import Blueprint
main = Blueprint('mian', __name__)
from . import views, errors