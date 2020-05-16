import json
from aiohttp import web
import aiohttp_cors
import aiohttp_swagger
import aiohttp_jinja2
import jinja2
from typing import Callable, Any, List
from nodeandtag import monad


def validate_required_params(_fun=None, *, names):
    """Validate that a query has all required parameters.

    Role of this decorator is to force returning a `web.HTTPForbidden`
    with an explicit message when one of required query parameters
    is missing.

    This will call the wrapped function with a dict containing
    all required parameters values.

    :param names: list of required parameters
    :return: result of wrapped function or `web.HTTPForbidden`
    """

    def wrapper(fun):
        async def run(self: web.View, *args, **kwargs):
            # Note that `self` is a `web.View` object.
            query = self.request.rel_url.query
            # Decode POST parameters
            if self.request.body_exists and self.request.content_type.endswith("json"):
                data = await self.request.json()
            else:
                data = {}
            # Check and get all parameters
            vals = {}
            for name in names:
                val = data.get(name, None) or query.get(name, None)
                if not val:
                    raise web.HTTPForbidden(
                        reason="{} parameter is required".format(name)
                    )
                vals[name] = val
            # Forward parameters to wrapped functions
            return await fun(self, *args, required_params=vals, **kwargs)

        return run

    return wrapper if not _fun else wrapper(_fun)


def APITagsView(*, db: monad.Database) -> web.View:
    class Wrapper(web.View, aiohttp_cors.CorsViewMixin):
        async def get(self):
            return web.Response(
                text=json.dumps(
                    {"result": "Ok", "params": db.get_tags()}, ensure_ascii=False
                )
            )

    return Wrapper


def APINotesView(*, db: monad.Database) -> web.View:
    class Wrapper(web.View, aiohttp_cors.CorsViewMixin):
        async def get(self):
            return web.Response(
                text=json.dumps(
                    {"result": "Ok", "params": db.get_notes()}, ensure_ascii=False
                )
            )

    return Wrapper


def APINotesByTagsView(*, db: monad.Database) -> web.View:
    class Wrapper(web.View, aiohttp_cors.CorsViewMixin):
        async def get(self):
            tags = self.request.match_info["tags"].split(":")
            return web.Response(
                text=json.dumps(
                    {"result": "Ok", "params": db.get_notes_by_tags(tags)}, ensure_ascii=False
                )
            )

    return Wrapper


def APINoteByIdView(*, db: monad.Database) -> web.View:
    class Wrapper(web.View, aiohttp_cors.CorsViewMixin):
        async def get(self):
            id = int(self.request.match_info["id"])
            note = db.get_note_by_id(id)
            if not note:
                return web.HTTPNotFound()

            return web.Response(
                text=json.dumps(
                    {"result": "Ok", "params": note}, ensure_ascii=False
                )
            )

    return Wrapper


def IndexView(*, api_base_url: str, cdn_url: str) -> web.View:
    class Wrapper(web.View):
        @aiohttp_jinja2.template('index.html')
        async def get(self, **_):
            return {"api_base_url": api_base_url, "cdn_url": cdn_url}

    return Wrapper


def Application(
    *args, db: str, jinja2_templates_dir: str, cdn_url: str, swagger_yml: str, swagger_url: str = None, api_base_url: str = None, base_url: str = None, **kwargs
):
    db = monad.Database(db)
    db.load_notes()

    app = web.Application(*args, **kwargs)

    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(jinja2_templates_dir)
    )

    base_url = base_url or "/"
    if base_url[-1] != "/":
        base_url += "/"

    api_base_url = api_base_url or "/"
    if api_base_url[-1] != "/":
        api_base_url += "/"

    cors = aiohttp_cors.setup(
        app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True, expose_headers="*", allow_headers="*",
            )
        },
    )

    # Web
    app.router.add_view(base_url, IndexView(api_base_url=api_base_url, cdn_url=cdn_url))

    # API
    cors.add(app.router.add_view(api_base_url + "tags", APITagsView(db=db)))
    cors.add(app.router.add_view(api_base_url + "tags/", APITagsView(db=db)))
    cors.add(app.router.add_view(api_base_url + "notes", APINotesView(db=db)))
    cors.add(app.router.add_view(api_base_url + "notes/", APINotesView(db=db)))
    cors.add(app.router.add_view(api_base_url + "notes/{tags:(([%a-zA-Z][-_%a-zA-Z0-9]*):?)+}", APINotesByTagsView(db=db)))
    cors.add(app.router.add_view(api_base_url + "notes/{tags:(([%a-zA-Z][-_%a-zA-Z0-9]*):?)+}/", APINotesByTagsView(db=db)))
    cors.add(app.router.add_view(api_base_url + "notes/{id:[0-9]+}", APINoteByIdView(db=db)))
    cors.add(app.router.add_view(api_base_url + "notes/{id:[0-9]+}/", APINoteByIdView(db=db)))

    aiohttp_swagger.setup_swagger(
        app, swagger_from_file=swagger_yml, swagger_url=swagger_url
    )

    return app
