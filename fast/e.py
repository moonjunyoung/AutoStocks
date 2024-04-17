import requests


def get_uuid(access_token):
    # 액세스 토큰을 설정하십시오.
    access_token = "F7DTCkZINPTvVa2uuhwa599F01_DwJ_BY9kKKiUNAAABjucsFxlSGUcvaFb1Eg"

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