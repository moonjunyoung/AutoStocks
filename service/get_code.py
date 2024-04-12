import asyncio
import aiohttp
import pandas as pd
import json

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

async def get_all_company_info():
    url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, url)
        code_df = pd.read_html(html, encoding='euc-kr')[0]
        code_df['종목코드'] = code_df['종목코드'].map('{:06d}'.format)
        code_df = code_df[['회사명', '종목코드','홈페이지']]
        print(code_df)
        return code_df

async def save_all_company_info_to_json():
    all_company_info = await get_all_company_info()
    all_company_info.to_json('company_info.json', orient='records')

async def get_company_info(company_name):
    company_info = load_data_from_json('company_info.json')
    desired_info = company_info[company_info['회사명'].str.contains(company_name)]
    return desired_info

def load_data_from_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return pd.DataFrame(data)

async def main():
    await save_all_company_info_to_json()

if __name__ == "__main__":
    asyncio.run(main())
