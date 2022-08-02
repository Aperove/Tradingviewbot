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




search_tv = on_command(
    "查查",
    aliases={"查下", },
    rule=to_me(),
    priority=5,
)

@search_tv.handle()
async def handle_first_receive(matcher: Matcher, args: Message = CommandArg()) -> None:
    plain_text = args.extract_plain_text().strip()
    if plain_text and re.match(r"^\S+\s\S+$", plain_text):
        matcher.set_arg("search_tv", args)


prompt = """\
请输入：标的 周期 以空格分隔\
"""

@search_tv.got("search_tv", prompt=prompt)
async def handle_search_tv(
    symbol_and_interval: str = ArgPlainText("search_tv")) -> None:
    try:
     symbol, interval = symbol_and_interval.split(" ", 1)
    except ValueError:
        await search_tv.reject('出错了,你格式不对')
        return

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
        # 'symbol' : symbol ,
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
    driver.set_window_size(1500,900)
    driver.implicitly_wait(10) #隐式等待
    driver.get(url)

    WebDriverWait(driver, 10, 1).until(EC.visibility_of_element_located((By.CLASS_NAME,'chart-gui-wrapper')))

    element = driver.find_element(By.XPATH, "//*[@class='group-T57LDNqT newStyles-T57LDNqT']")
    element.click()

    element = driver.find_element(By.XPATH, "//*[@class='inputContainer-CcsqUMct']//input")
    element.send_keys(symbol)

    sleep(2)

    element = driver.find_element(By.XPATH, "//*[@class='description-uhHv1IHJ'][1]")
    element.click()

    sleep(2)

    driver.save_screenshot('c:\\2.png') # get_screenshot_as_base64()      # 这个是获取base64备用
    driver.quit()
    await search_tv.finish(Message(r"[CQ:image,file=file:///c:\2.png,cache=1]")) 

