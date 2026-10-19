import json

from django.conf import settings
from django.contrib import messages
from django.db import IntegrityError
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from . import storage
from .forms import AddBookForm, UploadForm
from .models import Book
from .services import duplicate_message, find_duplicate


def index(request):
    files = storage.list_book_files()
    total = sum(len(f["books"]) for f in files)
    return render(request, "library/index.html", {"files": files, "total_books": total})


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
