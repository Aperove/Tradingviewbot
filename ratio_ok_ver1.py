# main
import requests, json, datetime, pickle
import numpy as np
import pandas as pd
import time, ccxt


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
    "ok",
    aliases={"oiok"},
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

    # if "1h" in interval:
    #     interval = '1H'
    # else:
    #     interval = interval

    symbol = symbol.upper()




    OKEX_CONFIG = {
        'apiKey': '',
        'secret': '',
        'timeout': 3000,
        'rateLimit': 10,
        'enableRateLimit': False}     # 是否开启Api频率限制

    exchange = ccxt.okx()
    # print(*list(dir(ccxt.okx())), sep='\n') # 查看所有功能


#############################################

    period = '1h'

    timeframe = period



    kline_symbol = symbol + '-USDT-SWAP'

    kline_json = exchange.fetchOHLCV(kline_symbol,timeframe) # 标的+周期

    df = pd.DataFrame(kline_json, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    df.date = pd.to_datetime(df.date)
    df.set_index("date", inplace=True)
    df = df.astype(float)


    # 历史开仓量
    if "1h" in interval:
        interval = '1H'
    else:
        interval = interval

    data = {'ccy':symbol,
        'period':interval,
        'limit':'100',
    }
    
    oi_json = exchange.publicGetRubikStatContractsOpenInterestVolume(data)
    oi_data = oi_json['data']

    oi_df = pd.DataFrame(oi_data, columns=['date', 'vol', 'oi'])
    # 转化为int
    oi_df = oi_df.astype(float)
    oi_df.date = pd.to_datetime(oi_df.date)
    oi_df


    # 历史多空比

    lsur_json = exchange.publicGetRubikStatContractsLongShortAccountRatio(data)
    lsur_data = lsur_json['data']

    lsur_df = pd.DataFrame(lsur_data, columns=['date', 'ratio'])
    # 转化为int
    lsur_df = lsur_df.astype(float)
    lsur_df.date = pd.to_datetime(lsur_df.date)


    # 合并
    Oi_Lsur_df = pd.merge(df,oi_df,on = 'date')
    Oi_Lsur_df = pd.merge(Oi_Lsur_df,lsur_df,on = 'date')
    Oi_Lsur_df.set_index("date", inplace=True)

    # 把持仓总价值除以close得到张数
    Oi_Lsur_df['oi'] = Oi_Lsur_df['vol'] / Oi_Lsur_df['close']


    # 消息内容
    # last_lusr ,last_oi, last_fr = str(Oi_Lsur_df.iloc[[-1],[2]].values[0][0]), str(oi_df.iloc[[-1],[1]].values[0][0]) , str(last_fr)
    last_lusr = str(Oi_Lsur_df.iloc[[-1],[-1]].values[0][0])
    message_data = '现在的多空比为:' + last_lusr +'。'

    my_color = mpf.make_marketcolors(
                                    edge='black',
                                    wick='black',)
    style_w = mpf.make_mpf_style(marketcolors=my_color,
                                gridcolor='(0.82, 0.83, 0.85)')


    index  = [
        mpf.make_addplot(Oi_Lsur_df['oi'], panel = 1 , color = 'black',alpha=0.4),
        mpf.make_addplot(Oi_Lsur_df['ratio'], panel = 1 , color = 'red',alpha=0.7)
        ]


    my_color = mpf.make_marketcolors(
                                    edge='black',
                                    wick='black',)
    style_w = mpf.make_mpf_style(marketcolors=my_color,
                                gridcolor='(0.82, 0.83, 0.85)')

    mpf.plot(
        Oi_Lsur_df, type = 'candle',
        style = style_w, 
        addplot = index , 
        figsize=(16,6), 
        ylabel='',
        savefig=(r"C:\7.png"),
        )
    await check_lsur.send(message_data)
    await check_lsur.finish(Message(r"[CQ:image,file=file:///c:\7.png,cache=1]")) 