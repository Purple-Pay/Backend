# Generated by Django 4.1.7 on 2023-08-08 07:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0006_paymentburneraddress_conversion_rate_in_usd'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentburneraddress',
            name='qr_code_string',
            field=models.CharField(blank=True, max_length=512, null=True, verbose_name='QR Code String'),
        ),
    ]
