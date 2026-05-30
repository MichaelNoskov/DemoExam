# Демоэкзамен 09.02.07 — Пайплайн разработки

> Главный файл. Здесь — только этапы, команды и ссылки на детали.
> Если тема знакома — пропускай ссылку, выполняй команды.

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

**Что делаем:** Устанавливаем инструменты, создаём БД, настраиваем Python-окружение.

```bash
# PostgreSQL — создать БД
sudo -u postgres psql -c "CREATE DATABASE shoe_store_2 OWNER postgres;"

# uv — менеджер пакетов
pip install uv

# Создать папку проекта и войти в неё
mkdir myproject && cd myproject

# Инициализировать проект с uv
uv init --no-readme
uv add "django>=6.0.4" "pillow>=12.2.0" "psycopg2-binary>=2.9.12"
source .venv/bin/activate
```

**Файлы:** `pyproject.toml` создаётся автоматически

→ [Подробнее: setup.md](setup.md)

---

## Этап 1 — Проектирование БД (Модуль 1)

**Что делаем:** Продумываем схему таблиц в 3НФ на бумаге/в голове перед кодом.

Таблицы проекта: `Role`, `User`, `Supplier`, `PickupPoint`, `Product`, `Order`, `OrderItem`

**Файлы:** Только аналитика — код пишем на этапе 3.

→ [Подробнее: db-design.md](db-design.md)

---

## Этап 2 — ER-диаграмма (draw.io → PDF)

**Что делаем:** Рисуем ER-диаграмму в draw.io и экспортируем в PDF для сдачи.

**Инструмент:** app.diagrams.net → шаблон Entity Relationship

→ [Пошаговая инструкция: er-diagram.md](er-diagram.md)

---

## Этап 3 — Блок-схема алгоритма (Модуль 2)

**Что делаем:** Рисуем блок-схему логики входа + отображения товаров по ГОСТ 19.701-90.

**Инструмент:** draw.io (та же программа, другая нотация)

→ [Подробнее: flowchart.md](flowchart.md)

---

## Этап 4 — Инициализация Django-проекта

**Что делаем:** Создаём структуру проекта, настраиваем `settings.py`.

```bash
django-admin startproject config .
python manage.py startapp core

# Создать папки вручную
mkdir -p core/templates/core
mkdir -p core/management/commands
touch core/management/__init__.py
touch core/management/commands/__init__.py
mkdir -p static/css static/images
mkdir -p media/products
```

**Файлы для редактирования:**
- `config/settings.py` — БД, AUTH_USER_MODEL, STATIC, MEDIA, LOGIN_REDIRECT_URL
- `config/urls.py` — базовая маршрутизация

→ [Полная настройка: django-init.md](django-init.md)

---

## Этап 5 — ORM-модели + миграции

**Что делаем:** Создаём все модели данных в `core/models.py`, применяем миграции.

```bash
# После написания models.py:
python manage.py makemigrations
python manage.py migrate

# Проверка (опционально):
python manage.py sqlmigrate core 0001
```

**Файлы:**
- `core/models.py` — 7 моделей
- `core/admin.py` — регистрация для Django-admin

→ [Типы полей, синтаксис, полный код: orm-models.md](orm-models.md)

---

## Этап 6 — Скрипт импорта CSV (вариативная часть)

**Что делаем:** Пишем management command для загрузки данных из CSV в БД.

```bash
# Запуск после написания скрипта:
python manage.py import_data
```

**Файлы:**
- `core/management/commands/import_data.py`

**CSV-файлы** должны лежать в `part_1/add_2/import/`:
`pp.csv`, `products.csv`, `users.csv`, `orders.csv`

→ [Management commands, CSV, полный код: csv-import.md](csv-import.md)

---

## Этап 7 — Views + URLs

**Что делаем:** Пишем представления (классовые view) для входа, списка товаров, добавления и редактирования.

```bash
# После написания views.py и urls.py — запустить сервер:
python manage.py runserver
# Открыть http://127.0.0.1:8000/
```

**Файлы:**
- `core/views.py` — 5 классов
- `config/urls.py` — маршруты + media в DEBUG

→ [CBV, миксины, Q-объекты, полный код: views-urls.md](views-urls.md)

---

## Этап 8 — HTML-шаблоны + CSS

**Что делаем:** Создаём все шаблоны и стили.

**Файлы:**
- `core/templates/core/base.html`
- `core/templates/core/login.html`
- `core/templates/core/product_list.html`
- `core/templates/core/product_form.html`
- `static/css/style.css`
- `static/images/Icon.png`, `Icon.ico`, `picture.png` — скопировать из Модуль 1/import/

→ [Синтаксис шаблонов, весь HTML/CSS: templates.md](templates.md)

---

## Этап 9 — Формы с валидацией

**Что делаем:** Пишем `ProductForm` с кастомным полем поставщика и валидацией.

**Файлы:**
- `core/forms.py`

→ [ModelForm, clean_X, save(), полный код: forms.md](forms.md)

---

## Этап 10 — Изображения с Pillow (вариативная часть)

**Что делаем:** Настраиваем загрузку и обработку изображений через Pillow.

Pillow уже установлен (этап 0). Нужно убедиться что:
- `ImageField` использован в модели
- `MEDIA_URL` и `MEDIA_ROOT` настроены
- Авто-удаление старого фото работает
- (Опционально) ресайз до 300×200 пикселей

→ [ImageField, MEDIA, авто-удаление, ресайз: images-pillow.md](images-pillow.md)

---

## Этап 11 — Проверка вариативных задач

**Что делаем:** Убеждаемся что все 5 вариативных задач реализованы.

```bash
# Запустить сервер и проверить:
python manage.py runserver
```

Чеклист:
- [ ] `import_data.py` существует и работает
- [ ] `{% csrf_token %}` в каждой POST-форме
- [ ] `Product.save()` удаляет старое фото
- [ ] `pillow` в `pyproject.toml`, `ImageField` в модели
- [ ] Проект на Django (не Flask)

→ [Все 5 задач подробно: variative.md](variative.md)

---

## Этап 12 — Git и финальная сдача

**Что делаем:** Инициализируем репо, делаем коммиты, готовим к сдаче.

```bash
git init
git add pyproject.toml manage.py config/ core/ static/
git commit -m "initial commit"

# Получить SQL-дамп структуры БД:
pg_dump -U postgres -s shoe_store_2 > schema.sql
```

**Что сдавать:** исходный код + `schema.sql` + ER-диаграмма.pdf + блок-схема.pdf + скриншоты.docx

→ [Git-команды, .gitignore, структура сдачи: git.md](git.md)

---

## Порядок коммитов (как у преподавателя)

```
1. initial commit
2. module 1: add models
3. module 1: add import script
4. module 2: add login view, template, url, static files
5. module 2: add product list guest view and styles
6. module 2: add guest entrance link
7. module 2: add search form for admin and manager
8. module 2-3: add search and filter logic
9. module 2-3: add product form
10. fix image not showing
11. clean form and make image upload working
12. upload images
13. add product edit button
```
