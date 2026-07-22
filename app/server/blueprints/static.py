"""Static file serving and React SPA catch-all."""

import os

from flask import Blueprint, send_from_directory

bp = Blueprint('static', __name__)

_static_folder = None


def init_static(app):
    global _static_folder
    _static_folder = app.static_folder


@bp.route('/')
def serve():
    return send_from_directory(_static_folder, 'index.html')


@bp.route('/<path:path>')
def static_proxy(path):
    file_path = os.path.join(_static_folder, path)
    if os.path.isfile(file_path):
        return send_from_directory(_static_folder, path)
    return send_from_directory(_static_folder, 'index.html')
