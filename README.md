# 自动化多市场交易信号扫描器 (Automated Multi-Market Trading Signal Scanner)

这是一个功能强大的自动化交易信号扫描系统。它使用Python复现了特定于TradingView Pine Script的交易策略，能够批量扫描美股、港股、A股以及加密货币市场，并在发现符合策略的买入信号时，通过Telegram机器人自动发送实时通知。

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 核心功能

-   **跨市场扫描**: 同时覆盖美股 (S&P 500)、港股、A股 (沪深300) 以及加密货币 (Binance) 市场。
-   **Pine Script 策略复现**: 核心逻辑基于一个多时间框架 (MTF) 的EMA趋势过滤和布林带/EMA金叉进场策略。
-   **多时间框架 (MTF) 分析**: 使用更高时间周期的指标来过滤趋势，提高信号的准确性。
-   **实时Telegram通知**: 当扫描到任何市场的买入信号时，会立即发送一条格式化好的汇总消息到您的Telegram。
-   **高度可配置**: 策略参数、股票/加密货币列表均可通过配置文件轻松修改，无需改动代码。
-   **模块化与可扩展**: 项目采用模块化设计，方便添加新的数据源、策略逻辑或通知渠道。

## 系统工作流程

本系统是一个自动化的流水线，其工作流程如下：

1.  **定时触发 (`Scheduler`)**: `scheduler.py` 每天在预设的时间（例如，收盘后）自动启动扫描任务。
2.  **读取配置 (`Config`)**: 从 `config.ini` 文件加载策略参数和要扫描的资产列表路径。
3.  **市场扫描 (`Market Scanner`)**: `scanner.py` 遍历资产列表中的每一个交易对。
4.  **数据获取 (`Data Fetcher`)**: `data_fetcher.py` 根据资产类型，从相应的数据源 (`yfinance` for Stocks, `Binance API` for Crypto) 获取日线和趋势周期（如1小时）的数据。
5.  **信号计算 (`Signal Calculator`)**: 在获取的数据上，使用 `pandas-ta` 库计算指标，并应用策略逻辑判断是否触发买入信号。
6.  **结果汇总**: 将所有触发信号的资产汇总成一个列表。
7.  **发送通知 (`Notifier`)**: `telegram_bot.py` 将汇总后的信号列表格式化成一条美观的消息，发送到您的Telegram。

## 项目结构

```
trading_signal_scanner/
├── .env                  # 存放所有API密钥和Token (需手动创建)
├── config.ini            # 策略参数、股票列表路径等
├── requirements.txt      # 项目依赖库
├── main.py               # 手动触发一次扫描的主入口
├── scanner.py            # 核心：市场扫描器 & 信号计算器
├── data_fetcher.py       # 数据获取器 (yfinance, Binance, Tushare)
├── telegram_bot.py       # Telegram通知发送器
└── stock_lists/          # 存放股票/加密货币代码列表的文件夹
    ├── us_stocks.txt
    ├── hk_stocks.txt
    ├── cn_stocks.txt
    └── crypto_symbols.txt
```

## 安装与配置指南

### 1. 克隆项目

```bash
git clone https://github.com/your-username/your-repository-name.git
cd your-repository-name
```

### 2. 安装依赖

建议在Python虚拟环境中进行安装。
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 3. 创建并配置 `.env` 文件

在项目根目录手动创建一个名为 `.env` 的文件，并填入您的API密钥。

```dotenv
# .env

# Tushare API (用于A股数据, 如果不用可留空)
TUSHARE_TOKEN="your_tushare_token_here"

# Telegram Bot
TELEGRAM_TOKEN="your_telegram_bot_token_here"
TELEGRAM_CHAT_ID="your_personal_or_group_chat_id_here"
```

### 4. 修改 `config.ini` 文件

根据您的需求调整策略参数和资产列表路径。默认配置已设置好。

### 5. 填充资产列表

进入 `stock_lists/` 文件夹，将您想要监控的股票代码或加密货币交易对填入对应的 `.txt` 文件中，每行一个。
-   **美股/港股**: 使用 `yfinance` 格式 (e.g., `AAPL`, `0700.HK`).
-   **A股**: 使用 `Tushare` 格式 (e.g., `600519.SH`).
-   **加密货币**: 使用 `Binance` 格式 (e.g., `BTCUSDT`).

## 如何使用

### 手动运行一次扫描 (用于测试)

执行 `main.py` 会立即触发一次完整的市场扫描，并将结果发送到Telegram。这对于测试配置和策略逻辑非常有用。

```bash
python main.py
```

### 启动自动化调度器 (用于生产)

执行 `scheduler.py` 会启动一个持续运行的进程。它会根据您在代码中设定的时间（默认为每日`17:00`）自动执行扫描任务。

```bash
python scheduler.py
```
您会看到脚本启动的提示信息，之后它会安静地在后台等待。**您需要保持这个终端窗口开启**。

> **生产部署建议**: 在云服务器上，建议使用 `screen` 或 `nohup` 命令来让 `scheduler.py` 脚本在后台持久运行。

## 策略逻辑简介

本系统实现的Pine Script策略是一个基于多时间框架的趋势跟踪策略：

1.  **趋势过滤**: 在一个更高的时间周期上（例如1小时图），判断快线EMA是否在慢线EMA之上。只有当趋势为多头时，才会在主周期上寻找买入机会。
2.  **进场信号 (日线图)**: 满足以下任一条件即可触发买入信号：
    *   **条件A (突破)**: 价格上穿布林带中轨 (`BBM` a.k.a SMA)。
    *   **条件B (确认)**: 价格已在中轨之上，并且主周期的快线EMA向上穿越慢线EMA（金叉）。

## 未来的改进方向

- [ ]  **集成回测框架**: 使用 `backtrader` 或 `Zipline` 对策略进行严格的历史数据回测。
- [ ]  **增加更多数据源**: 集成如 Alpha Vantage, Polygon.io 等其他数据API。
- [ ]  **增加更多策略**: 允许用户在配置文件中选择不同的策略进行扫描。
- [ ]  **Web仪表盘**: 创建一个简单的Flask或Streamlit Web界面来展示信号历史和系统状态。
- [ ]  **容器化**: 使用 Docker 进行封装，简化部署流程。

## 许可证

本项目采用 [MIT 许可证](https://opensource.org/licenses/MIT)。
