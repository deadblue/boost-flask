__author__ = 'deadblue'

import json as jsonlib
from abc import ABC, abstractmethod
from typing import Any

from flask import Response, render_template


class Renderer(ABC):
    """
    BaseRenderer is base class for all Renderer classes, user's custom renderer
    should be derived from this class.
    """

    @abstractmethod
    def render(self, result: Any) -> Response:
        """
        Render result from handler function to a `flask.Response` object.

        Args:
            result (Any): The returned value from handler function in view.
        
        Returns:
            Response: Flask response object.
        """
        pass


class JsonRenderer(Renderer):
    """
    JsonRenderer renders handler's result to JSON response.
    """

    def render(self, result: Any) -> Response:
        resp_body = jsonlib.dumps(result)
        resp = Response(resp_body, status=200)
        resp.headers.update({
            'Content-Type': 'application/json; charset=utf-8',
            'Content-Length': len(resp_body)
        })
        return resp


json = JsonRenderer()
"""
A JsonRenderer instance.

User should always use it instead of calling JsonRenderer().
"""


class TemplateRenderer(Renderer):

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

    def render(self, result: Any) -> Response:
        resp_body = render_template(self._template_name, **result)
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
