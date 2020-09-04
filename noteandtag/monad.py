__all__ = ["Database"]
import yaml
import shutil
import os
import tempfile
from functools import wraps


def _filtering(fun):
    @wraps(fun)
    def wrapper(*args, filters, **kwargs):
        def int_or(value, default):
            return default if value is None else value

        return fun(
            *args,
            filters={
                "offset": int_or(filters.get("offset", None), 0),
                "limit": min(int_or(filters.get("limit", None), 50), 50),
                "sort": filters.get("sort", [])
            },
            **kwargs
        )

    return wrapper


class Database:
    def __init__(self, filename: str):
        self._filename = filename
        self._notes = []

    @_filtering
    def get_notes(self, *, filters):
        return self._notes[filters["offset"]:filters["limit"]], len(self._notes)

    @_filtering
    def get_tags(self, *, filters):
        d = {}

        for note in self._notes:
            for _ in note["tags"]:
                d[_] = d.get(_, 0) + 1

        items = [{"name": tag, "total": total} for tag, total in d.items()]
        return items[filters["offset"]:filters["limit"]], len(items)

    @_filtering
    def get_notes_by_tags(self, tags, *, filters):
        def matches(note):
            for _ in note["tags"]:
                if _ in tags:
                    return True

            return False

        items = list(_ for _ in self._notes if matches(_))
        return items[filters["offset"]:filters["limit"]], len(items)

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

    def load_notes(self):
        """Load notes from external YAML file.

        :return: notes as JSON dicts
        """
        if os.path.isfile(self._filename):
            with open(self._filename, "rb") as f:
                content = f.read().decode()
                self._notes = list(yaml.safe_load_all(content))

        return self._notes

    def save_notes(self):
        """Save notes to external YAML file."""
        tmp = tempfile.NamedTemporaryFile(mode="w+b", delete=False)
        try:
            content = yaml.safe_dump_all(self._notes, allow_unicode=True).encode()
            tmp.write(content)
            tmp.close()

            shutil.copy(tmp.name, self._filename)
        finally:
            if not tmp.closed:
                tmp.close()
            os.remove(tmp.name)
