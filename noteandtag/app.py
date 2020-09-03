import json
from aiohttp import web
import aiohttp_cors
import aiohttp_swagger
import aiohttp_jinja2
import jinja2
from typing import Callable, Any, List
from noteandtag import monad


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

        async def put(self):
            data = await self.request.json()
            note = db.add_note(data["data"])
            if not note:
                return web.HTTPInternalServerError()

            db.save_notes()

            return web.Response(
                text=json.dumps({"result": "Ok", "params": note}, ensure_ascii=False)
            )

    return Wrapper


def APINotesByTagsView(*, db: monad.Database) -> web.View:
    class Wrapper(web.View, aiohttp_cors.CorsViewMixin):
        async def get(self):
            tags = self.request.match_info["tags"].split(":")
            return web.Response(
                text=json.dumps(
                    {"result": "Ok", "params": db.get_notes_by_tags(tags)},
                    ensure_ascii=False,
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
                text=json.dumps({"result": "Ok", "params": note}, ensure_ascii=False)
            )

        async def post(self):
            id = int(self.request.match_info["id"])
            data = await self.request.json()
            note = db.update_note(id, data["data"])
            if not note:
                return web.HTTPNotFound()

            db.save_notes()

            return web.Response(
                text=json.dumps({"result": "Ok", "params": note}, ensure_ascii=False)
            )

    return Wrapper


def IndexView(*, api_base_url: str, cdn_url: str, default_theme: str) -> web.View:
    class Wrapper(web.View):
        @aiohttp_jinja2.template("index.html")
        async def get(self, **_):
            return {
                "api_base_url": api_base_url,
                "cdn_url": cdn_url,
                "theme": self.request.rel_url.query.get("theme", default_theme),
            }

    return Wrapper


def Application(
    *args,
    db: str,
    jinja2_templates_dir: str,
    cdn_url: str,
    default_theme: str,
    swagger_yml: str = None,
    swagger_url: str = None,
    static_dir: str = None,
    api_base_url: str = None,
    base_url: str = None,
    **kwargs
):
    """Create the server application.

    :param args: additional args to **aiohttp**
    :param db: path to local notes database
    :param jinja2_templates_dir: directory containing jinja2 templates
    :param cdn_url: URL for serving static files
    :param default_theme: default selected CSS theme
    :param swagger_yml:
    :param swagger_url:
    :param static_dir: directory containing static files
    :param api_base_url:
    :param base_url:
    :param kargs: additional kargs to **aiohttp**
    :return: application
    """
    db = monad.Database(db)
    db.load_notes()

    app = web.Application(*args, **kwargs)

    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(jinja2_templates_dir))

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
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
        },
    )

    if static_dir is not None:
        app.add_routes([web.static(cdn_url, static_dir)])

    # Web
    app.router.add_view(
        base_url,
        IndexView(
            api_base_url=api_base_url, cdn_url=cdn_url, default_theme=default_theme
        ),
    )

    # API
    cors.add(app.router.add_view(api_base_url + "tags", APITagsView(db=db)))
    cors.add(app.router.add_view(api_base_url + "tags/", APITagsView(db=db)))
    cors.add(app.router.add_view(api_base_url + "notes", APINotesView(db=db)))
    cors.add(app.router.add_view(api_base_url + "notes/", APINotesView(db=db)))
    cors.add(
        app.router.add_view(
            api_base_url + "notes/{tags:(([%a-zA-Z][-_%a-zA-Z0-9]*):?)+}",
            APINotesByTagsView(db=db),
        )
    )
    cors.add(
        app.router.add_view(
            api_base_url + "notes/{tags:(([%a-zA-Z][-_%a-zA-Z0-9]*):?)+}/",
            APINotesByTagsView(db=db),
        )
    )
    cors.add(
        app.router.add_view(api_base_url + "notes/{id:[0-9]+}", APINoteByIdView(db=db))
    )
    cors.add(
        app.router.add_view(api_base_url + "notes/{id:[0-9]+}/", APINoteByIdView(db=db))
    )

    if swagger_yml is not None and swagger_url is not None:
        aiohttp_swagger.setup_swagger(
            app, swagger_from_file=swagger_yml, swagger_url=swagger_url
        )

    return app
