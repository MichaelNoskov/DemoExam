# Git — работа с репозиторием

← [Назад к пайплайну](README.md)

---

## 1. Инициализация репозитория

```bash
# В корне проекта:
git init
git branch -M main   # переименовать ветку в main
```

---

## 2. .gitignore — что не коммитить

Создать файл `.gitignore` в корне проекта:

```gitignore
# Виртуальное окружение
.venv/
venv/
env/

# Кеш Python
__pycache__/
*.pyc
*.pyo
*.pyd

# Django
*.log
local_settings.py
db.sqlite3

# Секреты (на всякий случай)
.env
*.env

# Временные файлы
*.tmp
.DS_Store
```

> **Медиафайлы (фото товаров):** Решение неоднозначное.
> - Если в ТЗ написано "загрузить в репо" — не игнорируй `media/`
> - Если нет — добавь `media/products/` в .gitignore
> - Безопаснее: не игнорировать, чтобы фото были в репозитории

---

## 3. Первый коммит

```bash
# Добавить все файлы проекта (кроме .gitignore-исключений)
git add manage.py pyproject.toml
git add config/
git add core/
git add static/
git add media/

# Создать коммит
git commit -m "initial commit"
```

---

## 4. Порядок коммитов (по этапам разработки)

Коммиты лучше делать после каждого значимого этапа — так легче отлаживать.

```bash
# Этап: модели
git add core/models.py core/migrations/
git commit -m "module 1: add models"

# Этап: скрипт импорта
git add core/management/
git commit -m "module 1: add import script"

# Этап: вход в систему
git add core/views.py core/templates/ static/ config/urls.py
git commit -m "module 2: add login view, template, url, static files"

# Этап: список товаров
git add core/views.py core/templates/core/product_list.html static/css/
git commit -m "module 2: add product list guest view and styles"

# Этап: поиск и фильтры
git add core/views.py core/templates/core/product_list.html
git commit -m "module 2-3: add search and filter logic"

# Этап: формы добавления/редактирования
git add core/forms.py core/views.py core/templates/core/product_form.html
git commit -m "module 2-3: add product form"
```

---

## 5. Полная история коммитов (как у преподавателя)

```
1.  initial commit
2.  module 1: add models
3.  module 1: add import script
4.  module 2: add login view, template, url, static files
5.  module 2: add product list guest view and styles
6.  module 2: add guest entrance link
7.  module 2: add search form for admin and manager
8.  module 2-3: add search and filter logic
9.  module 2-3: add product form
10. fix image not showing
11. clean form and make image upload working
12. upload images
13. add product edit button
```

---

## 6. Получение SQL-дампа для сдачи

```bash
# Только структура (без данных):
pg_dump -U postgres -s shoe_store_2 > schema.sql

# Структура + данные:
pg_dump -U postgres shoe_store_2 > full_dump.sql

# Если нужен пароль:
PGPASSWORD=826456 pg_dump -U postgres -s shoe_store_2 > schema.sql
```

---

## 7. Полезные команды git

```bash
git status              # что изменилось
git diff                # посмотреть изменения
git log --oneline       # краткая история коммитов
git add -p              # добавлять изменения по кускам (интерактивно)
git restore <file>      # отменить изменения файла (опасно!)
```

---

## 8. Структура для финальной сдачи

В репозитории должно быть:

```
myproject/
├── manage.py
├── pyproject.toml
├── .gitignore
├── schema.sql              ← SQL-скрипт структуры БД
├── ER-diagram.pdf          ← ER-диаграмма
├── flowchart.pdf           ← Блок-схема алгоритма
├── screenshots.docx        ← Скриншоты работы приложения
├── config/
│   ├── settings.py
│   └── urls.py
├── core/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── admin.py
│   ├── templates/core/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── product_list.html
│   │   └── product_form.html
│   ├── management/commands/
│   │   └── import_data.py
│   └── migrations/
│       ├── 0001_initial.py
│       └── ...
├── static/
│   ├── css/style.css
│   └── images/
│       ├── Icon.png
│       ├── Icon.ico
│       └── picture.png
└── media/
    └── products/
        └── 1.jpg ... 10.jpg
```

---

## 9. Скриншоты для .docx (Модуль 2 требование)

Сделать скриншоты:
1. Страница входа (login.html)
2. Список товаров — вид гостя (без фильтров)
3. Список товаров — вид менеджера/admin (с фильтрами)
4. Форма добавления товара
5. Форма редактирования товара
6. Список с карточками (показать разные цвета: sale, out-of-stock)

Вставить в Word, назвать `screenshots.docx`.
