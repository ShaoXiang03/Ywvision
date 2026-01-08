# Polymarket Markets Dashboard

本项目从 Polymarket Gamma API 拉取市场数据，过滤出符合条件的二元 YES/NO 候选市场，并通过 Streamlit 构建交互式网页展示：
- 所有候选市场列表（支持交互式过滤）
- 聚焦展示 2 个市场（1 个 Crypto + 1 个 Sports）
- 额外专用页面分别展示 Crypto 和 Sports 市场

项目完全符合 Onboarding Task v1 要求，并实现多项加分项（CLOB 价格、多页面、快速加载等）。

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
- 拉取所有市场列表及详细字段
- 支持分页：`limit` 与 `offset`

**关键字段**:
- `question`：市场问题
- `endDate`：结束时间（ISO 8601）
- `category`：市场分类
- `outcomes` / `outcomePrices` / `clobTokenIds`：可能为 JSON 字符串或数组
- `enableOrderBook`、`active`、`closed`

**健壮性处理**:
- 自动检测字段类型，若为字符串则 `json.loads()` 解析
- 只保留二元 YES/NO 市场（outcomes 长度为 2，且能识别 Yes/No）

### 2. CLOB API（已实现加分项）
**端点**: `POST https://clob.polymarket.com/prices`  
**用途**:
- 批量获取候选市场 YES/NO token 的最佳卖价（best ask）
- 价格更贴近真实盘口
- 若 CLOB 无数据，自动回退至 Gamma `outcomePrices`

## 分类与选取策略

### Crypto / Sports 判定规则（已写入 README）
采用两级判定，确保即使 API `category` 缺失也能正确识别：

1. **一级判定**：`category` 字段包含关键词（不区分大小写）
   - Crypto：包含 `"crypto"`
   - Sports：包含 `"sports"`

2. **二级判定**（fallback）：问题描述中包含关键词
   - **Crypto 关键词**：`bitcoin`, `btc`, `ethereum`, `eth`, `solana`, `sol`, `xrp`, `crypto`, `binance`, `coinbase`, `hyperliquid`, `okx`, `megaeth`
   - **Sports 关键词**：`nfl`, `nba`, `afc`, `nfc`, `super bowl`, `championship`, `eagles`, `packers`, `rams`, `bears`, `chiefs`, `seahawks`, `football`, `basketball`, `soccer`, `world cup`

### Focus=2 选取策略
- 从所有满足 **48 小时内关闭** 的候选市场中：
  - 选取 **第一个** 判定为 Crypto 的市场
  - 选取 **第一个** 判定为 Sports 的市场
- 若 48 小时内无符合市场，自动回退至 **168 小时（7 天）** 内选取，确保卡片永不为空
- 选取顺序遵循 Gamma API 返回顺序

## 过滤规则说明

### 候选市场过滤条件（全部必须满足）
1. `enableOrderBook == True`
2. `active == True` 且 `closed == False`
3. `0 < hours_to_close <= 48`（主页面候选表可通过滑块调整，专用页面固定 48h）
4. 有效的 YES/NO token IDs（`clobTokenIds` 可解析为长度 2，且能识别 Yes/No）

### 价格有效性过滤
- 一键按钮“Filter Valid Prices”
- 点击后仅显示 `yes_price` 和 `no_price` 均非 None 的市场
- 再次点击恢复显示全部候选市场

### 二元市场验证
- `len(outcomes) == 2`
- 必须能识别出 YES 与 NO（不区分大小写）
- 不符合的设 `invalid_reason` 并被排除

## 数据字段说明（MarketRecord）

| 字段               | 类型            | 说明                              |
|--------------------|-----------------|-----------------------------------|
| `id`               | str             | 市场唯一标识                      |
| `slug`             | str \| None     | URL slug                          |
| `question`         | str \| None     | 市场问题                          |
| `category`         | str \| None     | 分类（若缺失显示推断值）          |
| `endDate`          | str \| None     | 结束时间（ISO）                   |
| `hours_to_close`   | float \| None   | 距离关闭小时数（保留 2 位）       |
| `enableOrderBook`  | bool            | 是否启用订单簿                    |
| `active`           | bool            | 是否活跃                          |
| `closed`           | bool            | 是否已关闭                        |
| `yes_token_id`     | str \| None     | YES token ID                      |
| `no_token_id`     | str \| None     | NO token ID                       |
| `yes_price`        | float \| None   | YES 价格（CLOB best ask）         |
| `no_price`         | float \| None   | NO 价格（CLOB best ask）          |
| `invalid_reason`   | str \| None     | 无效原因                          |

## 项目结构

```
polymarket-task/
├── README.md                   # 本文件
├── requirements.txt
├── app.py                      # 主仪表盘（Focus=2 + 候选表）
├── pages/
│   ├── 1_Crypto_Markets.py     # Crypto 专用页面（≤48h，快速加载前 50 + Load All）
│   └── 2_Sports_Markets.py     # Sports 专用页面（同上）
└── src/
    ├── clients/
    │   ├── gamma.py            # Gamma API 客户端 + 全分页
    │   └── clob.py             # CLOB /prices 客户端
    └── core/
        ├── models.py           # MarketRecord
        ├── parse.py            # 解析与标准化
        ├── filters.py          # 过滤 + 分类判定
        └── select_focus.py     # Focus=2 选取
```

## 功能特性

- **主页面**
  - Focus=2 卡片展示（带 fallback）
  - 候选市场表格（Category、Question、End Date、Hours、YES/NO Price、Slug）
  - 价格过滤按钮、刷新按钮、调试模式
  - 空状态友好提示

- **Crypto / Sports 专用页面**
  - 固定 48 小时过滤
  - 默认快速加载前 50 条（~5-8 秒）
  - “Load All” 按钮可加载全部符合市场

- **性能优化**
  - 主页面使用 `@st.cache_data`
  - 专用页面默认只取足够数据获取前 50 条
  - CLOB 价格仅对显示的市场批量请求

## 技术栈

- Python 3.10+
- Streamlit ≥1.29
- requests
- pydantic ≥2.5
- pandas

## 故障排除

- **端口占用**：`streamlit run app.py --server.port 8502`
- **API 失败**：检查网络，Gamma API 可能有速率限制
- **无市场显示**：48 小时内确实可能无符合条件的二元市场（预测市场常见现象），可调整滑块或等待新事件

## 扩展建议

1. 接入 CLOB WebSocket 实现实时价格更新
2. 添加价格历史图表（Plotly）
3. 缓存历史数据用于趋势分析
4. 增加更多分类页面（Politics、Economics 等）

## License

MIT License

## 作者

