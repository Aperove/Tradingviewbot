import re
from time import sleep
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
# command
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.matcher import Matcher
from nonebot.params import ArgPlainText, CommandArg
from nonebot.rule import to_me


# 设置本地账户的option
options = webdriver.ChromeOptions()
options.add_argument(r'--user-data-dir=C:\Users\Administrator\AppData\Local\Google\Chrome\User Data') # 获取到的User Data路径
options.add_argument("--profile-directory=Default") # 获取到的--profile-directory值
options.add_argument("--headless") # 配置无头模式




check_tv = on_command(
    "看看",
    aliases={"看下", },
    rule=to_me(),
    priority=5,
)

@check_tv.handle()
async def handle_first_receive(matcher: Matcher, args: Message = CommandArg()) -> None:
    plain_text = args.extract_plain_text().strip()
    if plain_text and re.match(r"^\S+\s\S+$", plain_text):
        matcher.set_arg("check_tv", args)


prompt = """\
请输入：标的 周期 以空格分隔\
"""

@check_tv.got("check_tv", prompt=prompt)
async def handle_check_tv(
    symbol_and_interval: str = ArgPlainText("check_tv")) -> None:
    try:
     symbol, interval = symbol_and_interval.split(" ", 1)
    except ValueError:
        await check_tv.reject('出错了,你格式不对')
        return
    
    # 区分标的
    if "!" in symbol:
        symbol = symbol.replace('!', '')
    elif "OK1" in symbol:
        symbol = symbol.replace('OK1', 'OKEX:') + 'USDT'
    elif "FTX1" in symbol:
        symbol = symbol.replace('FTX1', 'FTX:') + 'USD'
    elif "A1" in symbol:
        if "A1600" in symbol:
            symbol = symbol.replace('A1', 'SSE:') 
        else:
            symbol = symbol.replace('A1', 'SZSE:') 
    else:
        symbol = 'BINANCE:' + symbol + 'USDT'

    # 处理周期

    if "M" in interval:
        interval = interval.replace('M', '')
    elif "m" in interval:
        interval = interval.replace('m', '')
    elif "H" in interval:
        interval = interval.replace('H', '')
        interval = str(int(interval) * 60)
    elif "h" in interval:
        interval = interval.replace('h', '')
        interval = str(int(interval) * 60)
    elif "d" in interval:
        interval = interval.replace('d', 'D')
    elif "w" in interval:
        interval = interval.replace('w', 'W')
    else:
        interval = interval

    # 处理链接
    data = {
        'symbol' : symbol ,
        'interval' : interval ,
    }
    js_params = []
    for params in data.items():
        i = "=".join(params)
        js_params.append(i)

    params = "&".join(js_params)
    url = 'https://www.tradingview.com/chart/aMqV8I3f/?'+params

    # 导入配置并启动浏览器打开链接
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1500,900)    #页面宽高
    driver.get(url)

    WebDriverWait(driver, 10, 1).until(EC.visibility_of_element_located((By.CLASS_NAME,'chart-gui-wrapper')))

    sleep(1)

    driver.save_screenshot('c:\\1.png') # get_screenshot_as_base64()      # 这个是获取base64备用
    driver.quit()
    await check_tv.finish(Message(r"[CQ:image,file=file:///c:\1.png,cache=0]")) 

