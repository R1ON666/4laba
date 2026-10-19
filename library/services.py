"""Бизнес-логика работы с книгами в БД."""
from .models import Book


def _norm(text):
    """Сравнение без учёта регистра и лишних пробелов (SQLite не умеет это для кириллицы)."""
    return " ".join(str(text).split()).casefold()


def find_duplicate(data, exclude_pk=None):
    """Ищет в БД такую же книгу. Возвращает (книга, причина) или None.

    Дубликатом считается книга с тем же ISBN либо с тем же названием, автором и годом.
    """
    qs = Book.objects.all()
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)

    same_isbn = qs.filter(isbn=data["isbn"]).first()
    if same_isbn:
        return same_isbn, "ISBN"

    title, author = _norm(data["title"]), _norm(data["author"])
    for book in qs.filter(year=data["year"]):
        if _norm(book.title) == title and _norm(book.author) == author:
            return book, "название, автор и год"
    return None


def duplicate_message(duplicate):
    book, reason = duplicate
    return (f"Такая книга уже есть в базе данных (совпадает: {reason}): "
            f"«{book.title}», {book.author}, {book.year}. Запись не добавлена.")
