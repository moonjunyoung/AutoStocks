from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import sys, base64, os, json, subprocess, requests
from cryptography.fernet import Fernet
from get_code import save_all_company_info_to_json

# 환경 변수에서 암호화 키를 로드합니다.
encryption_key = os.getenv('ENCRYPTION_KEY')
if encryption_key is None:
    raise ValueError("환경 변수 ENCRYPTION_KEY가 설정되지 않았습니다.")

# 암호화/복호화를 위한 Fernet 객체를 생성합니다.
cipher_suite = Fernet(encryption_key)

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
URL_BASE = "https://openapi.koreainvestment.com:9443"

# HTML 파일의 경로와 정적 파일 디렉토리를 상수로 정의합니다.
HTML_FILE_PATH = "./templates/index.html"
STATIC_DIR = "static"

# 정적 파일을 서빙할 디렉토리를 지정합니다.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 템플릿 엔진을 설정합니다.
templates = Jinja2Templates(directory="templates")

# HTML 파일을 앱 시작 시 미리 로드합니다.
with open(HTML_FILE_PATH, "r", encoding="utf-8") as file:
    html_content = file.read()
    

def decode_stored_id_token(stored_id_token_key):
    # 저장된 ID 토큰을 base64로 디코딩하고 복호화합니다.
    return decrypt_data(base64.b64decode(stored_id_token_key))

def encode_id_token(id_token):
    # ID 토큰을 암호화하고 base64로 인코딩합니다.
    return base64.b64encode(encrypt_data(id_token)).decode('utf-8')



def get_uuid(access_token):
    # 액세스 토큰을 설정하십시오.

    # 카카오 API를 사용하여 사용자 정보를 요청합니다.
    url = "https://kapi.kakao.com/v2/user/me"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)
    user_info = response.json()

    # 사용자 정보에서 UUID를 추출합니다.
    uuid = user_info.get("id")

    return uuid

def encrypt_data(data):
    """데이터를 암호화합니다."""
    # data가 문자열인 경우에만 encode를 수행합니다.
    if isinstance(data, str):
        data = data.encode()
    
    encrypted_data = cipher_suite.encrypt(data)
    return encrypted_data

def decrypt_data(encrypted_data):
    """암호화된 데이터를 복호화합니다."""
    decrypted_data = cipher_suite.decrypt(encrypted_data)
    return decrypted_data.decode()


# 유저 정보를 JSON 파일에 저장하고 비교하는 함수
def save_user_info_to_json(id_token, cano=None, app_key=None, app_secret=None, user_agent=None):
    # JSON 파일을 읽어서 데이터를 로드합니다.
    try:
        with open("user_info.json", "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}
        
    input_id_token_key = encode_id_token(id_token)
    found = False
    
    # 기존 데이터 비교 및 업데이트
    for stored_id_token_key, encoded_user_info in data.items():
        stored_decrypted_id_token = decode_stored_id_token(stored_id_token_key)
        if stored_decrypted_id_token == id_token:
            found = True
            
            # 기존 유저 정보 복호화
            user_info = {
                key: decode_stored_id_token(value) if value is not None else None
                for key, value in encoded_user_info.items()
            }
            
            # 새로운 데이터와 비교하고 업데이트
            need_update = False
            for key, new_value in [("cano", cano), ("app_key", app_key), ("app_secret", app_secret)]:
                if new_value is not None and user_info.get(key) != new_value:
                    user_info[key] = new_value
                    need_update = True
            
            # 업데이트가 필요한 경우 데이터를 업데이트
            if need_update:
                encoded_user_info = {
                    key: base64.b64encode(encrypt_data(value)).decode('utf-8') if value else None
                    for key, value in user_info.items()
                }
                data[stored_id_token_key] = encoded_user_info
                
            break
    
    # 새로운 데이터 추가
    if not found:
        user_info = {
            "id_token": id_token,
            "cano": cano,
            "app_key": app_key,
            "app_secret": app_secret,
            "user_agent": user_agent
        }
        
        # 유저 정보를 암호화하고 인코딩
        encoded_user_info = {
            key: base64.b64encode(encrypt_data(value)).decode('utf-8') if value else None
            for key, value in user_info.items()
        }
        data[input_id_token_key] = encoded_user_info
    
    # JSON 파일에 데이터를 저장
    with open("user_info.json", "w") as file:
        json.dump(data, file)

def load_user_info_from_json(id_token):
    # JSON 파일에서 유저 정보를 불러옵니다.
    try:
        with open("user_info.json", "r") as file:
            data = json.load(file)
            if id_token in data:
                encoded_user_info = data[id_token]
                
                # 유저 정보를 base64로 디코딩한 후 복호화합니다.
                user_info = {key: decrypt_data(base64.b64decode(value)) for key, value in encoded_user_info.items()}
                
                return user_info
            else:
                return None
    except FileNotFoundError:
        return None


def get_access_token(app_key, app_secret):
    """토큰 발급"""
    headers = {"content-type": "application/json"}
    body = {"grant_type": "client_credentials",
            "appkey": app_key,
            "appsecret": app_secret}
    PATH = "oauth2/tokenP"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    
    if res.status_code == 200:
        return res.json().get("access_token")
    else:
        return None

# 카카오 API로 auth코드 발급

def request_kakao_token(auth_code):
    url = "https://kauth.kakao.com/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": "18010fdee8889bcc676fad3404fa8ebd",  # 클라이언트 ID를 입력하세요.
        "redirect_uri": "http://hingurrr.shop:8000/kakao_auth",  # 리디렉션 URI를 입력하세요.
        "code": auth_code,
        "client_secret": "PwYrg0sq0LQUoEfBW80x7d4EoudDtwjc"  # 클라이언트 시크릿을 입력하세요.
    }
    response = requests.post(url, data=payload)
    return response.json()







# 루트 경로 함수
@app.get("/", response_class=HTMLResponse)
async def get_root(request: Request):
    # 템플릿을 렌더링하여 HTML 콘텐츠를 반환합니다.
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/index", response_class=HTMLResponse)
async def get_index():
    return html_content
@app.get("/kakao_auth")
async def kakao_auth(request: Request, code: str = Query(...), response_class=HTMLResponse):
    # 카카오 인증 코드를 이용하여 액세스 토큰 요청
    token_response = request_kakao_token(code)
    print(token_response)

    if "access_token" in token_response:
        # id_token을 얻은 경우
        access_token = token_response["access_token"]
        print(access_token)
        id_token = str(get_uuid(access_token))
        print(id_token)
        encryp_id_token = encrypt_data(id_token)
        encryp_id_token = base64.b64encode(encryp_id_token).decode('utf-8')
        
      
        
        # 클라이언트의 user-agent를 요청 객체에서 가져옵니다.
        user_agent = request.headers.get("user-agent", "unknown")
        # 암호화된 id_token 출력 (디버깅 목적)
        print(f"ID Token: {id_token},{encryp_id_token} User Agent: {user_agent}")
        # id_token과 user-agent를 JSON 파일에 저장합니다.
        save_user_info_to_json(id_token, cano=None, app_key=None, app_secret=None, user_agent=user_agent)

        # 클라이언트에게 전달할 HTML 생성
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <script>
                // 로컬 스토리지에 암호화된 id_token 저장
                localStorage.setItem("id_token", "{encryp_id_token}");
                
                // 홈 화면으로 이동
                window.location.href = 'http://hingurrr.shop:8000/';
            </script>
        </head>
        <body>
            <h1>Authentication successful!</h1>
            <p>Redirecting to the home page...</p>
        </body>
        </html>
        '''
        return HTMLResponse(content=html_content)

        # 템플릿 응답 생성
       
    else:
        return JSONResponse({"status": "error", "message": "액세스 토큰을 발급받을 수 없습니다."})




@app.get("/ui-buttons", response_class=HTMLResponse)
async def get_ui_buttons(request: Request):
    return templates.TemplateResponse("ui-buttons.html", {"request": request})

@app.get("/alerts", response_class=HTMLResponse)
async def get_alerts(request: Request):
    return templates.TemplateResponse("ui-alerts.html", {"request": request})

@app.get("/ui-card", response_class=HTMLResponse)
async def get_ui_card(request: Request):
    # buy_orders를 여기서 가져오도록 변경
    buy_orders = [
        {"code": "000080", "price": "20,500"}
    ]
    return templates.TemplateResponse("ui-card.html", {"request": request, "buy_orders": buy_orders})
@app.post("/api/save_company_info")
async def save_company_info():
    await save_all_company_info_to_json()
    return {"message": "Company information saved successfully"}

@app.post("/buy", response_class=HTMLResponse)
async def post_ui_card(request: Request, company_name: str = Form(...)): # 종목명 입력 받음
    # 종목명을 이용하여 종목코드 가져오기
    print(company_name)
   
    from get_code import get_company_info
    company_info = await get_company_info(company_name)

    sell_orders = []

    for _, row in company_info.iterrows():
        # 매도 주문 추가
        sell_orders.append({"company_name": row['회사명'], "code": row['종목코드'], "price": "20,550", "url": row['홈페이지']})
        

    return templates.TemplateResponse("ui-card.html", {"request": request, "sell_orders": sell_orders})

@app.post("/register", response_class=HTMLResponse)
async def register(request: Request, cano: str = Form(...), app_key: str = Form(...), app_secret: str = Form(...), id_token: str = Form(...)):
    # 입력된 값을 콘솔에 출력 (디버깅 목적)
    print(f"계좌번호: {cano}, App Key: {app_key}, App Secret: {app_secret}, ID Token: {id_token}")

    # 토큰 발급 시도
    access_token = get_access_token(app_key, app_secret)
    
    if access_token:
        # 토큰 발급 성공 시
        # 유저 정보를 JSON 파일에 저장합니다.
        print(id_token)
        id_token = base64.b64decode(id_token)

        id_token = decrypt_data(id_token)
        print(id_token)
        save_user_info_to_json(id_token, cano, app_key, app_secret)

        return templates.TemplateResponse(
            "registration_complete.html",
            {
                "request": request,
                "cano": cano,
                "app_key": app_key,
                "app_secret": app_secret,
                "success": True  # 성공 여부를 템플릿에 전달
            }
        )
    else:
        # 토큰 발급 실패 시
        return templates.TemplateResponse(
            "registration_failed.html",
            {
                "request": request,
                "cano": cano,
                "app_key": app_key,
                "app_secret": app_secret,
                "success": False  # 실패 여부를 템플릿에 전달
            }
        )

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