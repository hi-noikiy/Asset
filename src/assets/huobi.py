# -*- coding:utf-8 -*-

"""
Huobi 账户资产

Author: HuangTao
Date:   2019/01/20
"""

from quant.const import HUOBI
from quant.utils import tools
from quant.utils import logger
from quant.event import EventAsset
from quant.tasks import LoopRunTask
from quant.platform.huobi import HuobiRestAPI


class HuobiAsset:
    """ 账户资金
    self._assets
    {
        "BTC": {
            "free": 11.11,
            "locked": 22.22,
            "total": 33.33
        },
        ...
    }
    """

    def __init__(self, account, access_key, secret_key, host=None):
        """ 初始化
        @param host 请求的host
        @param account 资产账户
        @param access_key 请求的access_key
        @param secret_key 请求的secret_key
        """
        self._platform = HUOBI
        self._host = host or "https://api.huobi.pro"
        self._account = account
        self._access_key = access_key
        self._secret_key = secret_key
        self._update_interval = 10  # 更新时间间隔(秒)

        self._assets = {}  # 所有资金详情

        # 创建rest api请求对象
        self._rest_api = HuobiRestAPI(self._host, self._access_key, self._secret_key)

        # 注册心跳定时任务
        LoopRunTask.register(self.check_asset_update, self._update_interval)

    async def check_asset_update(self, *args, **kwargs):
        """ 检查账户资金是否更新
        """
        result, error = await self._rest_api.get_account_balance()
        if error:
            logger.warn("platform:", self._platform, "account:", self._account, "get asset info failed!", caller=self)
            return

        temps = {}
        for item in result.get("list"):
            name = item.get("currency").upper()
            t = item.get("type")
            b = float(item.get("balance"))
            if name not in temps:
                temps[name] = {}
            if t == "trade":
                temps[name]["total"] = b
            else:
                temps[name]["locked"] = b

        assets = {}
        for name, item in temps.items():
            if item["total"] <= 0:
                continue
            assets[name] = {
                "free": "%.8f" % (item["total"] - item["locked"]),
                "locked": "%.8f" % item["locked"],
                "total": "%.8f" % item["total"]
            }

        if assets == self._assets:
            update = False
        else:
            update = True
        self._assets = assets

        # 推送当前资产
        timestamp = tools.get_cur_timestamp_ms()
        EventAsset(self._platform, self._account, self._assets, timestamp, update).publish()
        logger.info("platform:", self._platform, "account:", self._account, "asset:", self._assets, caller=self)
