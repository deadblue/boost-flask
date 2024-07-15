# BootFlask

Say good-bye to `app.add_url_rule` or `@app.route`.

# Install

```bash
pip install git+https://github.com/deadblue/bootflask.git@master
```

# Exmaple

First, create your project with following layout:

```
your_project    # Top-level package
- views
| - __init__.py
| - foo1.py     # View module1
| - foo2.py     # View module2
- services
| - __init__.py
| - bar.py      # Service module
- other_packages
| - blabla.py   # Helper code
- __init.py__   # Top-level module
main.py         # 
```


```python
# your_project/__init__.py
from flask import Flask

def create_app() -> Flask:
    app = Flask(
        import_name=__name__,   # IMPORTANT!
        # Other parameters
    )


# your_project/views/foo1.py
from bootflask.view import JsonView

class Foo1View(JsonView):
    
    def __init__(self):
        super().__init__(
            url_rule=r'/api/foo1'
        )

    def handle(self):
        # Implement handle function with your business
        return {
            'foo': 'bar'
        }


# your_project/views/foo2.py
from bootflask.view import JsonView

from your_project.services.bar import BarService

class Foo2View(JsonView):
    
    _bar_service: BarService

    # Auto-inject bar_service
    def __init__(
        self, bar_service: BarService
    ):
        super().__init__(
            url_rule=r'/api/foo2'
        )
        self._bar_service = bar_service

    def handle(self):
        # Implement handle function with your business
        result = self._bar_service.balabala()
        return {
            'foo': result
        }


# main.py
from bootflask import Bootstrap

from your_project import create_app

if __name__ == '__main__':
    with Bootstrap(create_app()) as app:
        # Run flask app directly
        app.run()
        # Or run with WSGI server, such as waitress:
        # waitress.serve(app)
```
