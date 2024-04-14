import json
import requests
from service.common.repository import User, get_session
from dotenv import load_dotenv
import os
from sqlalchemy.orm import Session

load_dotenv()
kakao_cilent_id = os.environ.get("KAKAO_CLIENT_ID")
kakao_redirect_url = os.environ.get("KAKAO_REDIRECT_URL")
naver_client_id = os.environ.get("NAVER_CLIENT_ID")
naver_client_secret = os.environ.get("NAVER_CLIENT_SECRET")


class UserService:
    def __init__(self) -> None:
        self.session: Session = get_session()

    def oauth_login(self, platform, oauth_token):
        if platform == "naver":
            platform_id = self.__get_user_platform_id_by_naver_oauth(oauth_token)
        elif platform == "kakao":
            platform_id = self.__get_user_platform_id_by_kakao_oauth(oauth_token)

        existing_user = (
            self.session.query(User)
            .filter(platform == platform, platform_id == platform_id)
            .first()
        )
        if existing_user:
            return existing_user

        user = User(id=None, platform=platform, platform_id=platform_id)
        self.session.add(user)
        self.session.commit()
        return user

    def __get_user_platform_id_by_kakao_oauth(token):
        def __get_user_access_token_by_kakao_oauth(token):
            data = {
                "grant_type": "authorization_code",
                "client_id": kakao_cilent_id,
                "redirect_uri": kakao_redirect_url,
                "code": token,
            }
            kakao_token_data = json.loads(
                requests.post(
                    url=f"https://kauth.kakao.com/oauth/token", data=data
                ).text
            )
            access_token = kakao_token_data.get("access_token")
            return access_token

        access_token = __get_user_access_token_by_kakao_oauth(token)
        headers = {"Authorization": f"Bearer {access_token}"}
        kakao_user_data = json.loads(
            requests.get(url="https://kapi.kakao.com/v2/user/me", headers=headers).text
        )
        platform_id = kakao_user_data.get("id")
        if platform_id:
            return platform_id
        else:
            raise Exception("잘못된 Oauth")

    def __get_user_platform_id_by_naver_oauth(token):
        def __get_user_access_token_by_naver_oauth(token):
            naver_token_data = json.loads(
                requests.post(
                    url=f"https://nid.naver.com/oauth2.0/token?grant_type=authorization_code&client_id={naver_client_id}&client_secret={naver_client_secret}&code={token}&state=null"
                ).text
            )
            access_token = naver_token_data.get("access_token")
            return access_token

        access_token = __get_user_access_token_by_naver_oauth(token)
        headers = {"Authorization": f"Bearer {access_token}"}
        naver_user_data = json.loads(
            requests.get(
                url="https://openapi.naver.com/v1/nid/me", headers=headers
            ).text
        )
        platform_id = naver_user_data.get("response").get("id")
        if platform_id:
            return platform_id
        else:
            raise Exception("잘못된 Oauth")
