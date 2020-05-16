__all__ = ["setup_logging", "run", "main"]
import os
import sys
import argparse
import json
from aiohttp import web
import logging
from nodeandtag.app import Application
from nodeandtag import configuration


def setup_logging(
    *,
    access_logfile=None,
    access_maxbytes=None,
    access_backupcount=None,
    error_logfile=None,
    error_maxbytes=None,
    error_backupcount=None
):
    """Setup logging handlers.

    This setup two `RotatingFileHandler` for `aiohttp.access` and `aiohttp.server` logs.

    :param access_logfile: path for access logfile or `None`
    :param access_maxbytes: max bytes per access logfile
    :param access_backupcount: max number of access logfile to keep
    :param error_logfile: path for error logfile or `None`
    :param error_maxbytes: max bytes per error logfile
    :param error_backupcount: max number of error logfile to keep
    """
    from logging.handlers import RotatingFileHandler

    if access_logfile:
        logging.getLogger("aiohttp.access").addHandler(
            RotatingFileHandler(
                access_logfile,
                maxBytes=access_maxbytes,
                backupCount=access_backupcount,
            )
        )
    if error_logfile:
        logging.getLogger("aiohttp.server").addHandler(
            RotatingFileHandler(
                error_logfile, maxBytes=error_maxbytes, backupCount=error_backupcount,
            )
        )


def run(*, db: str, jinja2_templates_dir: str, cdn_url:str, swagger_yml: str, swagger_url: str, api_base_url: str, base_url: str, port: int):
    app = Application(
        db=db,
        jinja2_templates_dir=jinja2_templates_dir,
        cdn_url=cdn_url,
        swagger_yml=swagger_yml, swagger_url=swagger_url, api_base_url=api_base_url, base_url=base_url
    )
    web.run_app(app, port=port)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="Service", description="Help")
    parser.add_argument("directory", type=str, help="config directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbosity level")
    args = parser.parse_args(args=argv)

    config_dir = args.directory
    if not os.path.isdir(config_dir):
        raise NotADirectoryError(config_dir)

    config = configuration.load(os.path.join(config_dir, "config.cnf"))

    logging.basicConfig(level=logging.INFO)

    setup_logging(
        access_logfile=config["logging"].get("access-logfile", None),
        access_maxbytes=int(config["logging"].get("access-maxbytes", None)),
        access_backupcount=int(config["logging"].get("access-backupcount", None)),
        error_logfile=config["logging"].get("error-logfile", None),
        error_maxbytes=int(config["logging"].get("error-maxbytes", None)),
        error_backupcount=int(config["logging"].get("error-backupcount", None)),
    )

    run(
        db=config["service"]["db"],
        jinja2_templates_dir=config["service"]["jinja2-templates-dir"],
        cdn_url=config["service"]["cdn-url"],
        swagger_yml=config["service"]["swagger-yml"],
        swagger_url=config["service"]["swagger-url"],
        api_base_url=config["service"]["api-base-url"],
        base_url=config["service"]["base-url"],
        port=int(config["service"]["port"])
    )


if __name__ == "__main__":
    main(sys.argv)
