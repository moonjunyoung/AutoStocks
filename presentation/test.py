from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# 필요한 패키지 목록
required_packages = ["fastapi", "uvicorn", "jinja2", "python-multipart", "aiofiles"]

for package in required_packages:
    try:
        dist = __import__(package)
        print("{} is installed".format(dist.__name__))
    except ImportError:
        print("{} is NOT installed".format(package))
        print("Installing {}...".format(package))
        install(package)

app = FastAPI()

# HTML 파일 경로
html_file = "./templates/index.html"
# 정적 파일을 서빙할 디렉토리를 지정합니다.
app.mount("/static", StaticFiles(directory="static"), name="static")
# HTML 파일 읽기
with open(html_file, "r", encoding="utf-8") as file:
    html_content = file.read()
# HTML 파일을 렌더링할 템플릿 엔진을 설정합니다.
templates = Jinja2Templates(directory="templates")
# 각 페이지에 대한 경로 및 해당 HTML 반환
@app.get("/", response_class=HTMLResponse)
async def get_root():
    return html_content

@app.get("/index", response_class=HTMLResponse)
async def get_index():
    return html_content

@app.get("/ui-buttons", response_class=HTMLResponse)
async def get_ui_buttons(request: Request):
    return templates.TemplateResponse("ui-buttons.html", {"request": request})
    

@app.get("/alerts", response_class=HTMLResponse)
async def get_alerts(request: Request):
    return templates.TemplateResponse("ui-alerts.html", {"request": request})
# 매수 페이지에 대한 핸들러
@app.get("/ui-card", response_class=HTMLResponse)
async def get_ui_card(request: Request):
    # buy_orders를 여기서 가져오도록 변경
    buy_orders = [
        {"code": "000080", "price": "20,500"}
    ]
    return templates.TemplateResponse("ui-card.html", {"request": request, "buy_orders": buy_orders})

# 매수 처리를 위한 핸들러
@app.post("/buy", response_class=HTMLResponse)
async def post_ui_card(request: Request, company_name: str = Form(...)): # 종목명 입력 받음
    # 종목명을 이용하여 종목코드 가져오기
    print(company_name)
    # from get_code import save_all_company_info_to_json
    # await save_all_company_info_to_json()
    from get_code import get_company_info
    company_info = await get_company_info(company_name)

    sell_orders = []

    for _, row in company_info.iterrows():
        # 매도 주문 추가
        sell_orders.append({"company_name": row['회사명'], "code": row['종목코드'], "price": "20,550", "url": row['홈페이지']})
        

    return templates.TemplateResponse("ui-card.html", {"request": request, "sell_orders": sell_orders})




@app.get("/ui-forms", response_class=HTMLResponse)
async def get_ui_forms():
    return html_content

@app.get("/ui-typography", response_class=HTMLResponse)
async def get_ui_typography():
    return html_content

@app.get("/authentication-login", response_class=HTMLResponse)
async def get_authentication_login(request: Request):
    return templates.TemplateResponse("authentication-login.html", {"request": request})

@app.get("/authentication-register", response_class=HTMLResponse)
async def get_authentication_register(request: Request):
    return templates.TemplateResponse("authentication-register.html", {"request": request})

@app.get("/icon-tabler", response_class=HTMLResponse)
async def get_icon_tabler():
    return html_content

@app.get("/sample-page", response_class=HTMLResponse)
async def get_sample_page():
    return html_content

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

