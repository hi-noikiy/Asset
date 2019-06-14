# -*- coding:utf-8 -*-

"""
资产更新服务器

NOTE:
    1. 默认每隔10秒钟获取一次账户资产信息；
    2. 将最新的资产信息通过EventAsset事件推送至事件中心；

Author: HuangTao
Date:   2018/09/20
"""

import sys

from quant.quant import quant
from quant.const import OKEX, OKEX_FUTURE, BINANCE, HUOBI


def initialize():
    """ 初始化
    """
    from quant.utils import logger
    from quant.config import config

    # 初始化资产更新
    for platform, info in config.platforms.items():
        for item in info["assets"]:
            if platform == OKEX:
                from assets.okex import OKExAsset as AssetServer
            elif platform == BINANCE:
                from assets.binance import BinanceAsset as AssetServer
            elif platform == HUOBI:
                from assets.huobi import HuobiAsset as AssetServer
            elif platform == OKEX_FUTURE:
                from assets.okex_future import OKExFutureAsset as AssetServer
            else:
                logger.error("platform error! platform:", platform)
                continue
            AssetServer(**item)


def main():
    config_file = sys.argv[1]  # 配置文件 config.json
    quant.initialize(config_file)
    initialize()
    quant.start()


if __name__ == "__main__":
    main()
