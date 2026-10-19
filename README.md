# Библиотека: книги в JSON-файлах и в SQLite (Django)

Вариант 1 — информация о книгах. Данные можно хранить **в JSON-файлах** или **в базе данных SQLite**.

## Возможности
- Форма добавления книги с валидацией (ISBN с контрольной суммой, год, страницы и т. д.)
  и **выбором, куда сохранить**: база данных или JSON-файл.
- **Проверка дубликатов в БД**: совпадение ISBN либо (название + автор + год) без учёта регистра.
  Дубликат не добавляется, пользователь видит сообщение.
- Загрузка JSON-файлов: имя файла генерирует сервер (uuid), невалидный файл удаляется.
- Просмотр данных из **любого источника** (переключатель «База данных» / «JSON-файлы»).
- Для записей в БД: **AJAX-поиск** по названию, автору, ISBN, жанру и описанию,
  **редактирование** (с той же валидацией) и **удаление** (подтверждение в модальном окне, AJAX).
- Интерфейс на Bootstrap 5 (подключается с CDN).

## Локальный запуск
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate        # создаёт db.sqlite3 и таблицу library_book
python manage.py runserver
```
Откройте http://127.0.0.1:8000/. Для проверки загрузки возьмите `examples/books.json`.

Тесты: `python manage.py test`

## Структура
```
config/            настройки проекта, urls, wsgi
library/
  models.py        модель Book (SQLite)
  migrations/      миграции
  forms.py         валидация (BookForm, AddBookForm, UploadForm)
  services.py      поиск дубликатов в БД
  storage.py       чтение/запись/валидация JSON-файлов
  views.py         страницы и AJAX-эндпоинты
  templates/       шаблоны Bootstrap
  tests.py
examples/books.json
```

## Переменные окружения
| Переменная | Назначение | По умолчанию |
|---|---|---|
| `DJANGO_DEBUG` | `0` на хостинге | `1` |
| `DJANGO_SECRET_KEY` | обязателен при `DJANGO_DEBUG=0` | — |
| `DJANGO_ALLOWED_HOSTS` | домены через запятую | localhost |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://ваш-домен` через запятую | — |
| `DJANGO_DB_PATH` | путь к файлу SQLite | `./db.sqlite3` |
| `BOOKS_DIR` | папка с JSON-файлами | `./data/books` |

## Публикация на PythonAnywhere (бесплатный тариф)
Подходит, потому что диск постоянный: SQLite-файл и папка `data/books` не пропадают при перезапуске.

1. Зарегистрируйтесь на https://www.pythonanywhere.com (Beginner, бесплатно). Ваш адрес: `ЛОГИН.pythonanywhere.com`.
2. Вкладка **Consoles → Bash**:
   ```bash
   git clone https://github.com/ВАШ_ЛОГИН/ВАШ_РЕПОЗИТОРИЙ.git
   cd ВАШ_РЕПОЗИТОРИЙ
   mkvirtualenv books --python=python3.10      # нужна версия Python 3.10 или новее
   pip install -r requirements.txt
   python manage.py migrate
   python -c "import secrets; print(secrets.token_urlsafe(50))"   # скопируйте как секретный ключ
   ```
3. Вкладка **Web → Add a new web app → Manual configuration** (выберите ту же версию Python).
4. На странице Web укажите:
   - **Source code**: `/home/ЛОГИН/ВАШ_РЕПОЗИТОРИЙ`
   - **Virtualenv**: `/home/ЛОГИН/.virtualenvs/books`
5. Откройте **WSGI configuration file** и замените всё содержимое на:
   ```python
   import os
   import sys

   path = "/home/ЛОГИН/ВАШ_РЕПОЗИТОРИЙ"
   if path not in sys.path:
       sys.path.insert(0, path)

   os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
   os.environ["DJANGO_DEBUG"] = "0"
   os.environ["DJANGO_SECRET_KEY"] = "ВСТАВЬТЕ_СГЕНЕРИРОВАННЫЙ_КЛЮЧ"
   os.environ["DJANGO_ALLOWED_HOSTS"] = "ЛОГИН.pythonanywhere.com"
   os.environ["DJANGO_CSRF_TRUSTED_ORIGINS"] = "https://ЛОГИН.pythonanywhere.com"

   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```
6. Нажмите **Reload** на вкладке Web и откройте `https://ЛОГИН.pythonanywhere.com`.

Статические файлы настраивать не нужно: Bootstrap грузится с CDN, админка не используется.

Обновление после изменений: `git pull` в консоли, при новых миграциях `python manage.py migrate`, затем **Reload**.

> На хостингах с временным диском (бесплатные тарифы Render, Railway и подобные) SQLite-файл и загруженные
> JSON-файлы пропадают при каждом перезапуске. Для них нужен подключаемый постоянный том либо другая БД.
