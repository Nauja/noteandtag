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
            **kwargs,
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

    def query_row(self, stmt, args=None):
        self._cur.execute(stmt, args or [])
        return self._cur.fetchone()

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

    """Get a list of notes matching multiple filters.

    Filters have no effect when requesting by ids.
    :param filters: pagination and sort filters
    :param ids: list of notes ids
    :param label: only notes matching this label
    :param body: only notes matching this body
    :param tags: only notes matching those tags
    :return: a tuple (notes, total)
    """

    @_filtering
    def get_notes(
        self,
        *,
        filters: Dict[str, Any],
        ids: List[str] = None,
        label: str = None,
        body: str = None,
        tags: List[str] = None,
    ):
        # Fetch notes by ids only
        if ids:
            notes = self._get_notes_by_ids(ids)
            return notes, len(notes)

        # Fetch all notes
        return self._search_notes(filters=filters, label=label, body=body, tags=tags)

    """Return only notes from a list of ids.

    This may return less notes than ids if some ids don't exist in DB.
    :param ids: list of ids
    :return: notes
    """

    def _get_notes_by_ids(self, ids):
        return [_ for _ in (self.get_note_by_id(_) for _ in ids) if _]

    """Get a list of notes matching multiple filters.

    This is equivalent to:

    .. code-block:: python

        SELECT *
        FROM note
        WHERE label LIKE '%...%'
        AND body LIKE '%...%'
        LIMIT offset, limit

    Notes are filtered by tags afterward.

    :param filters: pagination and sort filters
    :param label: only notes matching this label
    :param body: only notes matching this body
    :param tags: only notes matching those tags
    :return: a tuple (notes, total)
    """

    def _search_notes(
        self,
        *,
        filters: Dict[str, Any],
        label: str = None,
        body: str = None,
        tags: List[str] = None,
    ):
        tags = tags if tags else []
        conditions = []
        args = []

        # Must contain a label
        if label is not None:
            conditions.append("label LIKE ?")
            args.append(f"%{label}%")

        # Must contain a body
        if body is not None:
            conditions.append("body LIKE ?")
            args.append(f"%{body}%")

        stmt = """
            FROM note
            {}
        """.format(
            "WHERE {}".format(" AND ".join(conditions)) if conditions else ""
        )

        with self._cursor() as cur:
            total = cur.query_value(
                """
                SELECT COUNT(id)
                {}
                """.format(
                    stmt
                ),
                args,
            )

            notes = cur.query(
                """
                SELECT *
                {}
                LIMIT ?, ?
                """.format(
                    stmt
                ),
                args + [filters["offset"], filters["limit"]],
            )

        # Fetch tags
        for _ in notes:
            _["tags"] = self.get_note_tags(_["id"])

        # Keep only notes matching tags
        size = len(notes)
        notes = [_ for _ in notes if all(tag in _["tags"] for tag in tags)]
        total -= size - len(notes)

        return notes, total

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
                """.format(
                    stmt
                )
            )

            items = cur.query(
                """
                SELECT label AS name, COUNT(noteid) AS total
                {}
                LIMIT ?, ?
                """.format(
                    stmt
                ),
                (filters["offset"], filters["limit"]),
            )

        return items, total

    """Get a single note by id.
    :param id: note id
    :return: note or None
    """

    def get_note_by_id(self, id):
        with self._cursor() as cur:
            data = cur.query_row(
                """
                SELECT *
                FROM note
                WHERE id=?
                """,
                (id,),
            )

        if not data:
            return None

        data["tags"] = self.get_note_tags(id)
        return data

    def get_note_tags(self, id):
        with self._cursor() as cur:
            return [
                _["label"]
                for _ in cur.query(
                    """
                SELECT label
                FROM note_tag
                WHERE noteid=?
                """,
                    (id,),
                )
            ]

    """Check if a note exists in DB.
    :param id: note id to check
    :return: if it exists
    """

    def has_note(self, id):
        with self._cursor() as cur:
            return (
                cur.query_value(
                    """
                SELECT id
                FROM note
                WHERE id=?
                """,
                    (id,),
                )
                is not None
            )

    """Update an existing note.
    :param id: note id
    :param data: new note data
    :return: updated note
    """

    def update_note(self, id, data):
        data = yaml.safe_load(yaml.safe_dump(data))

        if not self.has_note(id):
            return None

        self.delete_note(id)
        return self.add_note(data, id=id)

    """Add a new note to DB.
    :param data: new note data
    :param id: new note id
    :return: added note
    """

    def add_note(self, data, *, id=None):
        data = yaml.safe_load(yaml.safe_dump(data))

        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO note
                (id, label, author, body)
                VALUES (?, ?, ?, ?)
                """,
                (
                    None if id is None else id,
                    data["label"],
                    data["author"],
                    data["body"],
                ),
            )

            data["id"] = cur.lastrowid if id is None else id

            for _ in data["tags"]:
                cur.execute(
                    """
                    INSERT INTO note_tag
                    (noteid, label)
                    VALUES (?, ?)
                    """,
                    (data["id"], _),
                )

        return data

    """Delete a note from DB.
    :param id: note id
    """

    def delete_note(self, id):
        with self._cursor() as cur:
            cur.execute("DELETE FROM note_tag WHERE noteid=?", (id,))
            cur.execute("DELETE FROM note WHERE id=?", (id,))
