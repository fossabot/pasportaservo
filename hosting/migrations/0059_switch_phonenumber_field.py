# Generated by Django 2.2.19 on 2021-03-21 23:32

from django.db import migrations
import hosting.fields


class Migration(migrations.Migration):

    dependencies = [
        ('hosting', '0058_countryregion_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='phone',
            name='number',
            field=hosting.fields.PhoneNumberField(
                help_text='International number format begining with the plus sign (e.g.: +31 10 436 1044)',
                max_length=128,
                region=None,
                verbose_name='number'),
        ),
    ]
