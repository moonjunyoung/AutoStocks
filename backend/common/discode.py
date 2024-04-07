import discord
import asyncio
import yaml
import os
import subprocess
import datetime

intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)


# 봇 설정 클래스
class ClientSettings:
    def __init__(self):
        self.APP_KEY = ""
        self.APP_SECRET = ""
        self.CANO = ""
        self.ACNT_PRDT_CD = ""
        self.URL_BASE = ""
        self.DISCORD_WEBHOOK_URL = ""


# 봇 토큰 설정
TOKEN = ""

import requests
import json
import time
import yaml

with open("config.yaml", encoding="UTF-8") as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
APP_KEY = _cfg["APP_KEY"]
APP_SECRET = _cfg["APP_SECRET"]
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ0b2tlbiIsImF1ZCI6IjgyODQyZGY0LWI5NzQtNDYzOC05NDMyLWM5ZmM0ODhmMGI2NyIsImlzcyI6InVub2d3IiwiZXhwIjoxNzExNzcxNTk0LCJpYXQiOjE3MTE2ODUxOTQsImp0aSI6IlBTQzJzeG11cHc1c1pzSTJFYzhhY3k0VHQxWFBMcXZsejRiVyJ9.7pEj0nWC8stEcwipOWS92135JVjdW_Uz4iDVBnt89y8u1YErFbUT2w_gtaT7JEMwjGITnYyYcs1fQL7nlHn0zw"
CANO = _cfg["CANO"]
ACNT_PRDT_CD = _cfg["ACNT_PRDT_CD"]
DISCORD_WEBHOOK_URL = _cfg["DISCORD_WEBHOOK_URL"]
URL_BASE = _cfg["URL_BASE"]


def send_message(msg):
    """디스코드 메세지 전송"""
    now = datetime.datetime.now()
    message = {"content": f"[{now.strftime('%m-%d %H:%M:%S')}] {str(msg)}"}
    requests.post(DISCORD_WEBHOOK_URL, data=message)
    print(message)


def get_access_token():
    """토큰 발급"""
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
    }
    PATH = "oauth2/tokenP"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    ACCESS_TOKEN = res.json()["access_token"]
    return ACCESS_TOKEN


def hashkey(datas):
    """암호화"""
    PATH = "uapi/hashkey"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        "content-Type": "application/json",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
    }
    res = requests.post(URL, headers=headers, data=json.dumps(datas))
    hashkey = res.json()["HASH"]
    return hashkey


def get_current_price(code):
    """현재가 조회"""
    PATH = "uapi/domestic-stock/v1/quotations/inquire-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "FHKST01010100",
    }
    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": code,
    }
    res = requests.get(URL, headers=headers, params=params)
    return int(res.json()["output"]["stck_prpr"])


def get_stock_balance():
    # 주식 잔고조회
    PATH = "uapi/domestic-stock/v1/trading/inquire-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "TTTC8434R",
        "custtype": "P",
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }
    print(headers, params)
    res = requests.get(URL, headers=headers, params=params)
    try:
        print(res.json())
        stock_list = res.json()["output1"]
        evaluation = res.json()["output2"]
        stock_dict = {}
        msg = ""
        msg += "========주식 보유잔고========\n\n"
        for stock in stock_list:
            if int(stock["hldg_qty"]) > 0:
                stock_dict[stock["pdno"]] = stock["hldg_qty"]
                msg += f"{stock['prdt_name']}({stock['pdno']}): {(stock['hldg_qty'])}주\n\n현재가격 : {get_current_price(stock['pdno'])}\n\n평균매수단가 : {(stock['pchs_avg_pric'])}\n\n평가손익 : {stock['evlu_pfls_rt']}%\n\n===========================\n\n"

        msg += f"주식 평가 금액: {int(evaluation[0]['scts_evlu_amt']):,}원\n\n"

        msg += f"평가 손익 합계: {int(evaluation[0]['evlu_pfls_smtl_amt']):,}원\n\n"

        msg += f"총 평가 금액: {int(evaluation[0]['tot_evlu_amt']):,}원\n\n"

        msg += "==========================="
        print(msg)
        send_message(msg)
        return msg
    except KeyError as e:
        # API 응답에서 예상한 키가 존재하지 않는 경우
        msg = f"API 응답에서 예상한 키가 존재하지 않습니다: {str(e)}"
        # 로그에 에러 메시지 기록
        print(msg)
        return msg
        # 에러 메시지를 보내거나 다른 처리를 할 수 있음


def inquire_possible_revocation_orders():
    """주식 정정조회"""
    PATH = "/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "TTTC8036R",
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
        "INQR_DVSN_1": "1",
        "INQR_DVSN_2": "0",
    }
    res = requests.get(URL, headers=headers, params=params)
    # cash = res.json()['output1']['odno']
    print(res.json())
    send_message(f"주문 정정 가능 주문번호 : {res.json()}")
    # return int(cash)


def get_balance():
    """현금 잔고조회"""
    PATH = "uapi/domestic-stock/v1/trading/inquire-psbl-order"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "TTTC8908R",
        "custtype": "P",
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": "005930",
        "ORD_UNPR": "65500",
        "ORD_DVSN": "01",
        "CMA_EVLU_AMT_ICLD_YN": "Y",
        "OVRS_ICLD_YN": "Y",
    }
    res = requests.get(URL, headers=headers, params=params)
    cash = res.json()["output"]["ord_psbl_cash"]
    send_message(f"주문 가능 현금 잔고: {cash}원")
    return int(cash)


def buy(code, qty=1):
    """주식 최우선유리가 매수"""
    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "03",
        "ORD_QTY": str(int(qty)),
        "ORD_UNPR": "0",
    }
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "TTTC0802U",
        "custtype": "P",
        "hashkey": hashkey(data),
    }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()["rt_cd"] == "0":
        try:
            msg1 = res.json()["msg1"]
            ORD_TMD = res.json()["output"]["ORD_TMD"]
            message = f"[주문완료] 계좌번호{CANO}-{ACNT_PRDT_CD} \n 종목코드{code} {qty}주 {msg1}"
            send_message(message)
            order = "매수"
            return order, message
        except KeyError as e:
            print(f"Error extracting order completion information: {e}")
            send_message(f"[오류발생]{str(res.json())}")
            return True
    else:
        send_message(f"[매수 실패]{str(res.json())}")
        msg1 = res.json()["msg1"]
        order = "매수실패"
        message = (
            f"[매수실패] 계좌번호{CANO}-{ACNT_PRDT_CD} \n 종목코드{code} {qty}주 {msg1}"
        )
        return order, message


def sell(code, qty=1):
    """주식 시장가 매도"""
    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "07",
        "ORD_QTY": qty,
        "ORD_UNPR": "0",
    }
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "TTTC0801U",
        "custtype": "P",
        "hashkey": hashkey(data),
    }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    print(res.json())
    if res.json()["rt_cd"] == "0":
        try:
            msg1 = res.json()["msg1"]
            ORD_TMD = res.json()["output"]["ORD_TMD"]
            message = f"[주문완료] 계좌번호{CANO}-{ACNT_PRDT_CD} \n 종목코드{code} {qty}주 {msg1}"
            send_message(message)
            order = "매도"
            return order, message
        except KeyError as e:
            print(f"Error extracting order completion information: {e}")
            send_message(f"[오류발생]{str(res.json())}")
            return True
    else:
        send_message(f"[매도 실패]{str(res.json())}")
        msg1 = res.json()["msg1"]
        order = "매도실패"
        message = (
            f"[매도실패] 계좌번호{CANO}-{ACNT_PRDT_CD} \n 종목코드{code} {qty}주 {msg1}"
        )
        print(message, order)
        return order, message


# 임베드를 보내는 함수 정의
async def send_embed(ch, order, code, price):
    now = datetime.datetime.now()
    time = now.strftime("%m-%d %H:%M:%S")
    if order == "매수":
        color = discord.Color.red()
    elif order == "매도":
        color = discord.Color.blue()
    else:
        color = discord.Color.dark_orange()
        embed = discord.Embed(title="[오류발생]", description="", color=color)
        embed.add_field(
            name=f"오류코드 : {order}", value=f"사유 : {code}", inline=False
        )
        embed.set_footer(text=f"주문 시간 : {time}")
        msg = await ch.send(embed=embed)
        return

    embed = discord.Embed(title=order, description="", color=color)
    embed.add_field(name=f"종목코드 : {code}", value=f"가격 : {price}", inline=False)
    embed.set_footer(text=f"주문 시간 : {time}")
    msg = await ch.send(embed=embed)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    now = datetime.datetime.now()
    order = None
    code = None
    price = None
    time = now.strftime("%m-%d %H:%M:%S")
    ch = message.channel

    if message.author == client.user:
        return

    channel_id = 1222483915969921027  # 여기에 채널의 ID를 입력하세요
    channel = client.get_channel(channel_id)

    if ch == channel:
        send_message(f"\n요청자 {str(message.author)} \n요청내용 {message.content}")
    try:
        if message.content.startswith("초기설정"):
            await message.delete()
            embed = discord.Embed(
                title="사이트 링크:",
                description="[한국투자증권](https://apiportal.koreainvestment.com/intro)\n[트레이딩뷰](https://kr.tradingview.com/scripts/?script_type=strategies)",
                color=discord.Color.blue(),
            )
            await message.channel.send(embed=embed)
            user_message = await message.channel.send("APP_KEY를 입력해주세요.")
            app_key = await client.wait_for(
                "message", check=lambda m: m.author == message.author
            )
            await user_message.delete()
            await ch.purge(limit=1)

            user_message = await message.channel.send("APP_SECRET을 입력해주세요.")
            app_secret = await client.wait_for(
                "message", check=lambda m: m.author == message.author
            )
            await user_message.delete()
            await ch.purge(limit=1)

            user_message = await message.channel.send(
                "계좌를 입력해주세요. ex) 200000-01이면 200000만 입력"
            )
            cano = await client.wait_for(
                "message", check=lambda m: m.author == message.author
            )
            await user_message.delete()
            await ch.purge(limit=1)
            user_message = await message.channel.send(
                "계좌구분을 입력해주세요. ex) 200000-01에서 01을 입력"
            )
            acnt_prdt_cd = await client.wait_for(
                "message", check=lambda m: m.author == message.author
            )
            await user_message.delete()
            await ch.purge(limit=1)
            user_message = await message.channel.send(
                "DISCORD_WEBHOOK_URL을 입력해주세요."
            )
            discord_webhook_url = await client.wait_for(
                "message", check=lambda m: m.author == message.author
            )
            await user_message.delete()
            await ch.purge(limit=1)
            # 설정 파일에 값 저장
            settings = ClientSettings()
            settings.APP_KEY = app_key.content
            settings.APP_SECRET = app_secret.content
            settings.CANO = cano.content
            settings.ACNT_PRDT_CD = acnt_prdt_cd.content
            settings.URL_BASE = "https://openapi.koreainvestment.com:9443"
            settings.DISCORD_WEBHOOK_URL = discord_webhook_url.content

            # YAML 파일에 설정 저장
            with open("config.yaml", "w") as f:
                yaml.dump(settings.__dict__, f)

            await message.channel.send("Configuration saved successfully!")

        elif message.content.startswith("정보"):
            try:
                with open("config.yaml", "r") as f:
                    settings = yaml.safe_load(f)
                await message.channel.send("입력된 정보:")
                await message.channel.send(f"```yaml\n{yaml.dump(settings)}\n```")
            except FileNotFoundError:
                await message.channel.send(
                    "초기설정이 완료되지 않아 확인이 불가합니다."
                )

        elif message.content.startswith("지우기"):
            await ch.purge(limit=100)

        elif message.content.startswith("[주문]"):
            # '[매도]'로 시작하는 메시지 처리
            print(message.content)

            try:
                lines = message.content.split("\n")
                if len(lines) == 4:  # 메시지가 4줄로 이루어져 있는지 확인
                    order_line = lines[1].strip()  # 종목명 라인
                    code_line = lines[2].strip()  # 종목코드 라인
                    price_line = lines[3].strip()  # 현재가격 라인

                    # 종목명, 종목코드, 현재가격 추출
                    order = order_line.split(":")[1].strip()
                    code = code_line.split(":")[1].strip()
                    price = price_line.split(":")[1].strip()
                    print(order, code, price)
                    if order == "매수":
                        order, message = buy(code, 1)
                        await send_embed(ch, order, message, price)
                    elif order == "매도":
                        order, message = sell(code, 1)
                        await send_embed(ch, order, message, price)

                    # 매도 정보를 krstock.py 모듈에 전달하여 실행
                    # await execute_krstock_async(symbol, code, price)
            except Exception as e:
                msg = str(e)
                await send_embed(ch, msg, message.content, price)

        elif message.content.startswith("정정"):
            inquire_possible_revocation_orders()

        elif message.content.startswith("자산조회"):
            msg = get_stock_balance()
            embed = discord.Embed(title="자산조회", description="", color=0x70A0FF)
            embed.add_field(name=f"{msg}", value="", inline=False)
            embed.set_footer(text=f"요청 시간 : {time}")
            await ch.send(embed=embed)
    except Exception as e:
        msg = str(e)
        await send_embed(ch, msg, message.content, price)


try:
    # ACCESS_TOKEN = get_access_token()
    print(ACCESS_TOKEN)
except Exception as e:
    send_message(f"[오류 발생]{e}")
client.run(TOKEN)
