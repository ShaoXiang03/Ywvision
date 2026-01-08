# Polymarket API 市场拉取 + 双市场看板

## 项目概述

本项目从 Polymarket Gamma API 拉取市场数据，过滤出符合条件的候选市场，并通过 Streamlit 网页展示：
- 所有候选市场列表（支持交互式过滤）
- 聚焦展示 2 个市场（1 个 Crypto + 1 个 Sports）

## 快速开始

### 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 运行应用

```bash
streamlit run app.py
```

应用将在浏览器中自动打开，默认地址：`http://localhost:8501`

## 使用的 API

### 1. Gamma Markets API（主要数据源）

**端点**: `GET https://gamma-api.polymarket.com/markets`

**用途**:
- 拉取市场列表及详细字段
- 支持分页参数：`limit` 和 `offset`

**获取字段**:
- `question`: 市场问题
- `endDate`: 结束时间（ISO 格式）
- `category`: 市场分类
- `outcomes`: 结果选项（Yes/No）
- `outcomePrices`: 当前价格
- `clobTokenIds`: CLOB token IDs
- `enableOrderBook`: 是否启用订单簿
- `active`: 是否活跃
- `closed`: 是否已关闭

**健壮性处理**:
- `outcomes`、`outcomePrices`、`clobTokenIds` 可能是 JSON 字符串或数组
- 代码自动检测类型并使用 `json.loads()` 解析字符串格式

### 2. CLOB API（可选增强）

本项目基础版本使用 Gamma API 的 `outcomePrices`。

**可扩展**:
- `GET /book?token_id=...`: 获取订单簿详情
- `POST /prices`: 批量获取最佳买卖价

## 分类与选取策略

### Crypto / Sports 判定规则

**判定方法**: 基于 `category` 字段（不区分大小写）

- **Crypto 市场**: `category` 包含 `"crypto"` 关键词
- **Sports 市场**: `category` 包含 `"sports"` 关键词

**示例**:
```python
is_crypto = 'crypto' in market['category'].lower()
is_sports = 'sports' in market['category'].lower()
```

### Focus=2 选取策略

从候选市场中选出 2 个市场：

1. **选择第一个符合条件的 Crypto 市场**
   - 满足所有候选过滤条件
   - `category` 包含 "crypto"
   - 48 小时内关闭

2. **选择第一个符合条件的 Sports 市场**
   - 满足所有候选过滤条件
   - `category` 包含 "sports"
   - 48 小时内关闭

**优先级**: 按 API 返回顺序，选择第一个匹配的市场

**边界情况**:
- 如果没有找到符合条件的 Crypto 或 Sports 市场，该位置显示"未找到"
- UI 会明确标注哪个类别没有可用市场

## 过滤规则说明

### 候选市场过滤条件（全部必须满足）

代码中的 `filter_candidates()` 函数应用以下规则：

#### 1. Order Book 启用
```python
market.enableOrderBook == True
```

#### 2. 市场状态活跃
```python
market.active == True and market.closed == False
```

#### 3. 48 小时内关闭
```python
0 < hours_to_close <= 48
```
- `hours_to_close` 计算方式：`(endDate - now) / 3600秒`
- 必须是未来时间（> 0）
- 必须在 48 小时内

#### 4. 有效的 YES/NO Token IDs
```python
market.yes_token_id is not None and market.no_token_id is not None
```
- `clobTokenIds` 必须可解析为长度为 2 的列表
- 必须能够识别 YES/NO outcomes
- YES/NO 的判定：outcomes 中包含 "yes" 或 "no"（不区分大小写）

### Missing Price 定义

**价格无效**的情况：
- `yes_price` 或 `no_price` 为 `None`
- `yes_price` 或 `no_price` 为 `NaN`
- 无法从 `outcomePrices` 解析出数值

**过滤按钮行为**:
- **点击"过滤无效价格"**: 仅显示 `yes_price` 和 `no_price` 都有效（非 None 且为数字）的市场
- **再次点击或点击"重置"**: 恢复显示所有候选市场

### 二元市场验证

只处理 YES/NO 二元市场：

```python
if len(outcomes) != 2:
    invalid_reason = "Not a binary market (outcomes != 2)"
    
if 'yes' not in outcomes[i].lower() and 'no' not in outcomes[i].lower():
    invalid_reason = "Cannot identify YES/NO outcomes"
```

## 数据字段说明

### MarketRecord 结构

每个市场标准化为以下字段：

| 字段 | 类型 | 说明 |
|-----|------|------|
| `id` | str | 市场唯一标识 |
| `slug` | str \| None | 市场 URL slug |
| `question` | str | 市场问题 |
| `category` | str | 市场分类 |
| `endDate` | str | 结束时间（ISO 8601） |
| `hours_to_close` | float | 距离关闭的小时数（保留 2 位小数） |
| `enableOrderBook` | bool | 是否启用订单簿 |
| `active` | bool | 是否活跃 |
| `closed` | bool | 是否已关闭 |
| `yes_token_id` | str \| None | YES token ID |
| `no_token_id` | str \| None | NO token ID |
| `yes_price` | float \| None | YES 当前价格 |
| `no_price` | float \| None | NO 当前价格 |
| `invalid_reason` | str \| None | 无效原因（若适用） |

## 项目结构

```
polymarket-task/
├── README.md                 # 本文件
├── requirements.txt          # Python 依赖
├── app.py                   # Streamlit 应用入口
└── src/
    ├── __init__.py
    ├── clients/
    │   ├── __init__.py
    │   └── gamma.py         # Gamma API 客户端
    ├── core/
    │   ├── __init__.py
    │   ├── models.py        # 数据模型
    │   ├── parse.py         # 数据解析
    │   ├── filters.py       # 过滤逻辑
    │   └── select_focus.py  # Focus 市场选择
    └── utils/
        ├── __init__.py
        └── datetime_utils.py # 时间处理工具
```

## 功能特性

### 1. 候选市场表格
- 显示所有符合条件的候选市场
- 列：Category / Question / End Date / Hours to Close / YES Price / NO Price
- 支持水平滚动

### 2. 交互式过滤
- **"过滤无效价格"按钮**: 只显示价格完整的市场
- **"显示全部"按钮**: 恢复显示所有候选
- **"刷新数据"按钮**: 重新从 API 拉取最新数据

### 3. Focus=2 展示区
- 独立卡片展示 Crypto 和 Sports 市场
- 显示详细信息：问题、倒计时、价格、分类
- 如果找不到符合条件的市场，显示提示信息

## 技术栈

- **Python**: 3.10+
- **Streamlit**: 1.29+ (Web UI 框架)
- **requests**: HTTP 客户端
- **pydantic**: 数据验证和序列化

## 故障排除

### 端口已被占用

```bash
streamlit run app.py --server.port 8502
```

### API 请求失败

- 检查网络连接
- Gamma API 可能有速率限制，稍后重试

### 没有找到 Crypto/Sports 市场

- 48 小时窗口内可能确实没有符合条件的市场
- 尝试调整过滤条件或扩大时间窗口

## 扩展建议

1. **集成 CLOB API**: 获取更准确的盘口价格
2. **添加图表**: 使用 Plotly 展示价格趋势
3. **WebSocket 实时更新**: 监听市场价格变化
4. **数据库存储**: 保存历史数据用于分析
5. **单元测试**: 完善 `tests/` 目录

## License

MIT License

## 作者

Onboarding Task v1 - Polymarket Integration
