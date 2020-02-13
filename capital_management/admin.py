from django.contrib import admin
# from django import forms
from .form import TradeListsForm

from .models import CapitalAccount, TradeLists, Broker, TradeDailyReport, Clearance, EventLog


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
    list_display = ['name', 'nick_name', 'rate', 'stamp_duty', 'transfer_fee', 'date_added']


class TradeDailyReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'cost', 'amount', 'date']
    list_filter = ['name']


class TradeDailyReportInLine(admin.TabularInline):
    """
    设置内联：CapitalAccount和Positions
    TabularInLine: 表格式
    StackedInLine: 默认，竖列显示
    """
    model = TradeDailyReport
    extra = 1
    fields = ['name', 'code', 'cost', 'amount', 'date']
    # TODO: 内联模版 template= 'capital_management/admin/***.html 从而实现定制化显示


class CapitalAccountAdmin(admin.ModelAdmin):
    list_display = ['broker', 'initial_capital', 'date']
    list_filter = ['broker', 'date']

    # 内联功能
    def get_form(self, request, obj=None, **args):
        defaults = {}
        if obj is not None:

            if len(TradeDailyReport.objects.filter(id=obj.id)) == 1:
                self.inlines = [TradeDailyReportInLine]  # 设置内联
            else:
                self.inlines = []

        defaults.update(args)
        return super(CapitalAccountAdmin, self).get_form(request, obj, **defaults)


class TradeListsAdmin(admin.ModelAdmin):
    # 设置编辑表单页面格式
    form = TradeListsForm
    fieldsets = (
        ("交易对象", {"fields": [('name', 'code', 'account')]}),
        ("交易详情", {"fields": ['flag', ('price', 'quantity', 'brokerage', 'stamp_duty', 'transfer_fee', 'total_fee',
                                      'transaction_date', 'total_capital')]})
    )

    # 设置可显示字段
    list_display = ['name', 'code', 'colored_flag', 'price', 'quantity', 'transact_date', 'brokerage', 'stamp_duty',
                    'transfer_fee', 'total_fee', 'total_capital', 'account']

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
admin.site.register(TradeLists, TradeListsAdmin)
admin.site.register(Broker, BrokerAdmin)
admin.site.register(TradeDailyReport, TradeDailyReportAdmin)
admin.site.register(Clearance, ClearanceAdmin)
admin.site.register(EventLog)
