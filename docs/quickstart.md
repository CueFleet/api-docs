# 接入 CueFleet 本机交易 API

## 配置客户端

1. 下载并启动 [CueFleet](https://cuefleet.com/)，登录 CueFleet 后在「币安账号」连接你的币安账号。
2. 打开「API 交易」，选择账号，配置单号或双号模式，并在服务设置中生成本机访问密钥。
3. 保持「允许 API 下单」关闭，保存配置并启动服务。复制页面显示的本机地址。调用程序与 CueFleet 服务运行在同一台设备上。

## 查询验证

直接用终端访问健康检查。若页面显示其他端口，将 `17687` 换成实际值。

```sh
curl http://127.0.0.1:17687/v1/health
```

查询授权账号时，把 CueFleet 本机访问密钥存入环境变量 `CUEFLEET_API_KEY`。如需自定义端口，另设 `CUEFLEET_API_URL`。在仓库目录运行以下任一示例。

```sh
python examples/local_api.py
node examples/local_api.mjs
```

示例只读取 `/v1/accounts`。取返回的账号 ID，并用 [账号市场参数接口](api-reference.md#get-v1accountsaccountidmarket) 核对合约周期、支付率和限额。

## 实盘接入

明确授权后才开启「允许 API 下单」。按[下单接口](api-reference.md#post-v1orders)准备订单，把唯一的 UUID 持久保存后放进 `Idempotency-Key`。金额和支付率使用十进制字符串。

读响应的 `data.state`。若请求超时、断开或结果为 `unknown`，先用原 UUID 查[原请求回执](api-reference.md#get-v1requestsrequestid)，并核对币安订单记录。收到受理回执后，可在订单查询中查看结算。
