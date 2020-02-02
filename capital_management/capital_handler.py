from capital_management import models


class UpdateData(object):
    def __init__(self, request, data):
        self.request = request
        self.data = data

    def _update_positions(self):
        """
        更新持股数据
        :return:
        """

    def _update_clearance(self):
        """
        更新清仓数据
        :return:
        """
    def _update_capital_account(self):
        """
        更新账户资产数据
        :return:
        """