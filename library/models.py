from django.db import models

GENRES = ["Роман", "Фантастика", "Детектив", "Фэнтези", "Научная литература",
          "Биография", "Поэзия", "История", "Другое"]
GENRE_CHOICES = [(g, g) for g in GENRES]


class Book(models.Model):
    title = models.CharField("Название", max_length=200)
    author = models.CharField("Автор", max_length=120)
    year = models.PositiveIntegerField("Год издания")
    isbn = models.CharField("ISBN", max_length=20)
    genre = models.CharField("Жанр", max_length=40, choices=GENRE_CHOICES)
    pages = models.PositiveIntegerField("Количество страниц")
    description = models.TextField("Описание", blank=True)
    created_at = models.DateTimeField("Добавлено", auto_now_add=True)

    class Meta:
        verbose_name = "Книга"
        verbose_name_plural = "Книги"
        ordering = ["-created_at", "-id"]
        constraints = [
            # ISBN хранится в нормализованном виде (без дефисов и пробелов),
            # поэтому уникальность на уровне БД ловит дубликаты даже при гонке запросов
            models.UniqueConstraint(fields=["isbn"], name="unique_book_isbn"),
        ]

    def __str__(self):
        return f"{self.title} — {self.author} ({self.year})"
