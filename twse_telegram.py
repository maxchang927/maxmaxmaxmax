#!/usr/bin/env python3
"""
台股大盤收盤資訊 → Telegram Bot
每日 13:35 由 GitHub Actions 觸發
"""

import os
import json
import urllib.requesth
import urllib.parse
from datetime import datetime

# ── 設定（由環境變數讀取）──
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

TWSE_API = "https://openapi.twse.com.tw/v1/exchangeReport/FMTQIK"


def fetch_market_data() -> dict:
    """抓取 TWSE 當日大盤資料"""
    req = urllib.request.Request(
        TWSE_API,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if not data:
        raise ValueError("TWSE API 回傳空資料（今日可能休市）")

    return data[-1]  # 最新一筆（當日）


def format_message(d: dict) -> str:
    """格式化 Telegram 訊息"""
    # 民國日期轉西元
    roc_date = d.get("Date", "")
    try:
        parts = roc_date.split("/")
        year = int(parts[0]) + 1911
        date_str = f"{year}/{parts[1]}/{parts[2]}"
    except Exception:
        date_str = roc_date

    taiex = d.get("TAIEX", "N/A")
    change = d.get("Change", "0")
    trading_value = d.get("TradeValue", "0")

    # 成交金額：單位億元
    try:
        value_billion = float(trading_value.replace(",", "")) / 1e8
        value_str = f"{value_billion:,.2f} 億元"
    except Exception:
        value_str = trading_value

    # 漲跌符號
    try:
        chg = float(change.replace(",", ""))
        arrow = "🔺" if chg > 0 else ("🔻" if chg < 0 else "➡️")
        change_str = f"{arrow} {chg:+.2f}"
    except Exception:
        change_str = change

    msg = (
        f"📊 *台股大盤收盤* {date_str}\n"
        f"━━━━━━━━━━━━━\n"
        f"加權指數：*{taiex}*\n"
        f"漲跌：{change_str}\n"
        f"成交金額：{value_str}\n"
        f"━━━━━━━━━━━━━\n"
        f"🕐 {datetime.now().strftime('%H:%M')} 自動推播"
    )
    return msg


def send_telegram(text: str) -> None:
    """發送 Telegram 訊息"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        if not result.get("ok"):
            raise RuntimeError(f"Telegram API 錯誤：{result}")


def main():
    try:
        data = fetch_market_data()
        msg = format_message(data)
        send_telegram(msg)
        print("✅ 推播成功")
        print(msg)
    except Exception as e:
        error_msg = f"❌ 台股推播失敗：{e}"
        print(error_msg)
        try:
            send_telegram(error_msg)
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()
