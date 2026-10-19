import json

from django.conf import settings
from django.contrib import messages
from django.db import IntegrityError
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from . import storage
from .forms import AddBookForm, BookForm, UploadForm
from .models import Book
from .services import duplicate_message, find_duplicate


def index(request):
    source = request.GET.get("source", "db")
    if source not in ("db", "files"):
        source = "db"
    context = {"source": source}
    if source == "files":
        files = storage.list_book_files()
        context.update(files=files, total_books=sum(len(f["books"]) for f in files))
    else:
        books = Book.objects.all()
        context.update(books=books, total_books=len(books))
    return render(request, "library/index.html", context)


def add_book(request):
    form = AddBookForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = {k: v for k, v in form.cleaned_data.items() if k != "destination"}
        if form.cleaned_data["destination"] == "db":
            duplicate = find_duplicate(data)
            if duplicate:
                # дубликат: не сохраняем, остаёмся на форме с введёнными данными
                messages.warning(request, duplicate_message(duplicate))
            else:
                try:
                    Book.objects.create(**data)
                except IntegrityError:   # одновременный запрос успел добавить такой же ISBN
                    messages.warning(request, "Книга с таким ISBN уже есть в базе данных. Запись не добавлена.")
                else:
                    messages.success(request, "Книга сохранена в базу данных.")
                    return redirect(f"{reverse('index')}?source=db")
        else:
            storage.save_books([data])
            messages.success(request, "Книга сохранена в JSON-файл.")
            return redirect(f"{reverse('index')}?source=files")
    return render(request, "library/add.html", {"form": form})


def upload(request):
    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        uploaded = form.cleaned_data["file"]
        _, target = storage.new_file_path()      # оригинальное имя игнорируем
        with open(target, "xb") as fh:
            for chunk in uploaded.chunks():
                fh.write(chunk)
        books, errors = storage.parse_json_file(target)
        if errors:
            target.unlink(missing_ok=True)       # невалидный файл удаляем
            messages.error(request, "Файл невалиден и был удалён: " + " ".join(errors[:5])
                           + (" ..." if len(errors) > 5 else ""))
        else:
            messages.success(request, f"Файл загружен. Книг в файле: {len(books)}.")
            return redirect("index")
    return render(request, "library/upload.html", {"form": form})


def download(request, file_id):
    if not storage.FILE_ID_RE.match(file_id):
        raise Http404
    target = settings.BOOKS_DIR / f"{file_id}.json"
    if not target.is_file():
        raise Http404("Файл не найден")
    return FileResponse(open(target, "rb"), as_attachment=True,
                        filename=f"books_{file_id[:8]}.json", content_type="application/json")


def export_all(request):
    books = [b for f in storage.list_book_files() for b in f["books"]]
    if not books:
        messages.info(request, "Экспортировать нечего: на сервере нет ни одной книги.")
        return redirect("index")
    body = json.dumps({"books": books}, ensure_ascii=False, indent=2)
    resp = HttpResponse(body, content_type="application/json; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="all_books.json"'
    return resp


SEARCH_FIELDS = ("title", "author", "isbn", "genre", "description")


@require_GET
def book_search(request):
    """AJAX-поиск по текстовым полям. Возвращает JSON: количество и готовый HTML строк таблицы."""
    query = " ".join(request.GET.get("q", "")[:100].split()).casefold()
    books = list(Book.objects.all())
    if query:
        # SQLite сравнивает без учёта регистра только латиницу, поэтому фильтруем через casefold()
        books = [b for b in books if any(query in getattr(b, f).casefold() for f in SEARCH_FIELDS)]
    html = render_to_string("library/_db_rows.html", {"books": books}, request=request)
    return JsonResponse({"count": len(books), "html": html})


BOOK_FIELDS = ("title", "author", "year", "isbn", "genre", "pages", "description")


def book_edit(request, pk):
    """Редактирование записи из БД с той же валидацией, что и при добавлении."""
    book = get_object_or_404(Book, pk=pk)
    form = BookForm(request.POST or None, initial={f: getattr(book, f) for f in BOOK_FIELDS})
    if request.method == "POST" and form.is_valid():
        duplicate = find_duplicate(form.cleaned_data, exclude_pk=book.pk)
        if duplicate:
            form.add_error(None, duplicate_message(duplicate, outcome="Изменения не сохранены."))
        else:
            for name, value in form.cleaned_data.items():
                setattr(book, name, value)
            try:
                book.save()
            except IntegrityError:
                form.add_error("isbn", "Книга с таким ISBN уже есть в базе данных.")
            else:
                messages.success(request, f"Изменения сохранены: «{book.title}».")
                return redirect(f"{reverse('index')}?source=db")
    return render(request, "library/edit.html", {"form": form, "book": book})


@require_POST
def book_delete(request, pk):
    """Удаление записи. Только POST (защищено CSRF); для AJAX отвечает JSON."""
    book = get_object_or_404(Book, pk=pk)
    message = f"Книга «{book.title}» удалена."
    book.delete()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "message": message})
    messages.success(request, message)
    return redirect(f"{reverse('index')}?source=db")
