import django.db.models.deletion
from django.db import migrations, models


def populate_fk_references(apps, schema_editor):
    """Переносим текстовые category_text/manufacturer_text в FK-таблицы."""
    Product = apps.get_model("core", "Product")
    Category = apps.get_model("core", "Category")
    Manufacturer = apps.get_model("core", "Manufacturer")

    for product in Product.objects.all():
        if product.category_text:
            cat, _ = Category.objects.get_or_create(name=product.category_text)
            product.category = cat
        if product.manufacturer_text:
            mfr, _ = Manufacturer.objects.get_or_create(name=product.manufacturer_text)
            product.manufacturer = mfr
        product.save()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_alter_product_discount"),
    ]

    operations = [
        # Переименовываем старые текстовые поля во временные имена
        migrations.RenameField("product", "category", "category_text"),
        migrations.RenameField("product", "manufacturer", "manufacturer_text"),

        # Создаём новые справочные таблицы
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Manufacturer",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, unique=True)),
            ],
        ),

        # Добавляем nullable FK-поля
        migrations.AddField(
            model_name="product",
            name="category",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to="core.category"),
        ),
        migrations.AddField(
            model_name="product",
            name="manufacturer",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to="core.manufacturer"),
        ),

        # Data migration: заполняем FK из текстовых полей
        migrations.RunPython(populate_fk_references, migrations.RunPython.noop),

        # Делаем FK обязательными
        migrations.AlterField(
            model_name="product",
            name="category",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.category"),
        ),
        migrations.AlterField(
            model_name="product",
            name="manufacturer",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.manufacturer"),
        ),

        # Удаляем старые текстовые поля
        migrations.RemoveField(model_name="product", name="category_text"),
        migrations.RemoveField(model_name="product", name="manufacturer_text"),

        # Меняем CASCADE → PROTECT для целостности
        migrations.AlterField(
            model_name="product",
            name="supplier",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.supplier"),
        ),
        migrations.AlterField(
            model_name="orderitem",
            name="product",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.product"),
        ),
    ]
