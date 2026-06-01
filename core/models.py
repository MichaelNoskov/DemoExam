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
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    count = models.IntegerField()
