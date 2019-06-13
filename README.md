
## 资产服务

资产服务器主要实现了资产数据的获取和资产事件的发布功能。
资产服务器将根据各大交易所提供的REST API等方式，大约每隔10秒钟，从交易所获取一次资产详情，然后将资产数据经过打包处理，通过资产事件的方式发布至事件中心。


#### 1. 准备工作

- 使用 `pip` 安装 `thenextquant`:
```text
pip install thenextquant
```

- 下载项目 & 修改配置文件
```text
git clone https://github.com/TheNextQuant/Market.git  # 下载项目
cd Market  # 进入项目目录
vim config.json  # 编辑配置文件
```
> 可以参考[配置示例](config.json)，配置文件详解请参考 [配置文件说明](https://github.com/TheNextQuant/thenextquant/blob/master/docs/configure/README.md)。

#### 2. 运行

```text
python src/main.py config.json  # 启动之前请修改配置文件
```

#### 3. 各大交易所资产服务配置

将需要获取资产的账户，写入配置文件的 `PLATFORMS` 项目下，其中 `key` 为交易平台名称小写字母，可以通过 `from quant import const` 下各个交易所名称来确定。
注意，`assets` 为数组，可以同事配置多个账户。

- OKEx

OKEx的配置需要注意 `passphrase` 参数不要遗漏。
```json
{
    "PLATFORMS": {
        "okex": {
            "assets": [
                {
                    "account": "test@gmail.com",
                    "access_key": "abc123",
                    "secret_key": "ABC123",
                    "passphrase": "test123456"
                }
            ]
        }
    }
}
```
