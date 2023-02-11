# main
import requests, json, datetime, pickle
import numpy as np
import pandas as pd

from matplotlib import ticker, gridspec, dates, pyplot 
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as md

from datetime import datetime
import mplfinance as mpf
import dateutil


# nonebot
import re
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText, CommandArg
from nonebot.rule import to_me

check_lsur = on_command(
    "多空比",
    aliases={"lsur", "oi", "开仓量" },
    rule=to_me(),
    priority=5,
)

@check_lsur.handle()
async def handle_first_receive(matcher: Matcher, args: Message = CommandArg()) -> None:
    plain_text = args.extract_plain_text().strip()
    if plain_text and re.match(r"^\S+\s\S+$", plain_text):
        matcher.set_arg("check_lsur", args)

prompt = """\
请输入：标的 周期 以空格分隔\
"""

@check_lsur.got("check_lsur", prompt=prompt)
async def handle_check_lsur(
    symbol_and_interval: str = ArgPlainText("check_lsur")) -> None:
    try:
        symbol, interval = symbol_and_interval.split(" ", 1)
    except ValueError:
        await check_lsur.reject('出错了,你格式不对')
        return

    if "!" in symbol:
        symbol = symbol.replace('!', '')
    else:
        symbol = symbol + 'usdt'



    data = {
        'symbol': symbol,
        'pair': symbol,
        'period': interval,
        'interval': interval,
        'limit':'150'
    }


    # proxie={
    #     'http':'http://127.0.0.1:7890',
    #     'https':'http://127.0.0.1:7890'
    # }

    # Kline
    kline_url = 'https://fapi.binance.com/fapi/v1/klines'
    kline_json = requests.get(kline_url, params=data).json()
    # Lsur
    lsur_url = 'https://fapi.binance.com/futures/data/globalLongShortAccountRatio'
    lsur_data = requests.get(lsur_url, params=data).json()
    # Oi
    oi_url = 'https://fapi.binance.com/futures/data/openInterestHist'
    oi_data = requests.get(oi_url, params=data).json()
    # Fr
    fr_url = 'https://fapi.binance.com/fapi/v1/premiumIndex'
    fr_data = requests.get(fr_url, params=data).json()


    tmp  = []
    pair = []
    for base in kline_json:
        tmp  = []
        for i in range(0,6):
            if i == 0:
                base[i] = datetime.fromtimestamp(base[i]/1000)
            tmp.append(base[i])
        pair.append(tmp)
    df = pd.DataFrame(pair, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    df.date = pd.to_datetime(df.date)
    df.set_index("date", inplace=True)
    df = df.astype(float)

    lsur_df = pd.DataFrame(lsur_data)
    lsur_df['longShortRatio'] = lsur_df['longShortRatio'].astype(float)

    oi_df = pd.DataFrame(oi_data)
    oi_df['sumOpenInterest'] = oi_df['sumOpenInterest'].astype(float)

    last_fr = float(fr_data['lastFundingRate'])
    last_fr = str(f'{last_fr:.4%}')

    my_color = mpf.make_marketcolors(
                                    edge='black',
                                    wick='black',)
    style_w = mpf.make_mpf_style(marketcolors=my_color,
                                gridcolor='(0.82, 0.83, 0.85)')

    last_lusr ,last_oi, last_fr = str(lsur_df.iloc[[-1],[2]].values[0][0]), str(oi_df.iloc[[-1],[1]].values[0][0]) , str(last_fr)
    message_data = '现在的多空比为:' + last_lusr +'。开仓量为:'+ last_oi + '。资金费率为: ' + last_fr + '。'

    index  = [
        mpf.make_addplot(oi_df['sumOpenInterest'], panel = 1 , color = 'black', alpha=0.4, ylabel = 'Oi'),
        mpf.make_addplot(lsur_df['longShortRatio'], panel = 1 , color = 'red', alpha = 0.7, ylabel = 'Lsur'),
        ]

    plt = mpf.plot(
        df, type = 'candle',
        style = style_w, 
        addplot = index , 
        figsize=(17,8), 
        ylabel='Price',
        savefig=(r"C:\6.png"),
        ) # ,title = title_data
    await check_lsur.send(message_data)
    await check_lsur.finish(Message(r"[CQ:image,file=file:///c:\6.png,cache=1]")) 