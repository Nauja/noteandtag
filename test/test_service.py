# -*- coding: utf-8 -*-
__all__ = ["ServiceTestCase"]
import os
import unittest
import json
import sqlite3
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from noteandtag import configuration, Application

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CONFIG_CNF = os.path.join(DATA_DIR, "config.cnf")


"""Create a new note object.
"""


def note(*, id=0, label="", body="", author="", tags=[]):
    return {"id": id, "label": label, "author": author, "body": body, "tags": tags}


class ServiceTestCase(AioHTTPTestCase):
    async def get_application(self):
        config = configuration.load(CONFIG_CNF)
        self.db_path = config["service"]["db"]

        return Application(
            db=config["service"]["db"],
            default_theme=config["service"]["default-theme"],
            jinja2_templates_dir=config["service"]["jinja2-templates-dir"],
            cdn_url=config["service"]["cdn-url"],
            static_dir=config["service"].get("static-dir", None),
            swagger_yml=config["service"].get("swagger-yml", None),
            swagger_url=config["service"].get("swagger-url", None),
            api_base_url=config["service"]["api-base-url"],
            base_url=config["service"]["base-url"],
        )

    @unittest_run_loop
    async def test_doc(self):
        resp = await self.client.request("GET", "/api/v1/doc")
        assert resp.status == 200

    @unittest_run_loop
    async def test_api(self):
        self._clean_db()

        # Try to get non-existing note
        await self._get_note(0, status=404)

        # Try to update a non-existing note
        await self._update_note(note(), status=404)

        # Add a new note
        new_note = await self._add_note(
            note(label="test", author="test", body="test", tags=["a", "b"])
        )
        assert new_note["id"] > 0

        # Check the note has been created
        fetched_note = await self._get_note(new_note["id"])
        assert fetched_note["id"] == new_note["id"]
        assert fetched_note["label"] == "test"
        assert len(fetched_note["tags"]) == 2

        # Update the note
        new_note["label"] = "test2"
        await self._update_note(new_note)

        # Check the note has been updated
        fetched_note = await self._get_note(new_note["id"])
        assert fetched_note["id"] == new_note["id"]
        assert fetched_note["label"] == "test2"
        assert len(fetched_note["tags"]) == 2

        # Add a second note
        other_note = await self._add_note(
            note(label="test", author="test", body="test", tags=["b", "c"])
        )
        assert other_note["id"] > 0
        assert other_note["id"] != new_note["id"]

        # Check tags
        tags = await self._get_tags()
        assert len(tags) == 3

        # Get all notes
        notes = await self._get_notes()
        assert len(notes) == 2
        for _ in notes:
            assert len(_["tags"]) == 2

        # Get notes by ids
        notes = await self._get_notes(
            params={"ids": f"{new_note['id']},{other_note['id']}"}
        )
        assert len(notes) == 2

        # Get notes by filters
        notes = await self._get_notes(
            params={"label": "est", "body": "tes", "tags": "b"}
        )
        assert len(notes) == 2

        # Get only one note
        notes = await self._get_notes(params={"tags": "a"})
        assert len(notes) == 1

    """This will clear all notes from test DB.
    """

    def _clean_db(self):
        if os.path.isfile(self.db_path):
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("DELETE FROM note_tag")
            cur.execute("DELETE FROM note")
            cur.execute("COMMIT")
            conn.close()

    """Send PUT request to add a new note.
    """

    async def _add_note(self, note, *, status=200):
        resp = await self.client.put("/api/v1/notes", data=json.dumps({"data": note}))
        assert resp.status == status
        return json.loads(await resp.read())

    """Send GET request to get a note by id.
    """

    async def _get_note(self, id, *, status=200):
        resp = await self.client.get(f"/api/v1/notes/{id}")
        assert resp.status == status
        if resp.status == 200:
            return json.loads(await resp.read())
        return None

    """Send GET request to get all notes.
    """

    async def _get_notes(self, *, params={}, status=200):
        resp = await self.client.get(f"/api/v1/notes", params=params)
        assert resp.status == status
        if resp.status == 200:
            return json.loads(await resp.read())
        return None

    """Send PUT request to update a note.
    """

    async def _update_note(self, note, *, status=200):
        resp = await self.client.post(
            f"/api/v1/notes/{note['id']}", data=json.dumps({"data": note})
        )
        assert resp.status == status
        if resp.status == 200:
            return json.loads(await resp.read())
        return None

    """Send GET request to get tags.
    """

    async def _get_tags(self):
        resp = await self.client.get(f"/api/v1/tags")
        assert resp.status == 200
        return json.loads(await resp.read())


if __name__ == "__main__":
    unittest.main()
