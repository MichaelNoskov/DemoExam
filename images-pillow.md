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

## 8. Ресайз изображений через Pillow

ТЗ требует: "Изображение загружается, изменяется размер до 300×200".

Подход: сначала сохранить файл на диск через `super().save()`, затем открыть его Pillow и перезаписать.

```python
from PIL import Image

class Product(models.Model):
    # ...поля...
    
    def save(self, *args, **kwargs):
        # 1. Удалить старое фото если заменяется:
        try:
            this = Product.objects.get(id=self.id)
            if this.photo and self.photo and this.photo != self.photo:
                this.photo.delete(save=False)
        except Exception:
            pass
        
        # 2. Сохранить в БД и на диск:
        super().save(*args, **kwargs)
        
        # 3. Ресайз сохранённого файла (теперь self.photo.path доступен):
        if self.photo:
            try:
                img = Image.open(self.photo.path)
                img = img.resize((300, 200), Image.LANCZOS)
                img.save(self.photo.path)   # перезаписать файл на диске
            except Exception:
                pass
```

> **Почему `super().save()` первым:** До его вызова `self.photo` — это ещё `InMemoryUploadedFile` (данные в памяти). `self.photo.path` становится доступным только после сохранения файла на диск.

---

## 9. Полный код Product.save() (финальная версия с ресайзом)

```python
from PIL import Image
from django.db import models


class Product(models.Model):
    # ...поля...
    photo = models.ImageField(upload_to="products/", null=True, blank=True)

    def save(self, *args, **kwargs):
        # Удалить старое фото при замене
        try:
            this = Product.objects.get(id=self.id)
            if this.photo and self.photo and this.photo != self.photo:
                this.photo.delete(save=False)
        except Exception:
            pass
        # Сохранить файл на диск
        super().save(*args, **kwargs)
        # Ресайз до 300×200
        if self.photo:
            try:
                img = Image.open(self.photo.path)
                img = img.resize((300, 200), Image.LANCZOS)
                img.save(self.photo.path)
            except Exception:
                pass
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
