import json
import re
import shutil
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from . import storage
from .models import Book

ISBN_A = "978-5-17-090333-7"   # валидные ISBN-13 (контрольная сумма сходится)
ISBN_B = "978-3-16-148410-0"


def book_data(**override):
    data = dict(title="Мастер и Маргарита", author="М. Булгаков", year=1967,
                isbn=ISBN_A, genre="Роман", pages=480, description="")
    data.update(override)
    return data


def make_book(**override):
    data = book_data(**override)
    data["isbn"] = re.sub(r"[-\s]", "", data["isbn"])
    return Book.objects.create(**data)


class TempBooksDirMixin:
    """Каждый тест пишет JSON-файлы в свою временную папку."""

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp()
        override = override_settings(BOOKS_DIR=Path(self.tmp))
        override.enable()
        self.addCleanup(override.disable)
        self.addCleanup(shutil.rmtree, self.tmp, True)


class MigrationTests(TestCase):
    def test_no_missing_migrations(self):
        call_command("makemigrations", "library", check=True, dry_run=True)


class AddBookTests(TempBooksDirMixin, TestCase):
    url = reverse("add")

    def post(self, destination="db", **override):
        return self.client.post(self.url, {"destination": destination, **book_data(**override)})

    def test_save_to_database(self):
        response = self.post()
        self.assertRedirects(response, reverse("index") + "?source=db")
        book = Book.objects.get()
        self.assertEqual(book.isbn, "9785170903337")     # нормализован

    def test_duplicate_isbn_not_saved(self):
        make_book()
        response = self.post(title="Другое название", author="Другой автор", isbn="9785170903337")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Такая книга уже есть в базе данных")
        self.assertEqual(Book.objects.count(), 1)

    def test_duplicate_title_author_year_ignores_case(self):
        make_book()
        response = self.post(title="  мастер и МАРГАРИТА ", author="м. булгаков", isbn=ISBN_B)
        self.assertContains(response, "Такая книга уже есть в базе данных")
        self.assertEqual(Book.objects.count(), 1)

    def test_same_title_other_year_is_not_duplicate(self):
        make_book()
        self.post(year=1973, isbn=ISBN_B)
        self.assertEqual(Book.objects.count(), 2)

    def test_save_to_json_file(self):
        response = self.post(destination="json")
        self.assertRedirects(response, reverse("index") + "?source=files")
        self.assertEqual(Book.objects.count(), 0)
        files = list(Path(self.tmp).glob("*.json"))
        self.assertEqual(len(files), 1)
        saved = json.loads(files[0].read_text(encoding="utf-8"))
        self.assertEqual(saved["books"][0]["title"], "Мастер и Маргарита")

    def test_invalid_data_rejected(self):
        for bad in ({"isbn": "978-5-17-090333-0"},      # неверная контрольная сумма
                    {"year": 2999}, {"pages": 0}, {"title": ""}, {"genre": "Нет такого"}):
            with self.subTest(bad=bad):
                response = self.post(**bad)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(Book.objects.count(), 0)
                self.assertEqual(list(Path(self.tmp).glob("*.json")), [])


class ListTests(TempBooksDirMixin, TestCase):
    def test_db_list(self):
        make_book()
        self.assertContains(self.client.get(reverse("index") + "?source=db"), "Мастер и Маргарита")

    def test_files_empty_message(self):
        response = self.client.get(reverse("index") + "?source=files")
        self.assertContains(response, "нет ни одного JSON-файла")

    def test_files_list(self):
        storage.save_books([book_data(isbn="9785170903337")])
        self.assertContains(self.client.get(reverse("index") + "?source=files"), "М. Булгаков")

    def test_unknown_source_falls_back_to_db(self):
        self.assertEqual(self.client.get(reverse("index") + "?source=hack").status_code, 200)


class SearchTests(TestCase):
    def setUp(self):
        make_book()
        make_book(title="Война и мир", author="Л. Толстой", year=1869, isbn=ISBN_B,
                  description="Роман-эпопея")

    def search(self, q):
        return self.client.get(reverse("book_search"), {"q": q}).json()

    def test_empty_query_returns_all(self):
        self.assertEqual(self.search("")["count"], 2)

    def test_case_insensitive_cyrillic(self):
        data = self.search("БУЛГАКОВ")
        self.assertEqual(data["count"], 1)
        self.assertIn("Мастер и Маргарита", data["html"])

    def test_searches_description_and_isbn(self):
        self.assertEqual(self.search("эпопея")["count"], 1)
        self.assertEqual(self.search("9783161484100")["count"], 1)

    def test_nothing_found(self):
        data = self.search("несуществующее")
        self.assertEqual(data["count"], 0)
        self.assertIn("Ничего не найдено", data["html"])

    def test_html_is_escaped(self):
        make_book(title="<script>alert(1)</script>", author="X", year=2000, isbn="0306406152")
        html = self.search("script")["html"]
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)


class EditDeleteTests(TestCase):
    def setUp(self):
        self.book = make_book()
        self.other = make_book(title="Война и мир", author="Л. Толстой", year=1869, isbn=ISBN_B)
        self.edit_url = reverse("book_edit", args=[self.book.pk])

    def test_edit_form_prefilled(self):
        self.assertContains(self.client.get(self.edit_url), "Мастер и Маргарита")

    def test_edit_saves(self):
        response = self.client.post(self.edit_url, book_data(title="Новое название", pages=500))
        self.assertRedirects(response, reverse("index") + "?source=db")
        self.book.refresh_from_db()
        self.assertEqual((self.book.title, self.book.pages), ("Новое название", 500))

    def test_edit_invalid_not_saved(self):
        response = self.client.post(self.edit_url, book_data(pages=0))
        self.assertEqual(response.status_code, 200)
        self.book.refresh_from_db()
        self.assertEqual(self.book.pages, 480)

    def test_edit_into_duplicate_rejected(self):
        response = self.client.post(self.edit_url, book_data(isbn=ISBN_B))
        self.assertContains(response, "Изменения не сохранены")
        self.book.refresh_from_db()
        self.assertEqual(self.book.isbn, "9785170903337")

    def test_delete_ajax(self):
        response = self.client.post(reverse("book_delete", args=[self.book.pk]),
                                    HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertTrue(response.json()["ok"])
        self.assertFalse(Book.objects.filter(pk=self.book.pk).exists())

    def test_delete_requires_post(self):
        response = self.client.get(reverse("book_delete", args=[self.book.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Book.objects.filter(pk=self.book.pk).exists())

    def test_missing_book_404(self):
        self.assertEqual(self.client.get(reverse("book_edit", args=[99999])).status_code, 404)


class UploadTests(TempBooksDirMixin, TestCase):
    url = reverse("upload")

    def upload(self, name, content):
        return self.client.post(self.url, {"file": SimpleUploadedFile(name, content)})

    def test_valid_file_saved_under_generated_name(self):
        payload = json.dumps({"books": [book_data()]}).encode()
        response = self.upload("../../мой файл.json", payload)
        self.assertRedirects(response, reverse("index"))
        files = list(Path(self.tmp).iterdir())
        self.assertEqual(len(files), 1)
        self.assertRegex(files[0].name, r"^[0-9a-f]{32}\.json$")

    def test_broken_json_deleted(self):
        response = self.upload("a.json", b"{not json")
        self.assertContains(response, "невалиден и был удалён")
        self.assertEqual(list(Path(self.tmp).iterdir()), [])

    def test_invalid_book_deleted(self):
        payload = json.dumps([book_data(isbn="123")]).encode()
        self.upload("a.json", payload)
        self.assertEqual(list(Path(self.tmp).iterdir()), [])

    def test_wrong_extension_rejected(self):
        self.upload("a.txt", b"{}")
        self.assertEqual(list(Path(self.tmp).iterdir()), [])

    def test_download_rejects_bad_id(self):
        self.assertEqual(self.client.get(reverse("download", args=["..%2Fsettings"])).status_code, 404)
