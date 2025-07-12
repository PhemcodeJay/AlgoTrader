Here is a **combined and production-ready README** file for your **AlgoTrader** project, merging all the technical details, modules, and architecture in a clear and maintainable format:

---

# 🚀 AlgoTrader: Streamlit-Based Crypto Trading Dashboard

**AlgoTrader** is a full-stack algorithmic crypto trading platform built with **Streamlit**, integrating real-time market data, trading automation, signal generation, portfolio analytics, and social media export. It supports both **Virtual** and **Real (Bybit)** trading modes with robust risk management and modular architecture.

---

## 📐 Architecture Overview

### 🖥️ Frontend

* **Framework**: Streamlit
* **Charts**: Plotly
* **UI Components**: Modular components for dashboard views
* **Layout**: Sidebar navigation with pages: Dashboard, Signals, Portfolio, Charts, Automation, Database, Settings

### ⚙️ Backend

* **Trading Engine**: Core logic for trade simulation & live execution (Bybit)
* **Data Provider**: Binance Futures API for real-time OHLCV & symbol info
* **Automation Engine**: Background trading automation with threading
* **Database**: PostgreSQL + SQLAlchemy ORM
* **Virtual/Real Mode Toggle**: Seamless switching for simulation and live trading
* **Social Sharing**: Discord Webhook & Reddit integration

---

## 🔑 Key Features

| Feature                    | Description                                        |
| -------------------------- | -------------------------------------------------- |
| 📈 Signal Generation       | Technical analysis + confidence scoring            |
| 🤖 Auto Trading            | Optional automation every 5–15 minutes             |
| 💼 Virtual & Real Mode     | Toggle between simulation & live trading via Bybit |
| 💬 Social Media Export     | Signal sharing to Discord and Reddit               |
| 📊 Portfolio Analytics     | P\&L tracking, win rate, drawdowns                 |
| 🔒 Risk Management         | Capital protection, drawdown, max trade/day        |
| 📄 PDF Reports             | Auto-generated trade summaries                     |
| 🧠 Configurable Strategies | EMA, RSI, MACD, Bollinger, trend filters           |

---

## 🧱 File Structure

```
/
├── app.py                    # Main dashboard entry point
├── trading_engine.py         # Signal logic, trade execution, capital logic
├── dashboard_components.py   # UI: charts, tables, metric cards
├── data_provider.py          # Binance Futures data fetcher
├── utils.py                  # Formatters & helpers
├── database.py               # PostgreSQL ORM & models
├── automated_trader.py       # Automation thread & signal executor
├── start_automation.py       # CLI entry for automation engine
├── automated_trader.log      # Automation runtime logs
├── signals/                  # Archived signal data
├── trades/                   # Archived trade logs
```

---

## ⚙️ Trading Configuration

| Setting             | Value          |
| ------------------- | -------------- |
| Starting Capital    | `$10.00`       |
| Risk Per Trade      | `2%`           |
| Leverage            | `20x`          |
| Max Daily Trades    | `50`           |
| Stop Loss           | `10%`          |
| Take Profit         | `25%`          |
| Max Drawdown        | `20%`          |
| Automation Interval | `5–15 minutes` |

---

## 🔌 External Integrations

### ✅ APIs

* **Binance Futures** – OHLCV & symbol data
* **Bybit** – Live trade execution (Real Mode)
* **Discord Webhooks** – Signal posting
* **Reddit (Snoowrap)** – Signal sharing

### 🔐 Environment Variables

Set these in `.env` or Streamlit secrets:

```env
BYBIT_API_KEY=
BYBIT_API_SECRET=
DISCORD_WEBHOOK_URL=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USERNAME=
REDDIT_PASSWORD=
```

---

## 🛠️ Setup & Run

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```
Install POSTGRESQL and run python database.py

### 2. Start Streamlit Dashboard

```bash
streamlit run app.py
```

### 3. Start Automation (optional)

```bash
python start_automation.py
```

---

## 🧪 Toggle Trading Modes

Inside the dashboard, use the **"⚙️ Select Trade Mode"** radio button to switch between:

* 🧪 **Virtual**: Simulates trades, logs to DB, no API calls
* 🔴 **Real**: Sends real market orders to Bybit via API

The backend automatically adjusts trade routing based on this setting.

---

## 📊 Dashboard Tabs

| Tab            | Description                                        |
| -------------- | -------------------------------------------------- |
| **Dashboard**  | Overview, trade mode, ticker, signal metrics       |
| **Signals**    | Ranked trade ideas with confidence & strategy info |
| **Portfolio**  | Trade history, stats, P\&L, drawdown               |
| **Charts**     | Technical analysis per symbol                      |
| **Automation** | Start/Stop background trading                      |
| **Database**   | Sync/migrate legacy files to PostgreSQL            |
| **Settings**   | Configure thresholds, capital, risk                |

---

## 📌 Tech Stack

| Layer        | Technology                              |
| ------------ | --------------------------------------- |
| Frontend     | Streamlit + Plotly + Pandas             |
| Backend      | Python + threading + Bybit SDK          |
| Database     | PostgreSQL + SQLAlchemy ORM             |
| External API | Binance Futures, Bybit, Discord, Reddit |

---

## 🧩 Modular Design

Each part of AlgoTrader is decoupled and testable:

* Switch from Binance to any exchange (via DataProvider)
* Swap Bybit for Alpaca, Binance, etc.
* Add new strategy modules inside `trading_engine.py`

---

## ✅ Recent Updates (July 2025)

* ✅ Full support for PostgreSQL
* ✅ Toggle between Real/Virtual trading
* ✅ Discord and Reddit exports
* ✅ Technical chart overlays (EMA, BB, RSI)
* ✅ Performance charts and metrics
* ✅ Risk management system (drawdown, max trades)
* ✅ Threaded automation engine

---

## 📎 License & Disclaimer

This is an open-source educational tool for developing algorithmic trading strategies.

⚠️ **Disclaimer**: Use at your own risk. Real-money trading involves risk. This tool is for informational and development purposes only.

---
