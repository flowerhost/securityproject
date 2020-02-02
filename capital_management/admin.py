from django.contrib import admin
from django import forms

from .models import CapitalAccount, StockDetails, Broker, Positions, Clearance, EventLog


# Register your models here.


class MyAdminSite(admin.AdminSite):
    """
    class MyAdminSite(admin.AdminSite):
    调整页面头部显示内容和页面标题
    """
    site_header = '证券资产管理系统'  # 此处设置页面显示标题
    site_title = '证券资产'  # 此处设置页面头部标题


admin.site = MyAdminSite(name='management')


class BrokerAdmin(admin.ModelAdmin):
    list_display = ['name', 'rate', 'stamp_duty', 'transfer_fee', 'date_added']


class PositionsAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'cost', 'amount', 'date']
    list_filter = ['name']


class PositionsInLine(admin.TabularInline):
    """
    设置内联：CapitalAccount和Positions
    TabularInLine: 表格式
    StackedInLine: 默认，竖列显示
    """
    model = Positions
    extra = 1
    fields = ['name', 'code', 'cost', 'amount', 'date']
    # TODO: 内联模版 template= 'capital_management/admin/***.html 从而实现定制化显示


class CapitalAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'broker', 'total_assets', 'market_capital', 'fund_balance', 'position_gain_loss',
                    'initial_capital', 'date']
    list_filter = ['name', 'broker', 'date']

    # 内联功能
    def get_form(self, request, obj=None, **args):
        defaults = {}
        if obj is not None:

            if len(Positions.objects.filter(id=obj.id)) == 1:
                self.inlines = [PositionsInLine]  # 设置内联
            else:
                self.inlines = []

        defaults.update(args)
        return super(CapitalAccountAdmin, self).get_form(request, obj, **defaults)


class StockDetailsForm(forms.ModelForm):
    """设置表单编辑页面格式"""
    # 字段集分组显示


    class Meta:
        forms.model = StockDetails
        # TODO: 完成表单个性化
        widgets = {

        }


class StockDetailsAdmin(admin.ModelAdmin):
    # 设置编辑表单页面格式
    form = StockDetailsForm
    fieldsets = (
        ("交易对象", {"fields": [('name', 'code', 'account')]}),
        ("交易详情", {"fields": ['flag', ('price', 'quantity', 'brokerage', 'stamp_duty', 'transfer_fee', 'total_capital')]})
    )

    # 设置可显示字段
    list_display = ['name', 'code', 'colored_flag', 'price', 'quantity', 'transact_date', 'brokerage', 'stamp_duty',
                    'transfer_fee', 'total_capital', 'account']

    # 设置那些字段可以进入编辑表单
    list_display_links = ['name', 'code']

    # 筛选器
    list_filter = ['transaction_date', 'name', 'code']  # 过滤栏
    search_fields = ['name', 'code']  # 搜索栏
    date_hierarchy = 'transaction_date'  # 时间分层

    # ordering设置默认排序，负号表示降序排序
    ordering = ['-transaction_date']

    # list_per_page 设置每页显示多少条记录，默认 100条
    list_per_page = 50

    # 操作项功能显示位置设置，两个都为True则顶部和底部都显示
    actions_on_top = True
    actions_on_bottom = True

    # 字段为空值显示的内容
    empty_value_display = '-空白-'


class ClearanceAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'open_date', 'clear_date', 'invest_capital', 'accumulate_capital', 'fee',
                    'profit', 'account']


admin.site.register(CapitalAccount, CapitalAccountAdmin)
admin.site.register(StockDetails, StockDetailsAdmin)
admin.site.register(Broker, BrokerAdmin)
admin.site.register(Positions, PositionsAdmin)
admin.site.register(Clearance, ClearanceAdmin)
admin.site.register(EventLog)
