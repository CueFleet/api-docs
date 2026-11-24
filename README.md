<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/cuefleet-logo-dark.svg">
    <img src="assets/cuefleet-logo-light.svg" alt="CueFleet" width="146">
  </picture>
</p>

<h1 align="center">CueFleet 本机交易 API</h1>

<p align="center">在运行 CueFleet 的设备上查询授权账号、接入币安事件合约实盘、核对原请求回执。</p>

<p align="center">
  <a href="docs/quickstart.md"><strong>快速上手</strong></a> ·
  <a href="docs/api-reference.md">接口参考</a> ·
  <a href="openapi.json">OpenAPI 3.1</a> ·
  <a href="https://cuefleet.com/">CueFleet 官网</a>
</p>

## 接入流程

1. **配置客户端**。在「API 交易」选定已连接的币安账号，生成 CueFleet 访问密钥并启动本机服务。
2. **先验证查询**。让你的程序从同一台设备访问客户端显示的地址，默认是 `http://127.0.0.1:17687`。检查服务、账号授权和交易参数。
3. **实盘与回执**。从客户端明确开启「允许 API 下单」。每笔交易意图保存一个请求 UUID。遇到超时或结果未知，查原请求回执和币安订单。

## 接口一览

| 任务 | 接口 |
| --- | --- |
| 查看服务 | `GET /v1/health` · `GET /v1/status` |
| 查看授权账号 | `GET /v1/accounts` |
| 查支付率和限额 | `GET /v1/accounts/{accountId}/market` |
| 查在途和已结算订单 | `GET /v1/accounts/{accountId}/orders?page=1` |
| 提交订单 | `POST /v1/orders` |
| 查询原回执 | `GET /v1/requests/{requestId}` |
| 读取规范 | `GET /v1/openapi.json` |

[Python 查询示例](examples/local_api.py) · [Node.js 查询示例](examples/local_api.mjs)

本仓库跟踪新版客户端。地址、访问权限及接口行为以已安装版本的「接口文档」及 `/v1/openapi.json` 为准。

[联系 CueFleet · Telegram](https://t.me/lazyer_trading)
