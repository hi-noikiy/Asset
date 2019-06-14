# -*- coding:utf-8 -*-

"""
Deribit 账户资产
https://docs.deribit.com/v2/

Author: HuangTao
Date:   2019/04/20
"""

import json
import asyncio

from quant.utils import tools
from quant.utils import logger
from quant.const import DERIBIT
from quant.event import EventAsset
from quant.tasks import LoopRunTask
from quant.utils.websocket import Websocket
from quant.utils.decorator import async_method_locker


class DeribitAsset(Websocket):
    """ 账户资产
    """

    def __init__(self, account, access_key, secret_key, wss=None):
        """ 初始化
        @param wss websocket连接地址
        @param account 资产账户
        @param access_key 请求的access_key
        @param secret_key 请求的secret_key
        """
        self._platform = DERIBIT
        self._wss = wss or "wss://deribit.com"
        self._account = account
        self._access_key = access_key
        self._secret_key = secret_key
        self._update_interval = 10  # 更新时间间隔(秒)

        self._assets = {"BTC": {}, "ETH": {}}  # 所有资金详情
        self._last_assets = {}  # 上次推送的资产信息

        url = self._wss + "/ws/api/v2"
        super(DeribitAsset, self).__init__(url, send_hb_interval=5)

        self._query_id = 0  # 消息序号id，用来唯一标识请求消息
        self._queries = {}  # 未完成的post请求 {"request_id": future}

        self.initialize()

        # 注册定时任务
        LoopRunTask.register(self._do_auth, 60 * 60)  # 每隔1小时重新授权
        LoopRunTask.register(self._publish_asset, self._update_interval)  # 推送资产

        self._ok = False  # 是否建立授权成功的websocket连接

    async def connected_callback(self):
        """ 建立连接之后，授权登陆，然后订阅order和position
        """
        # 授权
        success, error = await self._do_auth()
        if error or not success.get("access_token"):
            logger.error("Websocket connection authorized failed:", error, caller=self)
            return
        self._ok = True

        # 授权成功之后，订阅数据
        method = "private/subscribe"
        params = {
            "channels": [
                "user.portfolio.btc",
                "user.portfolio.eth"
            ]
        }
        _, error = await self._send_message(method, params)
        if error:
            logger.error("subscribe asset error:", error, caller=self)
        else:
            logger.info("subscribe asset success.",caller=self)

    async def _do_auth(self, *args, **kwargs):
        """ 鉴权
        """
        method = "public/auth"
        params = {
            "grant_type": "client_credentials",
            "client_id": self._access_key,
            "client_secret": self._secret_key
        }
        success, error = await self._send_message(method, params)
        return success, error

    async def _send_message(self, method, params):
        """ 发送消息
        """
        f = asyncio.futures.Future()
        request_id = await self._generate_query_id()
        self._queries[request_id] = f
        data = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        await self.ws.send_json(data)
        logger.debug("send message:", data, caller=self)
        success, error = await f
        if error:
            logger.error("data:", data, "error:", error, caller=self)
        return success, error

    @async_method_locker("generate_query_id.locker")
    async def _generate_query_id(self):
        """ 生成query id，加锁，确保每个请求id唯一
        """
        self._query_id += 1
        return self._query_id

    @async_method_locker("process.locker")
    async def process(self, msg):
        """ 处理websocket消息
        """
        logger.debug("msg:", json.dumps(msg), caller=self)

        # 请求消息
        request_id = msg.get("id")
        if request_id:
            f = self._queries.pop(request_id)
            if f.done():
                return
            success = msg.get("result")
            error = msg.get("error")
            f.set_result((success, error))

        # 推送订阅消息
        if msg.get("method") != "subscription":
            return
        if msg["params"]["channel"] == "user.portfolio.btc":
            name = "BTC"
            total = float(msg["params"]["data"]["equity"])
            locked = float(msg["params"]["data"]["initial_margin"])
        elif msg["params"]["channel"] == "user.portfolio.eth":
            name = "ETH"
            total = float(msg["params"]["data"]["equity"])
            locked = float(msg["params"]["data"]["initial_margin"])
        else:
            return
        self._assets[name] = {
            "free": "%.8f" % (total - locked),
            "locked": "%.8f" % locked,
            "total": "%.8f" % total
        }

    async def _publish_asset(self, *args, **kwargs):
        """ 推送资产信息
        """
        if self._last_assets == self._assets:
            update = False
        else:
            update = True
        self._last_assets = self._assets
        timestamp = tools.get_cur_timestamp_ms()
        EventAsset(self._platform, self._account, self._assets, timestamp, update).publish()
        logger.info("platform:", self._platform, "account:", self._account, "asset:", self._assets, caller=self)
