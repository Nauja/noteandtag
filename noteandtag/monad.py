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


class _CursorContext:
    def __init__(self, conn):
        self._conn = conn

    def __enter__(self):
        self._cur = self._conn.cursor()
        return self

    def __exit__(self, *args, **kwargs):
        pass

    def query(self, stmt, args=None):
        self._cur.execute(stmt, args or [])
        return self._cur.fetchall()

    def query_value(self, stmt, args=None):
        self._cur.execute(stmt, args or [])
        row = self._cur.fetchone()
        if row is None:
            return None
        for k, v in row.items():
            return v
        return None

    def execute(self, stmt, args=None):
        self._cur.execute(stmt, args or [])
        self._conn.commit()

    @property
    def lastrowid(self):
        return self._cur.lastrowid


class Database:
    def __init__(self, filename: str):
        self._filename = filename
        self._conn = None

        with self._cursor() as cur:
            cur.query("SELECT * FROM note")

    @staticmethod
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def _cursor(self):
        if self._conn is None:
            self._conn = Database._connect(self._filename)
            self._conn.row_factory = Database.dict_factory

        return _CursorContext(self._conn)

    @staticmethod
    def _connect(filename):
        found = os.path.isfile(filename)

        conn = sqlite3.connect(filename)

        if not found:
            Database._setup(conn=conn)

        return conn

    @staticmethod
    def _setup(conn):
        with _CursorContext(conn) as cur:
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
        stmt = """
            FROM note
        """

        with self._cursor() as cur:
            total = cur.query_value(
                """
                SELECT COUNT(id)
                {}
                """.format(stmt)
            )

            items = cur.query(
                """
                SELECT *
                {}
                LIMIT ?, ?
                """.format(stmt),
                (filters["offset"], filters["limit"])
            )
        
        return items, total

    @_filtering
    def get_tags(self, *, filters):
        stmt = """
            FROM note_tag
            GROUP BY label
        """

        with self._cursor() as cur:
            total = cur.query_value(
                """
                SELECT COUNT(label)
                {}
                """.format(stmt)
            )

            items = cur.query(
                """
                SELECT label, SUM(noteid) AS total
                {}
                LIMIT ?, ?
                """.format(stmt),
                (filters["offset"], filters["limit"])
            )
            print(items, total)

        return items, total

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
        data = yaml.safe_load(yaml.safe_dump(data))

        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO note
                (label, author, body)
                VALUES (?, ?, ?)
                """,
                (
                    data["label"],
                    data["author"],
                    data["body"]
                )
            )

            data["id"] = cur.lastrowid

            for _ in data["tags"]:
                cur.execute(
                    """
                    INSERT INTO note_tag
                    (noteid, label)
                    VALUES (?, ?)
                    """,
                    (
                        data["id"],
                        _
                    )
                )

        return data
