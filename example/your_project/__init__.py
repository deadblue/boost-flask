__author__ = 'deadblue'

from flask import Flask

def create_app():
    app = Flask(
        import_name=__name__
    )
    # TODO: Add your code to configure app
    return app