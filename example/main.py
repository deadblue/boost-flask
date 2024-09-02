__author__ = 'deadblue'

import logging
logging.basicConfig(
    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S',
    format='[%(asctime)s] %(name)s - %(message)s'
)

from boostflask import Bootstrap

from your_project import create_app


def _main():
    with Bootstrap(
        app=create_app(),
        # URL prefix for all views
        url_prefix='/api',
        # App config
        app_conf={
            'foo': {
                'bar': 123456
            }
        }
    ) as app:
        # Run app directly
        app.run()
        # Or run it with other WSGI server:
        # import waitress
        # waitress.serve(app)

if __name__ == '__main__':
    _main()