"""Module for errors returned by the REST API.
"""
__all__ = ["bad_request", "invalid_parameter"]
import json
from aiohttp import web


def bad_request(label: str, code: int, description: str) -> web.HTTPBadRequest:
    """Raise a **400 (BadRequest)** generic error:

    .. code-block:: python

        {
            "error": "{label}",
            "code": {code},
            "description": "{description}"
        }

    :param label: unique error label
    :param code: unique error code
    :param description: description for debug purpose
    """
    raise web.HTTPBadRequest(
        text=json.dumps(
            {"error": label, "error_code": code, "error_description": description},
            ensure_ascii=False,
        ),
        content_type="application/json",
    )


def invalid_parameter(name: str) -> web.HTTPBadRequest:
    """Raise a **400 (BadRequest)** invalid_parameter error:

    .. code-block:: python

        {
            "error": "invalid_parameter",
            "code": 0,
            "description": "check your {name} parameter"
        }

    :param name: name of expected query parameter
    """
    bad_request(
        label="invalid_parameter", code=0, description=f"check your {name} parameter"
    )
