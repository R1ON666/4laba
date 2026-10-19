import datetime
import re

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

from .models import GENRE_CHOICES

def validate_isbn(value):
    """Проверка ISBN-10 / ISBN-13 с контрольной суммой (дефисы и пробелы допустимы)."""
    s = re.sub(r"[-\s]", "", str(value)).upper()
    if re.fullmatch(r"\d{13}", s):
        total = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(s))
        ok = total % 10 == 0
    elif re.fullmatch(r"\d{9}[\dX]", s):
        total = sum((10 - i) * (10 if c == "X" else int(c)) for i, c in enumerate(s))
        ok = total % 11 == 0
    else:
        ok = False
    if not ok:
        raise ValidationError("Некорректный ISBN (ожидается ISBN-10 или ISBN-13 с верной контрольной суммой).")


class BootstrapMixin:
    """Добавляет Bootstrap-классы всем виджетам формы."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.RadioSelect):
                widget.attrs["class"] = "form-check-input"
            elif isinstance(widget, forms.Select):
                widget.attrs["class"] = "form-select"
            else:
                widget.attrs["class"] = (widget.attrs.get("class", "") + " form-control").strip()


class BookForm(BootstrapMixin, forms.Form):
    title = forms.CharField(label="Название", max_length=200, strip=True)
    author = forms.CharField(label="Автор", max_length=120, strip=True)
    year = forms.IntegerField(label="Год издания", min_value=1000)
    isbn = forms.CharField(label="ISBN", max_length=20, validators=[validate_isbn],
                           help_text="Например: 978-5-17-090333-7 или 0-306-40615-2")
    genre = forms.ChoiceField(label="Жанр", choices=GENRE_CHOICES)
    pages = forms.IntegerField(label="Количество страниц", min_value=1, max_value=10000)
    description = forms.CharField(label="Описание", max_length=2000, required=False,
                                  strip=True, widget=forms.Textarea(attrs={"rows": 4}))

    def clean_year(self):
        year = self.cleaned_data["year"]
        if year > datetime.date.today().year:
            raise ValidationError("Год издания не может быть в будущем.")
        return year

    def clean_isbn(self):
        return re.sub(r"[-\s]", "", self.cleaned_data["isbn"]).upper()   # нормализованный вид для сравнения дубликатов


DESTINATIONS = [
    ("db", "База данных (SQLite)"),
    ("json", "Файл JSON"),
]


class AddBookForm(BookForm):
    """Форма добавления: та же книга + выбор, куда сохранить."""
    destination = forms.ChoiceField(label="Куда сохранить", choices=DESTINATIONS,
                                    initial="db", widget=forms.RadioSelect)
    field_order = ["destination"]


class UploadForm(BootstrapMixin, forms.Form):
    file = forms.FileField(
        label="JSON-файл",
        validators=[FileExtensionValidator(["json"], message="Допустимо только расширение .json")],
    )

    def clean_file(self):
        f = self.cleaned_data["file"]
        if f.size == 0:
            raise ValidationError("Файл пуст.")
        if f.size > settings.MAX_UPLOAD_SIZE:
            raise ValidationError("Файл слишком большой (максимум 1 МБ).")
        return f
