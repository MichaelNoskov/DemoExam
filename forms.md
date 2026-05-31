# Формы Django (ModelForm)

← [Назад к пайплайну](README.md)

---

## 1. Зачем формы?

Django-формы решают сразу несколько задач:
- Рендеринг HTML-полей (`{{ form }}` в шаблоне)
- Валидация данных (тип, обязательность, правила)
- Преобразование данных в объекты модели
- Защита от XSS

---

## 2. ModelForm — форма из модели

`ModelForm` автоматически создаёт поля из полей модели.

```python
from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product           # из какой модели
        fields = ["name", "price", "description"]  # какие поля включить
        # или fields = "__all__"  # все поля
        # или exclude = ["id"]    # все кроме указанных
```

---

## 3. Meta — настройки формы

```python
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["article", "name", "price", "quantity"]
        
        labels = {
            "article": "Артикул",
            "name": "Название",
            "price": "Цена (руб.)",
        }
        
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "price": forms.NumberInput(attrs={"step": "0.01"}),
        }
        
        help_texts = {
            "article": "Уникальный код товара",
        }
        
        error_messages = {
            "article": {
                "unique": "Товар с таким артикулом уже существует",
            }
        }
```

---

## 4. Дополнительные поля (не из модели)

```python
class ProductForm(forms.ModelForm):
    # Поле "поставщик" — пользователь вводит название, не выбирает из списка
    supplier_name = forms.CharField(
        label="Поставщик",
        required=True,
        max_length=200,
    )
    
    class Meta:
        model = Product
        fields = ["article", "name", ...]  # supplier_name НЕ включаем сюда
```

---

## 5. Предзаполнение при редактировании

```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # self.instance = объект из БД (при редактировании)
    if self.instance.pk:  # если это редактирование (pk существует)
        if self.instance.supplier:
            self.fields["supplier_name"].initial = self.instance.supplier.name
```

---

## 6. Валидация полей — clean_X

Метод `clean_FIELD_NAME` вызывается при валидации этого поля:

```python
def clean_price(self):
    price = self.cleaned_data.get("price")
    if price is None:
        return price
    if price < 0:
        raise forms.ValidationError("Цена не может быть отрицательной")
    return price  # обязательно вернуть значение

def clean_quantity(self):
    qty = self.cleaned_data.get("quantity")
    if qty < 0:
        raise forms.ValidationError("Количество не может быть отрицательным")
    return qty
```

### Валидация нескольких полей — clean()

```python
def clean(self):
    cleaned_data = super().clean()
    price = cleaned_data.get("price")
    discount = cleaned_data.get("discount")
    
    if price and discount and discount >= 100:
        raise forms.ValidationError("Скидка не может быть 100% или больше")
    
    return cleaned_data
```

---

## 7. Переопределение save()

```python
def save(self, commit=True):
    # Получить объект модели без сохранения в БД
    instance = super().save(commit=False)
    
    # Своя логика:
    supplier, _ = Supplier.objects.get_or_create(
        name=self.cleaned_data["supplier_name"].strip()
    )
    instance.supplier = supplier
    
    if commit:
        instance.save()  # сохранить в БД
    return instance
```

> `commit=False` даёт объект, но не сохраняет его. Нужно для случаев когда надо добавить данные перед сохранением.

---

## 8. Рендеринг в шаблоне

```html
<!-- Вывести всю форму сразу (автоматически) -->
{{ form }}
{{ form.as_p }}      <!-- каждое поле в <p> -->
{{ form.as_table }}  <!-- в <tr><td> -->
{{ form.as_ul }}     <!-- в <li> -->

<!-- Вывести конкретное поле -->
{{ form.name }}
{{ form.name.label }}
{{ form.name.errors }}
```

Не забыть `enctype="multipart/form-data"` если есть ImageField:
```html
<form method="post" enctype="multipart/form-data">
    {% csrf_token %}
    {{ form }}
    <button type="submit">Сохранить</button>
</form>
```

---

## 9. Полный код — core/forms.py

```python
from django import forms

from .models import Order, PickupPoint, Product, Supplier


class ProductForm(forms.ModelForm):
    # Текстовое поле для ввода названия поставщика
    supplier_name = forms.CharField(label="Поставщик", required=True)

    class Meta:
        model = Product
        fields = [
            "article",
            "name",
            "unit",
            "price",
            "discount",
            "quantity",
            "description",
            "photo",
            "category",
            "manufacturer",
        ]
        labels = {
            "article": "Артикул",
            "name": "Название",
            "unit": "Единица измерения",
            "price": "Цена",
            "discount": "Скидка",
            "quantity": "Количество",
            "description": "Описание",
            "photo": "Фото",
            "category": "Категория",
            "manufacturer": "Производитель",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Предзаполняем поле поставщика при редактировании
        if self.instance.pk:
            if self.instance.supplier:
                self.fields["supplier_name"].initial = self.instance.supplier.name

    def save(self, commit=True):
        # Найти существующего поставщика или создать нового
        supplier, _ = Supplier.objects.get_or_create(
            name=self.cleaned_data["supplier_name"].strip()
        )

        instance = super().save(commit=False)
        instance.supplier = supplier

        if commit:
            instance.save()
        return instance

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price < 0:
            raise forms.ValidationError("Цена не может быть отрицательной")
        return price

    def clean_quantity(self):
        qty = self.cleaned_data.get("quantity")
        if qty < 0:
            raise forms.ValidationError("Количество не может быть отрицательным")
        return qty


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["delivery_date", "pickup_point", "client_name", "pickup_code", "status"]
        labels = {
            "delivery_date": "Дата доставки",
            "pickup_point": "Пункт выдачи",
            "client_name": "ФИО клиента",
            "pickup_code": "Код получения",
            "status": "Статус",
        }
        widgets = {
            "delivery_date": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.delivery_date:
            self.initial["delivery_date"] = self.instance.delivery_date.strftime(
                "%Y-%m-%dT%H:%M"
            )

    def clean_pickup_code(self):
        code = self.cleaned_data.get("pickup_code")
        if code is not None and code < 0:
            raise forms.ValidationError("Код получения не может быть отрицательным")
        return code
```

### ID readonly при редактировании

`id` не включается в поля формы — отображается отдельно в шаблоне как disabled-поле:

```html
{% if is_edit %}
<p><strong>ID:</strong>
  <input type="text" value="{{ object.pk }}" disabled
         style="background: #eee; border: 1px solid #ccc; padding: 3px 6px;">
</p>
{% endif %}
```

`disabled` — поле видно, но не редактируется и не отправляется в форме.

---

## 10. Как работает форма в View

```python
class ProductCreateView(CreateView):
    form_class = ProductForm
    ...
    
    # Django делает это автоматически при GET/POST:
    # GET: form = ProductForm()          → пустая форма
    # POST: form = ProductForm(request.POST, request.FILES)
    #       → заполнена данными из запроса
    
    # request.FILES нужен для загрузки файлов (ImageField)
    # Django CBV передаёт его автоматически
```

---

## 11. Типы полей форм

| Поле | Виджет по умолчанию | Пример |
|------|---------------------|--------|
| `forms.CharField()` | `TextInput` | имена, артикулы |
| `forms.DecimalField()` | `NumberInput` | цены, скидки |
| `forms.IntegerField()` | `NumberInput` | количество |
| `forms.EmailField()` | `EmailInput` | email |
| `forms.BooleanField()` | `CheckboxInput` | да/нет |
| `forms.ChoiceField(choices=...)` | `Select` | выбор из вариантов |
| `forms.ImageField()` | `FileInput` | загрузка фото |
| `forms.DateField()` | `DateInput` | дата |

Виджеты переопределяются в `Meta.widgets` или напрямую в поле:
```python
price = forms.DecimalField(
    widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"})
)
```
