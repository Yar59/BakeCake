# Generated by Django 3.2.16 on 2022-11-28 17:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bakery', '0006_auto_20221125_1929'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('1', 'Ожидает оплаты'), ('2', 'Принят к обработке'), ('3', 'Готовится'), ('4', 'Передан в доставку'), ('5', 'Завершен')], default='1', max_length=20, verbose_name='Статус заказа'),
        ),
    ]
