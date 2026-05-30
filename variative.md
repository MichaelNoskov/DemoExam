# Вариативная часть — 25 баллов

← [Назад к пайплайну](README.md)

> 5 задач по 5 баллов каждая. Все реализованы в проекте. Проверить каждую по чеклисту.

---

## Задача 1: Скрипт загрузки из CSV в БД (5 баллов)

### Что нужно

Management command, который читает CSV-файлы и загружает данные в БД через ORM.

### Где реализовано

Файл: `core/management/commands/import_data.py`

### Как запустить

```bash
python manage.py import_data
```

### Что проверяют

- Файл `import_data.py` существует в правильном месте
- Команда выполняется без ошибок
- После выполнения в БД есть данные: 36 PickupPoint, 30 Product, 10 User, 10 Order

### Полный код и объяснение

→ [csv-import.md](csv-import.md)

### Чеклист

- [ ] Файл `core/management/commands/import_data.py` создан
- [ ] `core/management/__init__.py` существует
- [ ] `core/management/commands/__init__.py` существует
- [ ] `python manage.py import_data` выполняется без ошибок
- [ ] В БД загружены все данные

---

## Задача 2: CSRF-защита (5 баллов)

### Что такое CSRF

**CSRF (Cross-Site Request Forgery)** — атака подделки запроса. Злоумышленник заставляет браузер пользователя отправить запрос на сайт без его ведома.

**Пример:** Пользователь авторизован на сайте банка. Злоумышленник отправляет ему письмо со ссылкой, при переходе на которую браузер автоматически делает POST-запрос на перевод денег.

### Как Django защищает

1. **Middleware** `CsrfViewMiddleware` уже включён в `settings.py` по умолчанию:
   ```python
   MIDDLEWARE = [
       # ...
       "django.middleware.csrf.CsrfViewMiddleware",  # ← уже есть
       # ...
   ]
   ```

2. **CSRF-токен** — уникальный секретный токен, который Django добавляет в сессию.

3. При каждом POST-запросе Django проверяет что токен из формы совпадает с токеном в сессии.

### Что нужно сделать разработчику

В каждой POST-форме добавить `{% csrf_token %}`:

```html
<form method="post">
    {% csrf_token %}     <!-- ← обязательно! -->
    ...
</form>
```

Django рендерит это как:
```html
<input type="hidden" name="csrfmiddlewaretoken" value="abc123xyz...">
```

### Где использовано в проекте

**login.html** — форма входа:
```html
<form method="post">
    {% csrf_token %}
    <input type="text" name="username">
    <input type="password" name="password">
    <button type="submit">Войти</button>
</form>
```

**base.html** — форма выхода:
```html
<form action="{% url 'logout' %}" method="post" style="display: inline;">
    {% csrf_token %}
    <button type="submit">Выйти</button>
</form>
```

> Выход (`logout`) тоже POST-запрос — это правильно! GET-запрос на logout небезопасен (браузер может кэшировать).

**product_form.html** — форма добавления/редактирования:
```html
<form method="post" enctype="multipart/form-data">
    {% csrf_token %}
    {{ form }}
    <button type="submit">Сохранить</button>
</form>
```

### Как проверить

1. Открыть браузер → F12 → Network
2. Авторизоваться или отправить любую форму
3. В списке запросов найти POST-запрос
4. Открыть вкладку "Payload" или "Form Data"
5. Убедиться что присутствует `csrfmiddlewaretoken: <значение>`

### Чеклист

- [ ] `CsrfViewMiddleware` есть в `MIDDLEWARE` в settings.py
- [ ] `{% csrf_token %}` добавлен в форму входа (login.html)
- [ ] `{% csrf_token %}` добавлен в форму выхода (base.html)
- [ ] `{% csrf_token %}` добавлен в форму товара (product_form.html)

---

## Задача 3: Удаление неиспользуемых фотографий (5 баллов)

### Проблема

При обновлении фото товара (замене старого на новое):
- Django сохраняет новый файл в `media/products/`
- Старый файл **остаётся на диске** и занимает место
- В поле `photo` записывается путь к новому файлу

### Решение

Перехватить сохранение объекта (`save()`) и удалить старый файл до записи нового.

### Логика

```python
def save(self, *args, **kwargs):
    try:
        # Шаг 1: Получить текущее состояние из БД
        this = Product.objects.get(id=self.id)
        
        # Шаг 2: Проверить условия:
        # - было фото (this.photo)
        # - задано новое фото (self.photo)
        # - фото отличается (this.photo != self.photo)
        if this.photo and self.photo and this.photo != self.photo:
            # Шаг 3: Удалить старый файл с диска
            this.photo.delete(save=False)
            # save=False = не вызывать .save() снова (избежать бесконечной рекурсии)
    except Exception:
        # При создании нового товара self.id = None
        # Product.objects.get(id=None) выбросит DoesNotExist
        # Перехватываем и продолжаем
        pass
    
    # Шаг 4: Стандартное сохранение
    super().save(*args, **kwargs)
```

### Полный код в models.py

```python
class Product(models.Model):
    photo = models.ImageField(upload_to="products/", null=True, blank=True)
    
    def save(self, *args, **kwargs):
        try:
            this = Product.objects.get(id=self.id)
            if this.photo and self.photo and this.photo != self.photo:
                this.photo.delete(save=False)
        except Exception:
            pass
        super().save(*args, **kwargs)
```

### Как проверить

1. Загрузить товар с фото
2. Заметить имя файла в `media/products/`
3. Через форму редактирования заменить фото на другое
4. Проверить что старый файл удалён из `media/products/`

### Чеклист

- [ ] В классе `Product` переопределён метод `save()`
- [ ] Внутри `save()` есть получение `this = Product.objects.get(id=self.id)`
- [ ] Есть проверка что фото изменилось
- [ ] Вызывается `this.photo.delete(save=False)`
- [ ] Исключение перехватывается в `try/except`
- [ ] После `except` вызывается `super().save()`

---

## Задача 4: Pillow для работы с изображениями (5 баллов)

### Что нужно

1. Pillow установлен как зависимость
2. Используется `ImageField` в модели (требует Pillow)
3. Желательно: ресайз изображений при загрузке

### Где реализовано

**pyproject.toml** — зависимость:
```toml
dependencies = [
    "django>=6.0.4",
    "pillow>=12.2.0",     # ← Pillow
    "psycopg2-binary>=2.9.12",
]
```

**models.py** — ImageField:
```python
photo = models.ImageField(upload_to="products/", null=True, blank=True)
```

> `ImageField` в отличие от `FileField` использует Pillow для проверки что загружаемый файл является изображением.

### Дополнительно: ресайз до 300×200

Добавить в `Product.save()`:
```python
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

if self.photo:
    img = Image.open(self.photo)
    img = img.resize((300, 200), Image.LANCZOS)
    buffer = BytesIO()
    img.save(buffer, format=img.format or "JPEG")
    buffer.seek(0)
    self.photo.save(self.photo.name, ContentFile(buffer.getvalue()), save=False)
```

### Полное объяснение Pillow

→ [images-pillow.md](images-pillow.md)

### Чеклист

- [ ] `pillow>=12.2.0` в `pyproject.toml`
- [ ] Pillow установлен (`python -c "import PIL; print(PIL.__version__)"`)
- [ ] В модели `Product` используется `ImageField` (не `FileField`)
- [ ] Фото загружается через форму и отображается в списке товаров

---

## Задача 5: Django как основной фреймворк (5 баллов)

### Что нужно

Весь веб-приложение построено на Django.

### Где подтверждается

**pyproject.toml:**
```toml
dependencies = [
    "django>=6.0.4",    # ← Django
    ...
]
```

**manage.py** — стандартный файл Django-проекта (создаётся командой `django-admin startproject`)

**config/settings.py** — настройки Django

**core/models.py** — модели наследуют `models.Model`

**core/views.py** — используются Django CBV (ListView, CreateView, UpdateView)

### Чеклист

- [ ] `django>=6.0.4` в `pyproject.toml`
- [ ] Файл `manage.py` существует в корне проекта
- [ ] Файл `config/settings.py` существует
- [ ] Приложение работает через `python manage.py runserver`

---

## Итоговый чеклист вариативной части

| Задача | Файл | Признак выполнения |
|--------|------|-------------------|
| CSV-импорт | `core/management/commands/import_data.py` | `manage.py import_data` работает |
| CSRF | `login.html`, `base.html`, `product_form.html` | `{% csrf_token %}` в каждой POST-форме |
| Удаление фото | `core/models.py` | `Product.save()` с `photo.delete(save=False)` |
| Pillow | `pyproject.toml`, `core/models.py` | `ImageField` + pillow в зависимостях |
| Django | `pyproject.toml`, `manage.py` | Всё на Django |
