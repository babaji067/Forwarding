# 🤖 Forwarding Automation Bot

A powerful **subscription-based forwarding automation bot** built with  
**python-telegram-bot v21+**, designed for **Heroku / Pydroid / VPS**.

---

## ✨ Features

- 🔁 Interval-based auto forwarding
- 💳 Subscription system (Weekly / Monthly)
- 👑 Owner-only payment approval
- 💰 Payments supported:
  - UPI
  - Binance ID
  - USDT (TRC20 / BEP20)
- 📦 ZIP upload / withdraw
- ⏱ Custom message & time setup
- ⬅️ Step-by-step BACK navigation
- 📱 Reply Keyboard (buttons near typing box)
- ☁️ MongoDB optional (auto fallback to memory)
- 🚀 Heroku deploy ready

---

## 🚀 One-Click Deploy to Heroku

Click the button below to deploy directly from this repository 👇

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/babaji067/Forwarding-)

---

## ⚙️ Environment Variables (Required)

After deploying, go to **Heroku → Settings → Config Vars**  
and add the following:

| Key | Description |
|---|---|
| `BOT_TOKEN` | Telegram Bot Token from @BotFather |
| `OWNER_ID` | Your Telegram numeric user ID |

### Optional (MongoDB)
| Key | Description |
|---|---|
| `MONGO_URI` | MongoDB Atlas connection string |

> If `MONGO_URI` is not set, the bot runs in **memory mode**.

---

## 🧱 Project Structure
