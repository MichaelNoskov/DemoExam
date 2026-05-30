# Скрипт импорта CSV в БД

← [Назад к пайплайну](README.md)

> Это одна из **вариативных задач** (5 баллов). Management command — стандартный Django-способ создавать CLI-скрипты.

---

## 1. Что такое Management Command

Django позволяет создавать собственные команды для `manage.py`:

```bash
python manage.py import_data   # наша команда
python manage.py migrate       # встроенная команда
```

Команды живут в `core/management/commands/`. Каждый файл = одна команда с именем файла.

---

## 2. Структура Management Command

```python
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Описание команды (показывается в --help)"
    
    def add_arguments(self, parser):
        # Опционально: добавить аргументы командной строки
        parser.add_argument("--path", type=str, default="data/")
    
    def handle(self, *args, **options):
        # Основная логика команды
        self.stdout.write("Начало импорта...")
        
        # ... код ...
        
        self.stdout.write(self.style.SUCCESS("Импорт завершён!"))
```

Минимальная версия (без аргументов):
```python
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        # всё что нужно сделать
        pass
```

---

## 3. Работа с CSV — модуль `csv`

### DictReader — читает строки как словари

```python
import csv

with open("data.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)  # первая строка = заголовки
    for row in reader:
        print(row["name"], row["price"])  # доступ по имени столбца
```

### DictReader без заголовков (задаём сами)

```python
with open("pp.csv") as f:
    reader = csv.DictReader(f, ["address"])  # сами называем столбцы
    for row in reader:
        print(row["address"])
```

### Кодировка utf-8-sig

Excel экспортирует CSV с **BOM** (Byte Order Mark) — невидимый символ в начале файла. Если читать без `encoding="utf-8-sig"`, первый ключ словаря будет с мусором.

```python
# Неправильно для Excel-файлов:
with open("products.csv", encoding="utf-8") as f:
    ...

# Правильно:
with open("products.csv", encoding="utf-8-sig") as f:
    ...
```

---

## 4. Идемпотентные операции ORM

**Идемпотентность** = запускать скрипт сколько угодно раз, результат одинаковый (нет дублирования).

### get_or_create — найти или создать

```python
# Возвращает (объект, был_создан)
supplier, created = Supplier.objects.get_or_create(name="Kari")
# Если "Kari" есть — вернёт его. Нет — создаст.
```

### update_or_create — обновить или создать

```python
# Ищет по `article`, обновляет `defaults`
Product.objects.update_or_create(
    article=row["article"],  # ключ поиска
    defaults=row             # поля для обновления/создания
)
```

### Проверка и условное создание

```python
if not User.objects.filter(username=row["login"]).exists():
    user = User.objects.create(username=row["login"], ...)
```

---

## 5. Пароли пользователей

Django хранит пароли в виде хеша. Нельзя записать пароль напрямую:

```python
# Неправильно:
User.objects.create(username="user1", password="mypassword")  # сохранит открытый текст!

# Правильно:
user = User.objects.create(username="user1", ...)
user.set_password("mypassword")  # хеширует и сохраняет
user.save()
```

---

## 6. Порядок импорта (важно!)

Из-за Foreign Key нужно импортировать в правильном порядке:

```
1. PickupPoint (pp.csv)         ← не зависит ни от чего
2. Supplier + Product           ← Product зависит от Supplier
3. Role + User                  ← User зависит от Role
4. Order + OrderItem            ← Order зависит от PickupPoint и User
                                   OrderItem зависит от Order и Product
```

---

## 7. Разбор сложного формата items

В `orders.csv` поле `items` хранит список: `"А112Т4, 2, F635R4, 2"`  
Формат: `артикул, количество, артикул, количество, ...`

```python
items = row["items"].split(",")
# items = ["А112Т4", " 2", " F635R4", " 2"]

for i in range(0, len(items), 2):        # шаг 2: берём пары
    art = items[i].strip()               # убрать пробелы
    qty = int(items[i + 1])              # следующий элемент = количество
    
    try:
        prod = Product.objects.get(article=art)
        OrderItem.objects.create(order=order, product=prod, count=qty)
    except Exception:
        pass  # артикул не найден — пропустить
```

---

## 8. Полный код — import_data.py

Файл: `core/management/commands/import_data.py`

```python
import csv
import os
from typing import Any

from django.core.management.base import BaseCommand

from core.models import Order, OrderItem, PickupPoint, Product, Role, Supplier, User


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> str | None:
        base_path = "part_1/add_2/import/"

        # 1. Пункты выдачи
        with open(os.path.join(base_path, "pp.csv")) as f:
            reader = csv.DictReader(f, ["address"])
            for row in reader:
                print(row)
                PickupPoint.objects.get_or_create(address=row["address"])

        # 2. Товары и поставщики
        with open(os.path.join(base_path, "products.csv"), encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                print(row)
                if not row:
                    continue

                sup_obj, _ = Supplier.objects.get_or_create(name=row["supplier"])
                row["supplier"] = sup_obj

                if row.get("photo") and not row["photo"].startswith("products/"):
                    row["photo"] = f"products/{row['photo']}"

                Product.objects.update_or_create(article=row["article"], defaults=row)

        # 3. Пользователи
        with open(os.path.join(base_path, "users.csv"), encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                print(row)
                if not row:
                    continue

                role_obj, _ = Role.objects.get_or_create(name=row["role"])
                if not User.objects.filter(username=row["login"]).exists():
                    user = User.objects.create(
                        username=row["login"], full_name=row["full_name"], role=role_obj
                    )
                    user.set_password(str(row["password"]).strip())
                    user.save()

        # 4. Заказы и позиции заказов
        with open(os.path.join(base_path, "orders.csv"), encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                print(row)
                if not row:
                    continue

                pp_obj = (
                    PickupPoint.objects.get(id=row["pp"])
                    if PickupPoint.objects.filter(id=row["pp"]).exists()
                    else PickupPoint.objects.first()
                )
                order, created = Order.objects.get_or_create(
                    id=row["id"],
                    defaults={
                        "order_date": row["order_date"],
                        "delivery_date": row["delivery_date"],
                        "client_name": row["client_name"],
                        "pickup_code": row["pickup_code"],
                        "status": row["status"],
                        "pickup_point": pp_obj,
                    },
                )
                if created:
                    items = row["items"].split(",")
                    for i in range(0, len(items), 2):
                        art = items[i].strip()
                        try:
                            prod = Product.objects.get(article=art)
                            OrderItem.objects.create(
                                order=order, product=prod, count=int(items[i + 1])
                            )
                        except Exception:
                            pass
```

---

## 9. CSV-файлы и их структура

**Расположение:** `part_1/add_2/import/`

### pp.csv — пункты выдачи (без заголовка)
```
420151, г. Лесной, ул. Вишневая, 32
420151, г. Лесной, ул. Садовая, 15
...
```
36 строк. Читается с заголовком `["address"]`.

### products.csv — товары (с заголовком)
```
article,name,unit,price,supplier,manufacturer,category,discount,quantity,description,photo
А112Т4,Ботинки,шт.,4990,Kari,Kari,Женская обувь,3,6,Женские ботинки...,1.jpg
```

### users.csv — пользователи (с заголовком)
```
role,full_name,email,login,password
admin,Никифорова Весения Николаевна,94d5ous@gmail.com,94d5ous@gmail.com,uzWC67
```

### orders.csv — заказы (с заголовком)
```
id,items,order_date,delivery_date,pp,client_name,pickup_code,status
1,"А112Т4, 2, F635R4, 2",2025-02-27,2025-04-20,1,Степанов Михаил,901,Завершен
```

---

## 10. Запуск и проверка

```bash
# Запустить импорт (из корня проекта, с активированным .venv)
python manage.py import_data

# Проверить что данные загружены:
python manage.py shell
>>> from core.models import Product, User
>>> Product.objects.count()   # должно быть 30
>>> User.objects.count()      # должно быть 10
```
