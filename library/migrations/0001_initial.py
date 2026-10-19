from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Book",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="Название")),
                ("author", models.CharField(max_length=120, verbose_name="Автор")),
                ("year", models.PositiveIntegerField(verbose_name="Год издания")),
                ("isbn", models.CharField(max_length=20, verbose_name="ISBN")),
                ("genre", models.CharField(
                    choices=[("Роман", "Роман"), ("Фантастика", "Фантастика"), ("Детектив", "Детектив"),
                             ("Фэнтези", "Фэнтези"), ("Научная литература", "Научная литература"),
                             ("Биография", "Биография"), ("Поэзия", "Поэзия"), ("История", "История"),
                             ("Другое", "Другое")],
                    max_length=40, verbose_name="Жанр")),
                ("pages", models.PositiveIntegerField(verbose_name="Количество страниц")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Добавлено")),
            ],
            options={
                "verbose_name": "Книга",
                "verbose_name_plural": "Книги",
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.AddConstraint(
            model_name="book",
            constraint=models.UniqueConstraint(fields=("isbn",), name="unique_book_isbn"),
        ),
    ]
