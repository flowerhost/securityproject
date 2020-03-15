# Generated by Django 2.1.4 on 2020-03-14 21:56

import datetime
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('capital_management', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='evaluatestocks',
            name='express_date',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='业绩快报日期'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='evaluatestocks',
            name='express_eps_rate',
            field=models.FloatField(default=0, verbose_name='业绩快报'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='accountsurplus',
            name='date',
            field=models.DateField(default=datetime.datetime(2020, 3, 14, 21, 55, 24, 319738), verbose_name='结算日期'),
        ),
        migrations.AlterField(
            model_name='capitalaccount',
            name='date',
            field=models.DateField(default=datetime.datetime(2020, 3, 14, 21, 55, 24, 319113), verbose_name='创建日期'),
        ),
        migrations.AlterField(
            model_name='mystocklists',
            name='trade_date',
            field=models.DateField(default=datetime.datetime(2020, 3, 14, 21, 55, 24, 327382), verbose_name='交易日期'),
        ),
        migrations.AlterField(
            model_name='positions',
            name='date',
            field=models.DateField(default=datetime.datetime(2020, 3, 14, 21, 55, 24, 323101), verbose_name='结算日起'),
        ),
        migrations.AlterField(
            model_name='tradedailyreport',
            name='date',
            field=models.DateField(default=datetime.datetime(2020, 3, 14, 21, 55, 24, 322372), verbose_name='结算日期'),
        ),
        migrations.AlterField(
            model_name='tradelists',
            name='date',
            field=models.DateField(default=datetime.datetime(2020, 3, 14, 21, 55, 24, 320821), verbose_name='交易日期'),
        ),
        migrations.AlterField(
            model_name='tradeperformance',
            name='date',
            field=models.DateField(default=datetime.datetime(2020, 3, 14, 21, 55, 24, 321756), verbose_name='评价日期'),
        ),
    ]
