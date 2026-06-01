from django import forms
from django.forms import inlineformset_factory

from .models import Category, Manufacturer, Order, OrderItem, PickupPoint, Product, Supplier


class ProductForm(forms.ModelForm):
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
            "supplier",
        ]
        labels = {
            "article": "Артикул",
            "name": "Название",
            "unit": "Единица измерения",
            "price": "Цена",
            "discount": "Скидка (%)",
            "quantity": "Количество",
            "description": "Описание",
            "photo": "Фото",
            "category": "Категория",
            "manufacturer": "Производитель",
            "supplier": "Поставщик",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

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
            "status": forms.Select(choices=[
                ("Новый", "Новый"),
                ("В сборке", "В сборке"),
                ("Готов к выдаче", "Готов к выдаче"),
                ("Завершён", "Завершён"),
                ("Отменён", "Отменён"),
            ]),
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


OrderItemFormSet = inlineformset_factory(
    Order,
    OrderItem,
    fields=["product", "count"],
    labels={"product": "Товар", "count": "Количество"},
    extra=1,
    can_delete=True,
    min_num=0,
)
