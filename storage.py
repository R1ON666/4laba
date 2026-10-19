"""Работа с JSON-файлами: чтение, валидация, запись. Имена файлов генерирует сервер."""
import datetime
import json
import os
import re
import uuid

from django.conf import settings

from forms import BookForm

FILE_ID_RE = re.compile(r"^[0-9a-f]{32}$")


def validate_books_payload(data):
    """Проверяет разобранный JSON. Возвращает (список_книг, список_ошибок)."""
    if isinstance(data, dict) and "books" in data:
        items = data["books"]
        if not isinstance(items, list):
            return [], ['Поле "books" должно быть списком.']
    elif isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = [data]
    else:
        return [], ["Корневой элемент должен быть объектом или списком."]

    if not items:
        return [], ["В файле нет ни одной книги."]
    if len(items) > settings.MAX_BOOKS_PER_FILE:
        return [], [f"Слишком много книг (максимум {settings.MAX_BOOKS_PER_FILE})."]

    books, errors = [], []
    for i, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            errors.append(f"Книга №{i}: элемент должен быть объектом.")
            continue
        form = BookForm(item)
        if form.is_valid():
            books.append(form.cleaned_data)
        else:
            for field, errs in form.errors.items():
                for e in errs:
                    errors.append(f"Книга №{i}, поле «{field}»: {e}")
    return (books if not errors else []), errors


def parse_json_file(path):
    """Читает и валидирует файл. Возвращает (книги, ошибки)."""
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except UnicodeDecodeError:
        return [], ["Файл не в кодировке UTF-8."]
    except (json.JSONDecodeError, RecursionError) as exc:
        return [], [f"Невалидный JSON: {exc}"]
    except OSError as exc:
        return [], [f"Ошибка чтения файла: {exc}"]
    return validate_books_payload(data)


def new_file_path():
    settings.BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex
    return file_id, settings.BOOKS_DIR / f"{file_id}.json"


def save_books(books):
    """Атомарно записывает книги в новый JSON-файл."""
    file_id, target = new_file_path()
    tmp = target.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"books": books}, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, target)
    return file_id


def list_book_files():
    """Все существующие JSON-файлы папки (новые первыми)."""
    if not settings.BOOKS_DIR.is_dir():
        return []
    result = []
    for p in settings.BOOKS_DIR.glob("*.json"):
        if not (p.is_file() and FILE_ID_RE.match(p.stem)):
            continue
        st = p.stat()
        books, errors = parse_json_file(p)
        result.append({
            "id": p.stem, "books": books, "errors": errors, "size": st.st_size,
            "modified": datetime.datetime.fromtimestamp(st.st_mtime, tz=datetime.timezone.utc),
        })
    result.sort(key=lambda f: f["modified"], reverse=True)
    return result
