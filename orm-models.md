# ORM-модели Django

← [Назад к пайплайну](README.md)

---

## 1. Типы полей — справочник

### Текстовые

| Поле | Когда использовать | Пример |
|------|-------------------|--------|
| `CharField(max_length=N)` | Короткий текст (имя, артикул) | `name = CharField(max_length=255)` |
| `TextField()` | Длинный текст (описание, адрес) | `description = TextField()` |
| `EmailField()` | Email (валидирует формат) | `email = EmailField()` |
| `SlugField()` | URL-совместимый текст | редко |

### Числовые

| Поле | Когда использовать | Пример |
|------|-------------------|--------|
| `IntegerField()` | Целое число | `quantity = IntegerField(default=0)` |
| `DecimalField(max_digits, decimal_places)` | Деньги, проценты | `price = DecimalField(max_digits=10, decimal_places=2)` |
| `FloatField()` | Число с плавающей точкой | редко |
| `BigAutoField()` | Авто-инкремент PK | автоматически |

### Дата и время

| Поле | Когда использовать | Пример |
|------|-------------------|--------|
| `DateTimeField(auto_now_add=True)` | Дата создания (не меняется) | `order_date = DateTimeField(auto_now_add=True)` |
| `DateTimeField(auto_now=True)` | Дата последнего изменения | `updated_at = DateTimeField(auto_now=True)` |
| `DateTimeField()` | Дата, задаваемая вручную | `delivery_date = DateTimeField()` |
| `DateField()` | Только дата (без времени) | `DateField()` |

### Файлы

| Поле | Когда использовать | Пример |
|------|-------------------|--------|
| `ImageField(upload_to="folder/")` | Загружаемые изображения | `photo = ImageField(upload_to="products/", null=True, blank=True)` |
| `FileField(upload_to="folder/")` | Любые файлы | редко |

> `ImageField` требует установленного **Pillow**.

### Логические

| Поле | Когда использовать | Пример |
|------|-------------------|--------|
| `BooleanField(default=False)` | Да/Нет флаг | `is_active = BooleanField(default=True)` |

### Связи

| Поле | Тип связи | Пример |
|------|-----------|--------|
| `ForeignKey(Model, on_delete=...)` | Многие к одному (N:1) | `supplier = ForeignKey(Supplier, on_delete=CASCADE)` |
| `ManyToManyField(Model)` | Многие ко многим | через промежуточную таблицу |
| `OneToOneField(Model, on_delete=...)` | Один к одному | `profile = OneToOneField(User, ...)` |

---

## 2. Параметры полей

| Параметр | Значение | Пример использования |
|----------|----------|---------------------|
| `max_length=N` | Макс. длина строки | `CharField(max_length=50)` |
| `null=True` | Разрешить NULL в БД | `photo = ImageField(null=True)` |
| `blank=True` | Разрешить пустую строку в форме | `photo = ImageField(blank=True)` |
| `default=X` | Значение по умолчанию | `quantity = IntegerField(default=0)` |
| `unique=True` | Уникальное значение | `article = CharField(unique=True)` |
| `verbose_name="..."` | Название для форм/admin | `CharField(verbose_name="Артикул")` |

> **null vs blank:** `null=True` для БД, `blank=True` для форм. Для текстовых полей используй оба вместе если поле необязательно.

---

## 3. on_delete — что происходит при удалении родителя

| Значение | Что происходит |
|----------|---------------|
| `CASCADE` | Удалить вместе с родителем |
| `SET_NULL` | Поставить NULL (требует `null=True`) |
| `PROTECT` | Запретить удаление (исключение) |
| `RESTRICT` | Аналогично PROTECT, но мягче |
| `DO_NOTHING` | Ничего не делать (опасно) |

**В проекте:**
- `supplier`, `category`, `manufacturer` в Product → `PROTECT` (нельзя удалить справочник, если на него ссылаются товары; попытка вызовет `ProtectedError`)
- `product` в OrderItem → `PROTECT` (нельзя удалить товар, если он есть в заказах)
- `order` в OrderItem → `CASCADE` (удалили заказ — удались его позиции, это логично)
- `user` → `SET_NULL` (удалили пользователя — заказ остаётся, user=NULL)
- `role` → `SET_NULL` (удалили роль — пользователь остаётся без роли)

> **Правило выбора:** справочные данные (Supplier, Category, Manufacturer) защищают сами себя через `PROTECT`. Зависимые данные (OrderItem от Order) удаляются каскадом. `SET_NULL` — для «мягких» связей, где объект может существовать без родителя.

---

## 3.1 Третья нормальная форма (3НФ) и справочные таблицы

**Нарушение 3НФ:** если несколько строк хранят одно и то же значение текстом — это избыточность.

```python
# ПЛОХО — category и manufacturer повторяются в каждой строке Product
class Product(models.Model):
    category = models.CharField(max_length=200)     # "Ботинки" × 100 строк
    manufacturer = models.CharField(max_length=200) # "Nike" × 50 строк
```

**Решение — вынести повторяющиеся значения в справочные таблицы:**

```python
class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)

class Manufacturer(models.Model):
    name = models.CharField(max_length=200, unique=True)

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.PROTECT)
```

Теперь "Ботинки" хранится один раз в `Category`, все товары ссылаются на неё по `id`.

**Миграция при смене типа поля (CharField → ForeignKey)** требует data migration — промежуточный шаг, который создаёт FK-объекты из существующих текстов:

```python
# В файле миграции
def populate_fk_references(apps, schema_editor):
    Product = apps.get_model("core", "Product")
    Category = apps.get_model("core", "Category")
    for product in Product.objects.all():
        cat, _ = Category.objects.get_or_create(name=product.category_text)
        product.category = cat
        product.save()

class Migration(migrations.Migration):
    operations = [
        migrations.RenameField("product", "category", "category_text"),  # сохранить старое
        migrations.CreateModel("Category", ...),
        migrations.AddField("product", "category", ForeignKey(null=True, ...)),
        migrations.RunPython(populate_fk_references, migrations.RunPython.noop),
        migrations.AlterField("product", "category", ForeignKey(...)),    # убрать null
        migrations.RemoveField("product", "category_text"),               # удалить старое
    ]
```

---

## 4. Специальные конструкции

### `__str__` — строковое представление объекта

```python
class Role(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self) -> str:
        return self.name  # Role(name="admin") → "admin"
```

Нужно для: Django Admin, выпадающие списки, отладка.

### `@property` — вычисляемое поле

```python
class Product(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    @property
    def final_price(self):
        return self.price * (1 - self.discount / 100) if self.discount else self.price
```

Обращение: `product.final_price` (как обычное поле, без `()`).

### `class Meta` — метаданные модели

```python
class Product(models.Model):
    name = models.CharField(max_length=255)
    
    class Meta:
        verbose_name = "Товар"           # название в единственном числе
        verbose_name_plural = "Товары"   # во множественном
        ordering = ["name"]              # сортировка по умолчанию
```

### `AbstractUser` — расширение встроенного пользователя

```python
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=255)
    # Уже унаследованы: username, password, email, is_staff, is_active, date_joined
```

> После создания этой модели **обязательно** прописать в settings.py:
> ```python
> AUTH_USER_MODEL = "core.User"
> ```
> Делать это **до первой миграции**! Иначе конфликт.

---

## 5. Переопределение save()

```python
def save(self, *args, **kwargs):
    try:
        # Получить текущее состояние из БД (до сохранения)
        this = Product.objects.get(id=self.id)
        # Если фото изменилось — удалить старое с диска
        if this.photo and self.photo and this.photo != self.photo:
            this.photo.delete(save=False)  # save=False = не вызывать save() повторно
    except Exception:
        pass  # При создании нового объекта self.id = None, get() выбросит исключение
    super().save(*args, **kwargs)  # Вызвать оригинальный save()
```

---

## 6. Полный код проекта — core/models.py

```python
from django.contrib.auth.models import AbstractUser
from django.db import models
from PIL import Image


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Name of the role")

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=255)


class Supplier(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self) -> str:
        return self.name


# Справочные таблицы для 3НФ — выделены из Product,
# чтобы не хранить повторяющийся текст в каждой строке
class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self) -> str:
        return self.name


class Manufacturer(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self) -> str:
        return self.name


class PickupPoint(models.Model):
    address = models.TextField()

    def __str__(self) -> str:
        return self.address[:50]


class Product(models.Model):
    article = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=20, default="шт.")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.PROTECT)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    quantity = models.IntegerField(default=0)
    description = models.TextField()
    photo = models.ImageField(upload_to="products/", null=True, blank=True)

    def save(self, *args, **kwargs):
        try:
            this = Product.objects.get(id=self.id)
            if this.photo and self.photo and this.photo != self.photo:
                this.photo.delete(save=False)
        except Exception:
            pass
        super().save(*args, **kwargs)
        # Ресайз фото до 300×200 пикселей после сохранения на диск
        if self.photo:
            try:
                img = Image.open(self.photo.path)
                img = img.resize((300, 200), Image.LANCZOS)
                img.save(self.photo.path)
            except Exception:
                pass

    @property
    def final_price(self):
        return self.price * (1 - self.discount / 100) if self.discount else self.price


class Order(models.Model):
    order_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateTimeField()
    pickup_point = models.ForeignKey(PickupPoint, on_delete=models.CASCADE)
    client_name = models.CharField(max_length=255, null=True, blank=True)
    pickup_code = models.IntegerField()
    status = models.CharField(max_length=50, default="Новый")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)  # PROTECT: нельзя удалить товар из заказа
    count = models.IntegerField()
```

---

## 7. Регистрация в admin.py

```python
# core/admin.py
from django.contrib import admin
from .models import Category, Manufacturer, Order, OrderItem, PickupPoint, Product, Role, Supplier, User

admin.site.register(Role)
admin.site.register(User)
admin.site.register(Supplier)
admin.site.register(PickupPoint)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
```

---

## 8. Команды

```bash
# Создать файлы миграций (после написания/изменения models.py)
python manage.py makemigrations

# Применить миграции к БД
python manage.py migrate

# Посмотреть SQL который выполнит миграция:
python manage.py sqlmigrate core 0001

# Создать суперпользователя для Django Admin:
python manage.py createsuperuser
```

---

## 9. Частые ошибки

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `ValueError: AUTH_USER_MODEL refers to model...` | Модель User не зарегистрирована | Добавить `"core"` в INSTALLED_APPS |
| `django.db.utils.ProgrammingError` | Миграции не применены | `python manage.py migrate` |
| `cannot import name 'User' from 'core.models'` | Опечатка или неправильный импорт | Проверить имя класса |
| `HINT: Pillow must be installed` | Используется ImageField без Pillow | `uv add pillow` |
