__author__ = 'deadblue'

import json as jsonlib
from typing import Any, Callable

from flask import (
    Response, make_response, render_template
)


RendererType = Callable[[Any], Response]


default = make_response


def json(result: Any) -> Response:
    """
    JSON renderer
    """
    resp_body = jsonlib.dumps(result)
    resp = Response(resp_body, status=200)
    resp.headers.update({
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Length': len(resp_body)
    })
    return resp


class TemplateRenderer:

    _template_name: str
    _mime_type: str

    def __init__(self, template_name: str, mime_type: str) -> None:
        """
        TemplateRenderer renders content with specified template.

        Args:
            template_name (str): Template file name.
            mime_type (str): The MIME tpye of rendered content.
        """

        super().__init__()
        self._template_name = template_name
        self._mime_type = mime_type

    def __call__(self, result: Any) -> Response:
        resp_body = render_template(self._template_name, **result).encode()
        resp = Response(resp_body, status=200)
        resp.headers.update({
            'Content-Type': self._mime_type,
            'Content-Length': len(resp_body)
        })
        return resp


def from_template(template_name: str, mime_type: str) -> TemplateRenderer:
    """
    Helper function to create a TemplateRenderer with template name and MIME type.

    Args:
        template_name (str): Template file name.
        mime_type (str): The MIME tpye of rendered content.
    
    Returns:
        TemplateRenderer: renderer instance.
    """
    return TemplateRenderer(template_name, mime_type)


def html(template_name: str) -> TemplateRenderer:
    """
    Helper function to create a HTML Renderer.

    Args:
        template_name (str): Template file name.

    Returns:
        TemplateRenderer: renderer instance.
    """
    return from_template(template_name, 'text/html; charset=utf-8')
