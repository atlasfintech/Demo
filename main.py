# main.py

import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
from finnhub import Client as FinnhubClient
from telegram import Bot

# Telegram bilgilerini doğrudan buraya yaz
TELEGRAM_TOKEN = "7764012513:AAH1ky95MH1XwvsXmWNd0V-1Lc6uGSn3FcA"
TELEGRAM_CHAT_ID = 6876481988

FINNHUB_API_KEY = "d0mit59r01qqqs59pcfgd0mit59r01qqqs59pcg0"

finnhub_client = Client(api_key=FINNHUB_API_KEY)
telegram_bot = Bot(token=TELEGRAM_TOKEN)

BIST100 = ["THYAO.IS", "AKBNK.IS", "GARAN.IS"]
BIST30 = BIST100[:30]

def normalize(sym):
    return sym.strip().upper() + ".IS" if not sym.endswith(".IS") else sym

def fetch_candles(sym, resolution, days):
    now = dt.datetime.utcnow()
    end = int(now.timestamp())
    start = int((now - dt.timedelta(days=days)).timestamp())
    res = finnhub_client.stock_candles(symbol, resolution, _from, to)
    if res["s"] != "ok": 
        return None
    df = pd.DataFrame({
        "time": pd.to_datetime(res["t"], unit="s"),
        "open": res["o"], "high": res["h"],
        "low": res["l"], "close": res["c"], "volume": res["v"]
    }).set_index("time")
    return df.dropna()

from ta.trend import MACD, EMAIndicator, ADXIndicator, CCIIndicator, IchimokuIndicator
from ta.momentum import RSIIndicator, StochasticOscillator, StochRSIIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator, MFIIndicator
from ta.trend import PSARIndicator

def enrich(df):
    df = df.copy()
    df["rsi"] = RSIIndicator(df["close"]).rsi()
    df["macd_hist"] = MACD(df["close"], 26, 12, 9).macd_diff()
    df["ema20"] = EMAIndicator(df["close"], 20).ema_indicator()
    df["ema50"] = EMAIndicator(df["close"], 50).ema_indicator()
    df["atr10"] = AverageTrueRange(df["high"], df["low"], df["close"]).average_true_range()
    df["bb_hi"] = BollingerBands(df["close"]).bollinger_hband()
    df["bb_lo"] = BollingerBands(df["close"]).bollinger_lband()
    df["adx"] = ADXIndicator(df["high"], df["low"], df["close"]).adx()
    df["stoch"] = StochasticOscillator(df["high"], df["low"], df["close"]).stoch()
    df["stochrsi"] = StochRSIIndicator(df["close"]).stochrsi()
    df["willr"] = -100 * (df["high"].rolling(14).max() - df["close"]) / (df["high"].rolling(14).max() - df["low"].rolling(14).min())
    df["cci"] = CCIIndicator(df["high"], df["low"], df["close"]).cci()
    df["obv"] = OnBalanceVolumeIndicator(df["close"], df["volume"]).on_balance_volume()
    df["mfi"] = MFIIndicator(df["high"], df["low"], df["close"], df["volume"]).money_flow_index()
    ichimoku = IchimokuIndicator(df["high"], df["low"])
    df["ichi_a"] = ichimoku.ichimoku_a()
    df["ichi_b"] = ichimoku.ichimoku_b()
    df["psar"] = PSARIndicator(df["high"], df["low"], df["close"]).psar()
    df["rsi_slope"] = df["rsi"].diff()
    df["macd_slope"] = df["macd_hist"].diff()
    df["rsi_avg"] = df["rsi"].rolling(20).mean()
    df["rsi_th_low"] = df["rsi_avg"] - 10
    df["rsi_th_high"] = df["rsi_avg"] + 10
    return df.dropna()

def quality_filters(df_d, df_h):
    ld, lh = df_d.iloc[-1], df_h.iloc[-1]
    time_align = (
        (ld.rsi < ld.rsi_th_low and lh.rsi < lh.rsi_th_low and ld.rsi_slope > 0 and lh.rsi_slope > 0) or
        (ld.rsi > ld.rsi_th_high and lh.rsi > lh.rsi_th_high and ld.rsi_slope < 0 and lh.rsi_slope < 0)
    )
    ema_cross = (ld.ema20 > ld.ema50 and lh.ema20 > lh.ema50) or (ld.ema20 < ld.ema50 and lh.ema20 < lh.ema50)
    macd_dir = (ld.macd_hist > 0 and lh.macd_hist > 0) or (ld.macd_hist < 0 and lh.macd_hist < 0)
    adx_ok = ld.adx > 20 and lh.adx > 20
    vol_ok = ld.atr10 > df_d["atr10"].rolling(5).mean().iloc[-1] and ld.obv > df_d["obv"].iloc[-2]
    agree = time_align and ema_cross and macd_dir and adx_ok and vol_ok
    return {"align": time_align, "ema_cross": ema_cross, "macd_dir": macd_dir, "adx": adx_ok, "vol_ok": vol_ok, "agree": agree}

def check_signal(sym):
    df_d = fetch_candles(sym, "D", 90)
    df_h = fetch_candles(sym, "60", 5)
    if df_d is None or df_h is None: 
        return None
    df_d, df_h = enrich(df_d), enrich(df_h)
    f = quality_filters(df_d, df_h)
    if f["agree"]:
        direction = "AL" if df_d.iloc[-1].rsi_slope > 0 else "SAT"
        return f"SİNYAL [{sym}] → {direction} ✅\n{f}"
    return f"RED [{sym}] ❌\n{f}"

@st.cache_data(show_spinner=False)
def run_backtest(sym):
    df = fetch_candles(sym, "D", 180)
    if df is None: 
        return "Veri alınamadı."
    df = enrich(df)
    results = []
    for i in range(50, len(df)-5):
        df_d = df.iloc[:i+1]
        df_h = df.iloc[i-24:i+1]
        f = quality_filters(df_d, df_h)
        if f["agree"]:
            entry = df.iloc[i]
            direction = "AL" if entry.rsi_slope > 0 else "SAT"
            for exit in df.iloc[i+1:i+6].itertuples():
                gain = (exit.close - entry.close) / entry.close if direction == "AL" else (entry.close - exit.close) / entry.close
                if 0.05 <= gain <= 0.10:
                    results.append({
                        "Tarih": entry.Index.strftime("%Y-%m-%d"),
                        "Yön": direction, 
                        "Giriş": round(entry.close, 2),
                        "Çıkış": round(exit.close, 2), 
                        "Getiri (%)": round(gain * 100, 2),
                        "Vade (gün)": (exit.Index - entry.Index).days
                    })
                    break
    return pd.DataFrame(results) if results else "Sinyal bulunamadı."

def notify(msg):
    try:
        telegram_bot.send_message(chat_id=int(TELEGRAM_CHAT_ID), text=msg)
    except Exception as e:
        print(f"Telegram gönderme hatası: {e}")

st.set_page_config(page_title="AtlasTrade AutoScan")
st.title("📊 AtlasTrade Otomatik Tarayıcı")

mode = st.radio("Mod:", ["BIST100", "BIST30", "Tek Hisse", "Backtest"])
custom = st.text_input("Hisse Kodu", value="THYAO") if mode in ["Tek Hisse", "Backtest"] else None

if st.button("🔍 Tara") and mode != "Backtest":
    syms = BIST100 if mode == "BIST100" else BIST30 if mode == "BIST30" else [normalize(custom)]
    for sym in syms:
        result = check_signal(sym)
        st.write(result)
        if result and "SİNYAL" in result: 
            notify(result)

if mode == "Backtest" and st.button("🚀 Backtest Başlat"):
    results = run_backtest(normalize(custom))
    if isinstance(results, pd.DataFrame):
        st.dataframe(results)
        st.success(f"Toplam Sinyal: {len(results)}")
        st.info(f"Ortalama Getiri: {results['Getiri (%)'].mean():.2f}%")
    else:
        st.warning(results)
