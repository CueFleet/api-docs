# CueFleet 本机交易 API v1

默认地址：`http://127.0.0.1:17687`。仅供本机程序调用，不是币安官方 API。

本文均为格式示例，不会执行或发送请求。账号、请求编号、金额与时间均为示例值。不要直接发送示例订单。

## 接口索引

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/v1/health` | 服务状态 |
| GET | `/v1/status` | 模式、权限与并发 |
| GET | `/v1/accounts` | 授权账号 |
| GET | `/v1/accounts/{accountId}/market` | 支付率与交易限额 |
| GET | `/v1/accounts/{accountId}/orders?page=1` | 持仓与历史 |
| POST | `/v1/orders` | 创建订单 |
| GET | `/v1/requests/{requestId}` | 原请求回执 |
| GET | `/v1/openapi.json` | OpenAPI 规范 |

## 认证与使用权限

这是 CueFleet 客户端提供的本机接口。使用 http://127.0.0.1:实际端口，默认 17687。除 /v1/health 外均需 Authorization: Bearer YOUR_API_KEY。

本机 API 向所有已登录 CueFleet 的用户免费开放。旧版客户端请以其页面显示的可用权限为准。启动服务需配置本机 API 密钥及可用交易账号。

配置账号不能绑定跟单；后续变成跟单账号也会拦截新的 API 查询和下单。原有名额及交易授权继续生效。

如果客户端版本过低，创建新订单会返回 HTTP 426，错误码为 `client_upgrade_required`。先升级 CueFleet 客户端或 Linux 交易连接器。调用程序继续使用 `/v1` 和原有 API 密钥。收到此错误的订单未发往交易所，原请求仍可通过 `GET /v1/requests/{requestId}` 查询。

从客户端左侧打开「API 交易」，选择模式和账号，生成并保存密钥、保存配置、手动启动服务。服务可在最小化或其他页面运行，退出平台或关闭软件会停止。不要把密钥写入源码或公开日志。

## 幂等、超时与未知结果

每笔意图只用一个 UUID，保持全部参数及金额/支付率字符串写法一致。不同参数或不同显式账号会返回 idempotency_conflict；"5" 与 "5.0" 也不是相同字符串。

自动分配选定后，原编号固定到该账号，负载或策略变化不会换号。取消原账号授权将拒绝核对/重放，而不是换号补发。

意图先写入本机加密日志，再发送。超时、断线、202 unknown 或 order_outcome_unknown 后先查原回执和交易所订单，不无条件重试 POST，不换新 UUID。

重启后缺少最终发送结果可能显示 unknown；只保存准备意图而未发送会显示 blocked / intent_interrupted。两者均不自动重发。

## 格式、限流与响应

金额、价格、赔率、交易所编号是字符串；普通时间戳与 duration 是毫秒。不要把 null 当成 0。

仅绑定 IPv4 127.0.0.1，Host 须匹配实际端口；拒绝 Origin 和 Sec-Fetch-Site，不提供 CORS。只接受列明的方法、路径和字段。

全局每秒 20 次，下单每秒 2 次，最多 8 个并发请求；429 带 Retry-After: 1。JSON 请求体最多 16 KiB。

接口错误为 {ok:false,error:{code},traceId}；预检和交易所拒绝也可能在 ok=true 的 data.state/reason/code 中。不要只看 HTTP 或 ok。

```json
{
  "ok": false,
  "error": {
    "code": "account_not_authorized"
  },
  "traceId": "99999999-9999-4999-8999-999999999999"
}
```

## GET /v1/health

服务状态

### 参数

无请求参数。

### 请求示例

```http
GET /v1/health HTTP/1.1
Host: 127.0.0.1:17687
```

### 响应示例 · HTTP 200

```json
{
  "ok": true,
  "data": {
    "service": "EventFolo Local API",
    "version": "1",
    "running": true
  },
  "traceId": "99999999-9999-4999-8999-999999999999"
}
```

无需密钥。只表示本机正在监听，不代表平台、会员、币安会话或交易权限有效。

## GET /v1/status

模式、权限与并发

### 参数

| 字段 | 说明 |
| --- | --- |
| `Authorization` | 必填请求头，Bearer + 本机 API 密钥，不是币安官方 API Key。 |

### 请求示例

```http
GET /v1/status HTTP/1.1
Host: 127.0.0.1:17687
Authorization: Bearer YOUR_API_KEY
```

### 响应示例 · HTTP 200

```json
{
  "ok": true,
  "data": {
    "accountMode": "single",
    "loadStrategy": "balanced",
    "access": {
      "allowed": true,
      "kind": "free",
      "expiresAt": null,
      "trialEndsAt": null,
      "remainingMs": null
    },
    "accounts": [
      {
        "id": "11111111-1111-4111-8111-111111111111",
        "slot": "A",
        "uid": "123456789",
        "nickname": "Account A",
        "connected": true,
        "enabled": true,
        "canTrade": true,
        "copyRole": null,
        "availableUsdt": "100.00",
        "openOrders": 1,
        "submitting": 0,
        "capacity": 5,
        "checkedAt": 1700000000000,
        "stale": false,
        "state": "ready",
        "apiEligible": true,
        "blockedReason": null
      }
    ],
    "concurrency": {
      "open": 1,
      "submitting": 0,
      "capacity": 5,
      "known": true
    }
  },
  "traceId": "99999999-9999-4999-8999-999999999999"
}
```

accountMode：single/dual；loadStrategy：balanced/sequential。open 是在途，submitting 是提交中，capacity 是总名额；known=false 时 open 为 null，不是 0。

`access.kind` 为 `free`。此前表示截止时间和剩余时长的字段保留为 `null`。

## GET /v1/accounts

授权账号

### 参数

| 字段 | 说明 |
| --- | --- |
| `Authorization` | 必填请求头，Bearer + 本机 API 密钥，不是币安官方 API Key。 |

### 请求示例

```http
GET /v1/accounts HTTP/1.1
Host: 127.0.0.1:17687
Authorization: Bearer YOUR_API_KEY
```

### 响应示例 · HTTP 200

```json
{
  "ok": true,
  "data": [
    {
      "id": "11111111-1111-4111-8111-111111111111",
      "slot": "A",
      "uid": "123456789",
      "nickname": "Account A",
      "connected": true,
      "enabled": true,
      "canTrade": true,
      "copyRole": null,
      "availableUsdt": "100.00",
      "openOrders": 1,
      "submitting": 0,
      "capacity": 5,
      "checkedAt": 1700000000000,
      "stale": false,
      "state": "ready",
      "apiEligible": true,
      "blockedReason": null
    }
  ],
  "traceId": "99999999-9999-4999-8999-999999999999"
}
```

accountId 必须使用 id（连接 UUID），不能使用 UID、昵称或 A/B 槽位。未核实的余额/在途为 null；checkedAt 为毫秒时间戳，stale=true 时不能当作可交易数据。

apiEligible 始终为布尔值，blockedReason 为 null 或阻止原因。若配置中存在跟单账号，整个 HTTP 请求返回 api_follower_account，需先在软件中更换账号。

## GET /v1/accounts/{accountId}/market

支付率与交易限额

### 参数

| 字段 | 说明 |
| --- | --- |
| `Authorization` | 必填请求头，Bearer + 本机 API 密钥，不是币安官方 API Key。 |
| `accountId` | 必填路径参数：已授权连接 UUID；不接受查询参数。 |

### 请求示例

```http
GET /v1/accounts/11111111-1111-4111-8111-111111111111/market HTTP/1.1
Host: 127.0.0.1:17687
Authorization: Bearer YOUR_API_KEY
```

### 响应示例 · HTTP 200

```json
{
  "ok": true,
  "data": {
    "state": "ready",
    "catalog": [
      {
        "symbol": "ETHUSDT",
        "min": "5",
        "max": "125",
        "tick": "1",
        "periods": [
          {
            "period": "TEN_MINUTE",
            "long": "0.8",
            "short": "0.8"
          }
        ]
      }
    ],
    "checkedAt": 1700000000000,
    "blocked": false
  },
  "traceId": "99999999-9999-4999-8999-999999999999"
}
```

示例只展示一个标的/周期；额度和支付率以最新 catalog 为准。long/short 对应看涨/看跌净支付率。投入 5、支付率 0.8，猜对净赚 4、总返还 9 USDT。

返回周期 TEN_MINUTE/THIRTY_MINUTE/ONE_HOUR/ONE_DAY，下单转换为 10m/30m/1h/1d。blocked=true 表示存在未核清的本机提交，禁止新单。

HTTP 200 后仍须判断 data.state。blocked/unavailable 可带 reason。示例仅列业务字段，响应可附加 uid、grantId、timings 等诊断字段。

## GET /v1/accounts/{accountId}/orders?page=1

持仓与历史

### 参数

| 字段 | 说明 |
| --- | --- |
| `Authorization` | 必填请求头，Bearer + 本机 API 密钥，不是币安官方 API Key。 |
| `accountId` | 必填已授权连接 UUID。 |
| `page` | 可选 1–10000 整数，默认 1；不可重复，不接受其他查询参数。 |

### 请求示例

```http
GET /v1/accounts/11111111-1111-4111-8111-111111111111/orders?page=1 HTTP/1.1
Host: 127.0.0.1:17687
Authorization: Bearer YOUR_API_KEY
```

### 响应示例 · HTTP 200

```json
{
  "ok": true,
  "data": {
    "state": "ready",
    "checkedAt": 1700000600001,
    "serverTime": 1700000600000,
    "openTotal": 0,
    "closedTotal": 1,
    "page": 1,
    "rows": [
      {
        "id": "90071992547409931234",
        "symbol": "ETHUSDT",
        "direction": "LONG",
        "amount": "5",
        "ratio": "0.8",
        "openTime": 1700000000000,
        "expiresAt": 1700000600000,
        "duration": 600000,
        "openPrice": "2300.12",
        "closePrice": "2302.34",
        "wallet": "UM",
        "source": "closed",
        "result": "ITM",
        "pnl": "4"
      }
    ],
    "lastAttempt": null
  },
  "traceId": "99999999-9999-4999-8999-999999999999"
}
```

每次合并当前持仓（最多 50 行）与所选历史页（20 行），翻页仍会重复出现持仓。按 id 去重，source 区分 open/closed。

amount、ratio、pnl、价格及订单编号为字符串；openTime/expiresAt 为毫秒时间戳，duration 为毫秒。ITM/OTM/ATM 是赢/输/平；未结算结果和未知价格可能为 null。

lastAttempt 为最近本机提交摘要或 null。rows 可带 timing/tradeOrigin；响应可带 uid/grantId/timings。先检查 data.state，再读取订单。

## POST /v1/orders

创建订单

### 参数

| 字段 | 说明 |
| --- | --- |
| `Authorization` | 必填请求头，Bearer + 本机 API 密钥，不是币安官方 API Key。 |
| `Idempotency-Key` | 必填 UUID 请求头，一笔意图一个编号，核对时沿用原编号。 |
| `Content-Type` | application/json |
| `accountId` | 可选 UUID；省略为自动分配，填写后仅使用该账号且不换号。 |
| `symbol` | 必填：BTCUSDT / ETHUSDT。 |
| `direction` | 必填：LONG 看涨 / SHORT 看跌。 |
| `amount` | 必填正十进制字符串，满足市场 min/max/tick 及本机单笔上限。 |
| `period` | 必填：10m / 30m / 1h / 1d。 |
| `wallet` | 仅 UM，可省略，默认 UM。 |
| `payoutRatio` | 必填当前市场的标的、周期及方向支付率，十进制字符串。 |

### 请求示例 · 自动分配

```http
POST /v1/orders HTTP/1.1
Host: 127.0.0.1:17687
Authorization: Bearer YOUR_API_KEY
Idempotency-Key: 33333333-3333-4333-8333-333333333333
Content-Type: application/json

{
  "symbol": "ETHUSDT",
  "direction": "LONG",
  "amount": "5",
  "period": "10m",
  "wallet": "UM",
  "payoutRatio": "0.8"
}
```

### 请求示例 · 指定账号

```http
POST /v1/orders HTTP/1.1
Host: 127.0.0.1:17687
Authorization: Bearer YOUR_API_KEY
Idempotency-Key: 33333333-3333-4333-8333-333333333333
Content-Type: application/json

{
  "accountId": "11111111-1111-4111-8111-111111111111",
  "symbol": "ETHUSDT",
  "direction": "LONG",
  "amount": "5",
  "period": "10m",
  "wallet": "UM",
  "payoutRatio": "0.8"
}
```

### 响应示例 · HTTP 201

```json
{
  "ok": true,
  "data": {
    "id": "33333333-3333-4333-8333-333333333333",
    "connection": "11111111-1111-4111-8111-111111111111",
    "state": "accepted",
    "attempted": true,
    "orderId": "90071992547409931234",
    "reason": null,
    "code": "000000",
    "timing": {
      "version": 1,
      "mode": "api",
      "receivedAt": 1700000000000,
      "submitReceivedAt": 1700000000010,
      "responseAt": 1700000000250,
      "acceptedAt": 1700000000250,
      "stages": {
        "connectorMs": 240
      },
      "confirmationWaitMs": null,
      "clickToAcceptedMs": null,
      "effectiveMs": null,
      "submitToAcceptedMs": 240,
      "backendMs": 240,
      "clickToPositionMs": null,
      "clickToEntryPriceMs": null
    },
    "replayed": false
  },
  "traceId": "99999999-9999-4999-8999-999999999999"
}
```

### 响应示例 · HTTP 202

```json
{
  "ok": true,
  "data": {
    "id": "33333333-3333-4333-8333-333333333333",
    "connection": "11111111-1111-4111-8111-111111111111",
    "state": "unknown",
    "attempted": null,
    "orderId": null,
    "reason": "transport_interrupted",
    "code": null,
    "timing": {
      "version": 1,
      "mode": "api",
      "receivedAt": 1700000000000,
      "submitReceivedAt": 1700000000010,
      "responseAt": 1700000000250,
      "stages": {
        "connectorMs": 240
      },
      "confirmationWaitMs": null,
      "clickToAcceptedMs": null,
      "effectiveMs": null,
      "submitToAcceptedMs": null,
      "backendMs": 240,
      "clickToPositionMs": null,
      "clickToEntryPriceMs": null
    },
    "replayed": false
  },
  "traceId": "99999999-9999-4999-8999-999999999999"
}
```

两段请求为替代示例，不是连续步骤；本页不会执行。开启 API 下单后使用真实资金，不会再弹逐笔确认。

均衡先选在途较少账号，再比较余额和交替顺序；串行优先第一账号，满 5 笔或余额不足再用第二账号。每号最多 5 笔，双号合计 10 笔。结果未知、拒绝或预检失败均不自动换号补单。

201 首次受理；200 原回执重放；202 未知；422 明确拒绝；409 受阻。ok=true 只表示有业务结果，必须读取 data.state；accepted 不等于结算。

id 为请求 UUID，connection 为实际账号，orderId 可为 null，attempted 可为 true/false/null。timing 是诊断对象，部分耗时字段可能为空。

## GET /v1/requests/{requestId}

原请求回执

### 参数

| 字段 | 说明 |
| --- | --- |
| `Authorization` | 必填请求头，Bearer + 本机 API 密钥，不是币安官方 API Key。 |
| `requestId` | 必填原 Idempotency-Key UUID，不是交易所 orderId。 |

### 请求示例

```http
GET /v1/requests/33333333-3333-4333-8333-333333333333 HTTP/1.1
Host: 127.0.0.1:17687
Authorization: Bearer YOUR_API_KEY
```

### 响应示例 · HTTP 200

```json
{
  "ok": true,
  "data": {
    "id": "33333333-3333-4333-8333-333333333333",
    "connection": "11111111-1111-4111-8111-111111111111",
    "state": "accepted",
    "attempted": true,
    "orderId": "90071992547409931234",
    "reason": null,
    "code": "000000",
    "timing": {
      "version": 1,
      "mode": "api",
      "receivedAt": 1700000000000,
      "submitReceivedAt": 1700000000010,
      "responseAt": 1700000000250,
      "acceptedAt": 1700000000250,
      "stages": {
        "connectorMs": 240
      },
      "confirmationWaitMs": null,
      "clickToAcceptedMs": null,
      "effectiveMs": null,
      "submitToAcceptedMs": 240,
      "backendMs": 240,
      "clickToPositionMs": null,
      "clickToEntryPriceMs": null
    },
    "selection": {
      "symbol": "ETHUSDT",
      "period": "TEN_MINUTE",
      "amount": "5",
      "direction": "LONG",
      "wallet": "UM"
    },
    "createdAt": 1700000000000,
    "attemptedAt": 1700000000010
  },
  "traceId": "99999999-9999-4999-8999-999999999999"
}
```

### 响应示例 · HTTP 200

```json
{
  "ok": true,
  "data": {
    "id": "33333333-3333-4333-8333-333333333333",
    "connection": "11111111-1111-4111-8111-111111111111",
    "state": "processing",
    "attempted": false,
    "selection": {
      "symbol": "ETHUSDT",
      "period": "TEN_MINUTE",
      "amount": "5",
      "direction": "LONG",
      "wallet": "UM"
    },
    "createdAt": 1700000000000
  },
  "traceId": "99999999-9999-4999-8999-999999999999"
}
```

正在执行可返回 processing，发送前 attempted=false，发送中可能为 null；它不是拒绝或取消。继续核对原编号。

原请求回执需使用有效的本机密钥、CueFleet 登录会话和原账号授权范围。日志不自动重发。

404 request_not_found 不证明交易所没有成交。unknown 或发送中断时，先结合交易所订单核对，不能换新编号补单。

## GET /v1/openapi.json

OpenAPI 规范

### 参数

| 字段 | 说明 |
| --- | --- |
| `Authorization` | 必填请求头，Bearer + 本机 API 密钥，不是币安官方 API Key。 |

### 请求示例

```http
GET /v1/openapi.json HTTP/1.1
Host: 127.0.0.1:17687
Authorization: Bearer YOUR_API_KEY
```

### 响应示例 · HTTP 200 · 节选

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "CueFleet Local Trading API",
    "version": "1.1.0"
  },
  "servers": [
    {
      "url": "http://127.0.0.1:17687"
    }
  ]
}
```

直接返回 OpenAPI JSON，不包装 ok/data/traceId；示例为根字段节选。可导入兼容工具，实际端口以软件为准。

## 错误码

| HTTP | code | 说明 |
| --- | --- | --- |
| 401 | `invalid_api_key` | 密钥缺失、错误或已重置。 |
| 401 | `session_unavailable / login_required / session_expired` | 平台登录无效，重新登录；订单先核对原回执。 |
| 403 | `api_follower_account / copy_manual_locked` | 账号绑定跟单，不能自主交易。 |
| 403 | `account_not_authorized` | 账号不在密钥授权范围。 |
| 403 | `api_read_only / trading_not_enabled / account_limit_locked` | API 下单未开、交易授权缺失或名额暂停。 |
| 403 | `api_amount_limit` | 超过本机单笔上限。 |
| 400 | `invalid_order / invalid_request / invalid_selection` | 字段、金额字符串、周期等无效；多余字段也拒绝。 |
| 400 | `invalid_query / invalid_path / invalid_request_id` | 路径、查询参数或 UUID 无效。 |
| 400 | `idempotency_key_required` | 缺少合法请求 UUID。 |
| 409 | `idempotency_conflict` | 原编号已用于不同参数。 |
| 409 | `order_in_progress` | 请求或账号正提交，查原编号。 |
| 409 | `order_outcome_unknown` | 先核清原请求和交易所订单。 |
| 409 | `api_no_account_capacity` | 无足够余额或在途名额。 |
| 503 | `api_account_data_unavailable` | 余额或在途未能核实。 |
| 409 | `connection_login_required` | 币安连接缺失或需登录。 |
| 404 | `request_not_found / route_not_found` | 无本机记录或路径；不证明没有成交。 |
| 415 / 413 / 400 | `json_required / request_too_large / invalid_json` | 不是 JSON、超过 16 KiB 或格式错误。 |
| 429 | `rate_limited / too_many_requests` | 读取 Retry-After，勿自动重发交易。 |
| 403 | `local_clients_only / api_access_revoked` | 本机条件不符或处理中授权/配置/登录变化。 |
| 503 | `service_unavailable` | 本机/上游异常，订单仍查原意图。 |

## 客户端与规范

- [Python 客户端](../examples/local_api.py)：标准库客户端。
- [JavaScript 客户端](../examples/local_api.mjs)：Node.js 客户端。
- [OpenAPI 3.1](../openapi.json)：完整机器可读规范。

这些示例须由技术人员配置密钥并检查权限。本文不会启动服务、生成密钥、调用查询或发送订单。
