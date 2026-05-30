# Работа с изображениями — Pillow и ImageField

← [Назад к пайплайну](README.md)

> Это одна из **вариативных задач** (5 баллов). Также касается задачи удаления неиспользуемых фото.

---

## 1. Установка Pillow

```bash
uv add "pillow>=12.2.0"
# или через pip:
pip install pillow
```

В `pyproject.toml`:
```toml
dependencies = [
    "django>=6.0.4",
    "pillow>=12.2.0",      # ← без этого ImageField не работает
    "psycopg2-binary>=2.9.12",
]
```

Pillow нужен Django для:
- Валидации файла (проверяет что загружен именно файл-изображение)
- Работы с `ImageField` в модели и форме

---

## 2. ImageField в модели

```python
class Product(models.Model):
    # ...
    photo = models.ImageField(
        upload_to="products/",   # подпапка внутри MEDIA_ROOT
        null=True,               # NULL в БД если нет фото
        blank=True,              # пустое значение в форме допустимо
    )
```

**Что хранится в БД:** не сам файл, а путь к файлу (`products/1.jpg`)

**Где хранится файл:** `MEDIA_ROOT / upload_to` = `media/products/1.jpg`

---

## 3. Настройка MEDIA в settings.py

```python
# URL-префикс для медиафайлов (для браузера)
MEDIA_URL = "/media/"

# Папка на диске где хранятся файлы
MEDIA_ROOT = BASE_DIR / "media"
```

---

## 4. Раздача медиафайлов в разработке

В `config/urls.py` добавить в конец:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... все маршруты ...
]

# Только в DEBUG-режиме (на разработке)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## 5. Отображение фото в шаблоне

```html
{% if product.photo %}
    <!-- .url возвращает URL: /media/products/1.jpg -->
    <img src="{{ product.photo.url }}" alt="{{ product.name }}">
{% else %}
    <!-- заглушка из static -->
    <img src="{% static 'images/picture.png' %}" alt="Нет фото">
{% endif %}
```

> Всегда используй `.url` (не `.path`). `.path` — путь на диске сервера, браузер его не откроет.

---

## 6. Загрузка фото через форму

В шаблоне форма должна иметь `enctype`:
```html
<form method="post" enctype="multipart/form-data">
    {% csrf_token %}
    {{ form }}
    <button type="submit">Сохранить</button>
</form>
```

Без `enctype="multipart/form-data"` файлы не передаются!

---

## 7. Автоматическое удаление старого фото

**Проблема:** При обновлении фото товара старый файл остаётся на диске.

**Решение:** Переопределить `save()` в модели:

```python
def save(self, *args, **kwargs):
    try:
        # Получить текущее состояние из БД (до нашего изменения)
        this = Product.objects.get(id=self.id)
        # Сравниваем: было фото, новое фото задано, и оно другое
        if this.photo and self.photo and this.photo != self.photo:
            this.photo.delete(save=False)   # удалить файл с диска
            # save=False = не вызывать Product.save() снова (избежать рекурсии)
    except Exception:
        pass   # новый товар (self.id = None) — исключение, просто пропускаем
    super().save(*args, **kwargs)   # выполнить стандартное сохранение
```

**Что делает `this.photo.delete(save=False)`:**
- Удаляет физический файл с диска
- НЕ сохраняет модель повторно (save=False)

---

## 8. Ресайз изображений через Pillow (дополнительно)

ТЗ требует: "Изображение загружается, изменяется размер до 300×200".

Добавить ресайз в метод `save()` **перед** вызовом `super().save()`:

```python
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

class Product(models.Model):
    # ...поля...
    
    def save(self, *args, **kwargs):
        # Сначала удалить старое фото:
        try:
            this = Product.objects.get(id=self.id)
            if this.photo and self.photo and this.photo != self.photo:
                this.photo.delete(save=False)
        except Exception:
            pass
        
        # Потом ресайз нового:
        if self.photo:
            img = Image.open(self.photo)
            img = img.resize((300, 200), Image.LANCZOS)  # LANCZOS = качественный алгоритм
            
            buffer = BytesIO()
            # Определить формат (JPEG/PNG/etc):
            img_format = img.format or "JPEG"
            img.save(buffer, format=img_format)
            buffer.seek(0)
            
            # Заменить файл в поле (без сохранения в БД — save=False):
            self.photo.save(
                self.photo.name,
                ContentFile(buffer.getvalue()),
                save=False
            )
        
        super().save(*args, **kwargs)
```

> **Важно:** Ресайз делать **после** получения старого фото из БД, но **до** `super().save()`.

---

## 9. Полный код Product с ресайзом

```python
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.db import models


class Product(models.Model):
    article = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=20, default="шт.")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    manufacturer = models.CharField(max_length=200)
    supplier = models.ForeignKey("Supplier", on_delete=models.CASCADE)
    category = models.CharField(max_length=200)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    quantity = models.IntegerField(default=0)
    description = models.TextField()
    photo = models.ImageField(upload_to="products/", null=True, blank=True)

    def save(self, *args, **kwargs):
        # Удалить старое фото при замене
        try:
            this = Product.objects.get(id=self.id)
            if this.photo and self.photo and this.photo != self.photo:
                this.photo.delete(save=False)
        except Exception:
            pass
        
        # Ресайз нового фото до 300x200
        if self.photo:
            img = Image.open(self.photo)
            img = img.resize((300, 200), Image.LANCZOS)
            buffer = BytesIO()
            img.save(buffer, format=img.format or "JPEG")
            buffer.seek(0)
            self.photo.save(self.photo.name, ContentFile(buffer.getvalue()), save=False)
        
        super().save(*args, **kwargs)

    @property
    def final_price(self):
        return self.price * (1 - self.discount / 100) if self.discount else self.price
```

---

## 10. Базовый вариант без ресайза (из demoexam_26)

Если ресайз не требуется — используй более простую версию:

```python
def save(self, *args, **kwargs):
    try:
        this = Product.objects.get(id=self.id)
        if this.photo and self.photo and this.photo != self.photo:
            this.photo.delete(save=False)
    except Exception:
        pass
    super().save(*args, **kwargs)
```

---

## 11. Частые ошибки

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `HINT: Pillow must be installed` | Pillow не установлен | `uv add pillow` |
| Фото не отображается (404) | Нет раздачи media в urls.py | Добавить `urlpatterns += static(...)` |
| Фото не отображается (пустой src) | Используется `.path` вместо `.url` | Заменить на `{{ photo.url }}` |
| Файл не загружается | Нет `enctype="multipart/form-data"` | Добавить в тег `<form>` |
| `ValueError: seek of closed file` | Файл закрыт до ресайза | Читать/писать в правильном порядке |
