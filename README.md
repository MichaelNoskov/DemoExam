# Демоэкзамен 09.02.07 — Пайплайн разработки

> Главный файл. Этапы → команды → ссылки на детали.
> Каждый этап добавляет только то, что нужно прямо сейчас.
> `urls.py` обновляется постепенно — на каждом шаге написан **точный фрагмент** для добавления.

---

## Таблица баллов

| Часть | Критерий | Баллы |
|---|---|---|
| **Инвариантная** | Проектирование БД (3НФ, целостность) | 6 |
| | Реализация БД в СУБД | 4 |
| | Проектирование алгоритма | 2 |
| | Разработка модуля по ТЗ | 11 |
| | Отладка с использованием инструментов | 2 |
| | Модификация ПО | 24 |
| | Поиск и анализ информации | 1 |
| | Интеграция модулей | 23 |
| | Подход к решению задачи | 2 |
| | **Итого инвариант** | **75** |
| **Вариативная** | Скрипт загрузки CSV → БД | 5 |
| | CSRF-защита | 5 |
| | Удаление неиспользуемых фото | 5 |
| | Pillow для изображений | 5 |
| | Django как фреймворк | 5 |
| | **Итого вариатив** | **25** |
| | **МАКСИМУМ** | **100** |

---

## Этап 0 — Подготовка окружения

```bash
sudo -u postgres psql -c "CREATE DATABASE shoe_store_2 OWNER postgres;"
pip install uv
mkdir myproject && cd myproject
uv init --no-readme
uv add "django>=6.0.4" "pillow>=12.2.0" "psycopg2-binary>=2.9.12"
source .venv/bin/activate
```

→ [Подробнее: setup.md](setup.md)

---

## Этап 1 — Проектирование БД (Модуль 1)

Продумать схему на бумаге до написания кода. 7 таблиц:
`Role`, `User`, `Supplier`, `PickupPoint`, `Product`, `Order`, `OrderItem`

→ [Подробнее: db-design.md](db-design.md)

---

## Этап 2 — ER-диаграмма (draw.io → PDF)

→ [Пошаговая инструкция: er-diagram.md](er-diagram.md)

---

## Этап 3 — Блок-схема алгоритма (Модуль 2, ГОСТ 19.701-90)

→ [Подробнее: flowchart.md](flowchart.md)

---

## Этап 4 — Инициализация Django-проекта

```bash
django-admin startproject config .
python manage.py startapp core
mkdir -p core/templates/core
mkdir -p core/management/commands
touch core/management/__init__.py
touch core/management/commands/__init__.py
mkdir -p static/css static/images
mkdir -p media/products
```

**Начальный `config/urls.py`** (минимальный — будем расширять):
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

→ [Полная настройка settings.py: django-init.md](django-init.md)

---

## Этап 5 — ORM-модели + миграции

Редактировать: `core/models.py`

```bash
python manage.py makemigrations
python manage.py migrate
```

→ [Типы полей, синтаксис, полный код models.py: orm-models.md](orm-models.md)

---

## Этап 6 — Скрипт импорта CSV (вариативная часть)

Создать: `core/management/commands/import_data.py`

```bash
python manage.py import_data
```

→ [Management commands, CSV, полный код: csv-import.md](csv-import.md)

---

## Этап 7 — Вход в систему (Login view)

Создать: `core/views.py` (только `UserLoginView`)  
Создать: `core/templates/core/base.html`, `login.html`

**Добавить в `urls.py`:**
```python
from django.contrib.auth.views import LogoutView
from core.views import UserLoginView

# в urlpatterns:
path("", UserLoginView.as_view(), name="login"),
path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
```

→ [CBV, миксины, полный код views.py: views-urls.md](views-urls.md)

---

## Этап 8 — Список товаров + CSS

Добавить в `core/views.py`: `ProductListView`  
Создать: `core/templates/core/product_list.html`  
Создать: `static/css/style.css`  
Скопировать: `static/images/Icon.png`, `Icon.ico`, `picture.png`

**Добавить в `urls.py`:**
```python
from core.views import ProductListView

path("products/", ProductListView.as_view(), name="product_list"),
```

→ [Синтаксис шаблонов, весь HTML/CSS: templates.md](templates.md)

---

## Этап 9 — Форма добавления/редактирования товара

Создать: `core/forms.py` (`ProductForm`)  
Добавить в `core/views.py`: `AdminRequiredMixin`, `ProductCreateUpdateMixin`, `ProductCreateView`, `ProductUpdateView`  
Создать: `core/templates/core/product_form.html`

**Добавить в `urls.py`:**
```python
from core.views import ProductCreateView, ProductUpdateView

path("products/add/", ProductCreateView.as_view(), name="product_create"),
path("products/<int:pk>/edit/", ProductUpdateView.as_view(), name="product_edit"),
```

→ [ModelForm, валидация: forms.md](forms.md) | [ImageField, Pillow: images-pillow.md](images-pillow.md)

---

## Этап 10 — Удаление товара (Модуль 3)

Добавить в `core/views.py`: `ProductDeleteView`

**Добавить в `urls.py`:**
```python
from core.views import ProductDeleteView

path("products/<int:pk>/delete/", ProductDeleteView.as_view(), name="product_delete"),
```

В `product_list.html` добавить кнопку "Удалить" с `onsubmit="return confirm(...)"`.

→ [Подробнее о delete view: views-urls.md](views-urls.md)

---

## Этап 11 — Раздел заказов (Модуль 4)

Создать: `core/forms.py` → добавить `OrderForm`  
Добавить в `core/views.py`: `ManagerOrAdminMixin`, `OrderListView`, `OrderCreateView`, `OrderUpdateView`, `OrderDeleteView`  
Создать: `core/templates/core/order_list.html`  
Создать: `core/templates/core/order_form.html`

**Добавить в `urls.py`:**
```python
from core.views import OrderListView, OrderCreateView, OrderUpdateView, OrderDeleteView

path("orders/", OrderListView.as_view(), name="order_list"),
path("orders/add/", OrderCreateView.as_view(), name="order_create"),
path("orders/<int:pk>/edit/", OrderUpdateView.as_view(), name="order_edit"),
path("orders/<int:pk>/delete/", OrderDeleteView.as_view(), name="order_delete"),
```

→ [Полный гайд по Модулю 4: orders-module.md](orders-module.md)

---

## Этап 12 — Проверка вариативных задач

```bash
python manage.py runserver
```

Чеклист:
- [ ] `import_data.py` существует и работает без ошибок
- [ ] `{% csrf_token %}` в каждой POST-форме (login, logout, product form, order form, delete)
- [ ] `Product.save()` удаляет старое фото и делает resize до 300×200
- [ ] `pillow>=12.2.0` в `pyproject.toml`, `ImageField` в модели
- [ ] Проект работает через Django

→ [Все 5 задач подробно: variative.md](variative.md)

---

## Этап 13 — Git и финальная сдача

```bash
git init
git add manage.py pyproject.toml config/ core/ static/
git commit -m "initial commit"
pg_dump -U postgres -s shoe_store_2 > schema.sql
```

→ [Git-команды, структура сдачи: git.md](git.md)

---

## Финальный `config/urls.py` (итог всех этапов)

```python
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path

from core.views import (
    OrderCreateView, OrderDeleteView, OrderListView, OrderUpdateView,
    ProductCreateView, ProductDeleteView, ProductListView, ProductUpdateView,
    UserLoginView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", UserLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path("products/", ProductListView.as_view(), name="product_list"),
    path("products/add/", ProductCreateView.as_view(), name="product_create"),
    path("products/<int:pk>/edit/", ProductUpdateView.as_view(), name="product_edit"),
    path("products/<int:pk>/delete/", ProductDeleteView.as_view(), name="product_delete"),
    path("orders/", OrderListView.as_view(), name="order_list"),
    path("orders/add/", OrderCreateView.as_view(), name="order_create"),
    path("orders/<int:pk>/edit/", OrderUpdateView.as_view(), name="order_edit"),
    path("orders/<int:pk>/delete/", OrderDeleteView.as_view(), name="order_delete"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## Порядок коммитов

```
1. initial commit
2. module 1: add models
3. module 1: add import script
4. module 2: add login view, template, url, static files
5. module 2: add product list view and styles
6. module 2-3: add search, filter, sort
7. module 2-3: add product form (add/edit)
8. module 3: add product delete
9. module 4: add orders section
```
