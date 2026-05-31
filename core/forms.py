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
        # Форматируем дату для datetime-local инпута при редактировании
        if self.instance.pk and self.instance.delivery_date:
            self.initial["delivery_date"] = self.instance.delivery_date.strftime(
                "%Y-%m-%dT%H:%M"
            )

    def clean_pickup_code(self):
        code = self.cleaned_data.get("pickup_code")
        if code is not None and code < 0:
            raise forms.ValidationError("Код получения не может быть отрицательным")
        return code
