import time
import random

from flask import render_template, redirect, url_for
from flask import Blueprint

home_blueprint = Blueprint("home", __name__, url_prefix='/home')


@home_blueprint.route('/index')
def index():
    pass


