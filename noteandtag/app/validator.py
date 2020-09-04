"""Module for validating user inputs to the REST API.
"""
__all__ = ["filtering"]
import json
import re
from aiohttp import web
from functools import wraps
from noteandtag.app import error
from typing import List


def _parse_int_query_param(request, name: str) -> int:
    """Parse a query parameter as int.

    Raise an **invalid_parameter** error if an exception occurs.

    :param request: HTTP request
    :param name: parameter name
    :return: parameter value
    """
    if name not in request.rel_url.query:
        return None

    try:
        return int(request.rel_url.query[name])
    except:
        error.invalid_parameter(name)


def _parse_sort_query_param(request, name: str) -> List:
    """Parse the sortBy query parameter.

    The **sortBy** parameter must be a comma-separated list of fields:

    .. code-block:: python

        sortBy=field1,field2,...

    An optional sort order can be specified:

    .. code-block:: python

        sortBy=field1:asc,field2:desc,...

    Raise an **invalid_parameter** error if an exception occurs.

    :param request: HTTP request
    :param name: parameter name
    :return: parameter value
    """
    if name not in request.rel_url.query:
        return None

    items = []
    params = request.rel_url.query[name].split(",")
    print(params)
    pattern = r"^(?P<field>\w+)(?:\:(?P<order>asc|desc))?$"
    for _ in params:
        m = re.match(pattern, _)
        print(_, m)
        if not m:
            error.invalid_parameter(name)

        items.append({
            "field": m.group("field"),
            "order": m.group("order")
        })

    return items


def filtering(fun):
    """Filter results by offset and limit.

    .. code-block:: python

        "X-Total-Count": {total}

    Raise an **invalid_parameter** error if user inputs are invalid.

    """
    @wraps(fun)
    async def wrapper(self, *args, **kwargs):
        # Filter items according to parameters
        items, total = await fun(
            self,
            *args,
            filters={
                "offset": _parse_int_query_param(self.request, "offset"),
                "limit": _parse_int_query_param(self.request, "limit"),
                "sort": _parse_sort_query_param(self.request, "sortBy")
            },
            **kwargs
        )

        # Return items and total count
        return web.Response(
            text=json.dumps(
                items,
                ensure_ascii=False,
            ),
            headers={
                "X-Total-Count": str(total)
            }
        )

    return wrapper
