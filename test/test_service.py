# -*- coding: utf-8 -*-
__all__ = ["ServiceTestCase"]
import os
import unittest
import json
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from noteandtag import configuration, Application

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CONFIG_CNF = os.path.join(DATA_DIR, "config.cnf")


class ServiceTestCase(AioHTTPTestCase):
    async def get_application(self):
        config = configuration.load(CONFIG_CNF)

        return Application(
            db=config["service"]["db"],
            jinja2_templates_dir=config["service"]["jinja2-templates-dir"],
            cdn_url=config["service"]["cdn-url"],
            static_dir=config["service"].get("static-dir", None),
            swagger_yml=config["service"].get("swagger-yml", None),
            swagger_url=config["service"].get("swagger-url", None),
            api_base_url=config["service"]["api-base-url"],
            base_url=config["service"]["base-url"]
        )

    @unittest_run_loop
    async def test_doc(self):
        resp = await self.client.request("GET", "/api/v1/doc")
        assert resp.status == 200

    @unittest_run_loop
    async def test_api(self):
        resp = await self.client.request("GET", "/api/v1/tags")
        assert resp.status == 200


if __name__ == "__main__":
    unittest.main()
