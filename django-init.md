# Инициализация Django-проекта

← [Назад к пайплайну](README.md)

---

## 1. Создать структуру проекта

```bash
# Создать Django-проект в текущей папке (точка = не создавать вложенную папку)
django-admin startproject config .

# Создать приложение core
python manage.py startapp core

# Создать необходимые папки
mkdir -p core/templates/core
mkdir -p core/management/commands
mkdir -p static/css
mkdir -p static/images
mkdir -p media/products

# Создать __init__.py для management команд
touch core/management/__init__.py
touch core/management/commands/__init__.py
```

После этих команд структура папок:

```
myproject/
├── manage.py
├── pyproject.toml
├── config/
│   ├── __init__.py
│   ├── settings.py      ← редактируем
│   ├── urls.py          ← редактируем
│   ├── wsgi.py
│   └── asgi.py
├── core/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py        ← пишем модели
│   ├── views.py         ← пишем views
│   ├── forms.py         ← создаём
│   ├── tests.py
│   ├── templates/
│   │   └── core/
│   │       ├── base.html
│   │       ├── login.html
│   │       ├── product_list.html
│   │       └── product_form.html
│   └── management/
│       ├── __init__.py
│       └── commands/
│           ├── __init__.py
│           └── import_data.py
├── static/
│   ├── css/
│   │   └── style.css
│   └── images/
│       ├── Icon.png
│       ├── Icon.ico
│       └── picture.png
└── media/
    └── products/
        └── 1.jpg ... 10.jpg
```

---

## 2. config/settings.py — полное содержимое

Заменить весь файл:

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-juxbbv#f+93@&1rt#7fyj=@e^700n1bdzjvx)9k!c7&abhet_q"

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",          # ← наше приложение
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",    # ← CSRF защита
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,    # ← ищет templates/ внутри каждого приложения
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# База данных PostgreSQL
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "shoe_store_2",
        "USER": "postgres",
        "PASSWORD": "826456",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Используем нашу кастомную модель пользователя
AUTH_USER_MODEL = "core.User"

# Локализация
LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

# Статические файлы (CSS, картинки)
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]   # папка static/ в корне проекта

# Медиафайлы (загружаемые пользователями фото)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Куда редиректить после входа/выхода
LOGIN_REDIRECT_URL = "product_list"
LOGOUT_REDIRECT_URL = "login"
```

---

## 3. config/urls.py — начальная минимальная версия

На этом этапе `core/views.py` ещё не написан — импортировать нечего. Начинаем с минимума:

```python
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

> **urls.py расширяется постепенно** — каждый следующий этап добавляет свои импорты и path().
> Финальная версия (с заказами и удалением) — в [README.md → Финальный urls.py](README.md).

### Как добавлять URL по шагам

| Этап | Что добавить в urlpatterns |
|------|---------------------------|
| Этап 7 — Login | `path("", UserLoginView...)`, `path("logout/", LogoutView...)` |
| Этап 8 — ProductList | `path("products/", ProductListView...)` |
| Этап 9 — CRUD товаров | `path("products/add/", ...)`, `path("products/<int:pk>/edit/", ...)` |
| Этап 10 — Удаление | `path("products/<int:pk>/delete/", ...)` |
| Этап 11 — Заказы | `path("orders/", ...)`, `path("orders/add/", ...)`, `path("orders/<int:pk>/edit/", ...)`, `path("orders/<int:pk>/delete/", ...)` |

---

## 4. Скопировать статические изображения

```bash
# Скопировать из папки с материалами экзамена:
cp "Модуль 1/import/Icon.png" static/images/
cp "Модуль 1/import/Icon.ico" static/images/
cp "Модуль 1/import/picture.png" static/images/

# Скопировать фото товаров:
cp "Модуль 1/import/1.jpg" media/products/
cp "Модуль 1/import/2.jpg" media/products/
# ... и т.д. до 10.jpg
```

---

## 5. Проверка

```bash
# Должно вывести "System check identified no issues"
python manage.py check

# Запустить сервер (после написания views)
python manage.py runserver
```

---

## 6. Ключевые настройки — краткая таблица

| Параметр | Значение | Зачем |
|----------|----------|-------|
| `AUTH_USER_MODEL` | `"core.User"` | Использовать нашу модель User |
| `LOGIN_REDIRECT_URL` | `"product_list"` | После входа → список товаров |
| `LOGOUT_REDIRECT_URL` | `"login"` | После выхода → страница входа |
| `MEDIA_ROOT` | `BASE_DIR / "media"` | Куда сохраняются загруженные фото |
| `STATICFILES_DIRS` | `[BASE_DIR / "static"]` | Где искать статику |
| `APP_DIRS = True` | — | Шаблоны ищутся в `core/templates/` |
