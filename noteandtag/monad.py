__all__ = ["Database"]
import yaml
import shutil
import os
import tempfile
import sqlite3
from functools import wraps
from typing import List, Dict, Any


def _filtering(fun):
    @wraps(fun)
    def wrapper(*args, filters=None, **kwargs):
        def get_attr(name, default):
            value = filters.get(name, None) if filters else None
            return value if value is not None else default

        return fun(
            *args,
            filters={
                "offset": int(get_attr("offset", 0)),
                "limit": min(int(get_attr("limit", 50)), 50),
                "sort": get_attr("sort", []),
            },
            **kwargs
        )

    return wrapper


class Database:
    def __init__(self, filename: str):
        self._filename = filename
        self._conn = None
        self._query("SELECT * FROM note")

    def _query(self, stmt, args=None):
        if self._conn is None:
            self._conn = Database._connect(self._filename)

        cur = self._conn.cursor()
        return cur.execute(stmt)

    @staticmethod
    def _connect(filename):
        found = os.path.isfile(filename)

        conn = sqlite3.connect(filename)

        if not found:
            Database._setup(conn=conn)

        return conn

    @staticmethod
    def _setup(conn):
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE "note" (
                "id" INTEGER NOT NULL,
                "label"	TEXT NOT NULL,
                "author" TEXT NOT NULL,
                "body" TEXT NOT NULL,
                PRIMARY KEY("id" AUTOINCREMENT)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE "note_tag" (
                "noteid" INTEGER NOT NULL,
                "label" TEXT NOT NULL,
                PRIMARY KEY("noteid", "label"),
                FOREIGN KEY("noteid") REFERENCES note("id")
            )
            """
        )

    @_filtering
    def get_notes(
        self,
        *,
        filters: Dict[str, Any],
        ids: List[str] = None,
        label: str = None,
        body: str = None,
        tags: List[str] = None
    ):
        items = self._query(
            """
            SELECT *
            FROM note
            """
        )
        print(items)
        def _matches(note):
            import re

            if ids and note["id"] not in ids:
                return False

            if label is not None and not re.search(label, note["label"], re.IGNORECASE):
                return False

            if body is not None and not re.search(body, note["body"], re.IGNORECASE):
                return False

            if tags:
                for tag in tags:
                    if tag not in note["tags"]:
                        return False

            return True

        items = [_ for _ in self._notes if _matches(_)]

        for criteria in filters["sort"]:
            items.sort(
                key=lambda _: _[criteria["field"]], reverse=criteria["order"] == "desc"
            )

        return items[filters["offset"] : filters["limit"]], len(items)

    @_filtering
    def get_tags(self, *, filters):
        d = {}

        for note in self._notes:
            for _ in note["tags"]:
                d[_] = d.get(_, 0) + 1

        items = [{"name": tag, "total": total} for tag, total in d.items()]
        return items[filters["offset"] : filters["limit"]], len(items)

    @_filtering
    def get_notes_by_tags(self, tags, *, filters):
        def matches(note):
            for _ in note["tags"]:
                if _ in tags:
                    return True

            return False

        items = list(_ for _ in self._notes if matches(_))
        return items[filters["offset"] : filters["limit"]], len(items)

    def get_note_by_id(self, id):
        for _ in self._notes:
            if _["id"] == id:
                return _

        return None

    def update_note(self, id, data):
        data = yaml.safe_load(yaml.safe_dump(data))

        for _ in self._notes:
            if _["id"] == id:
                _.update(data)
                return _

        return False

    def add_note(self, data):
        id = (max(int(_["id"]) for _ in self._notes) + 1) if self._notes else 1
        data["id"] = id
        data = yaml.safe_load(yaml.safe_dump(data))
        self._notes.append(data)

        return data
