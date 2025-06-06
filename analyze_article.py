import os
import json
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup as bs
import time

load_dotenv()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
}
requests.packages.urllib3.disable_warnings()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

company_dictionary = read_file("dictionary_companies.csv")
sector_dictionary = read_file("dictionary_sectors.csv")

class Company(BaseModel):
    company_name: str
    company_stock_id: str

class Sector(BaseModel):
    id: str
    article: str
    sector: str
    companies: list[Company]

class SectorList:
    sectors: list[Sector]

class CompanyResult:
    def __init__(self, name, stockId):
        self.company_name = name
        self.company_stock_id = stockId

class SectorResult:
    def __init__(self, id, article, sector, companies):
        self.id = id
        self.article = article
        self.sector = sector
        self.companies = companies

def convert_company(c: Company) -> CompanyResult:
    return CompanyResult(name=c.company_name, stockId=c.company_stock_id)

def convert_sector(s: Sector) -> SectorResult:
    company_results = [convert_company(c) for c in s.companies]
    return SectorResult(
        id=s.id,
        article=s.article,
        sector=s.sector,
        companies=company_results
    )
        
def sector_result_to_dict(sr: SectorResult):
    return {
        "id": sr.id,
        "article": sr.article,
        "sector": sr.sector,
        "companies": [
            {
                "company_name": c.company_name,
                "company_stock_id": c.company_stock_id
            }
            for c in sr.companies
        ]
    }

# Output
results: list[SectorResult] = []

article_id = 1
for i in range(1, 4):  # Crawl 3 trang
    print(f"\n========== Crawling page {i} ==========")
    page_url = f"https://vneconomy.vn/chung-khoan.htm?trang={i}"
    try:
        response = requests.get(page_url, headers=HEADERS, verify=False, timeout=10)
        response.raise_for_status()
        soup = bs(response.content, 'html.parser')
        threads = soup.find_all('article', class_='story story--featured story--timeline')

        for thrd in threads:
            try:
                title = thrd.find('h3').text.strip()
                link = thrd.find('figure').find('a')['href']
                if not link.startswith('http'):
                    link = 'https://vneconomy.vn' + link

                article_response = requests.get(link, headers=HEADERS, verify=False, timeout=10)
                article_response.raise_for_status()
                article_soup = bs(article_response.content, 'html.parser')

                content_div = article_soup.find('div', class_='detail__content')
                if content_div:
                    paragraphs = content_div.find_all('p')
                    content_text = "\n".join([p.get_text(separator=' ', strip=True) for p in paragraphs])
                else:
                    content_text = "Nội dung không tìm thấy"

                print(f"📄 Đang phân tích bài báo: {title[:50]}...")

                article_content = f"id,title,content\n{article_id},{title},{content_text}"

                # Gọi OpenAI để phân tích
                response = client.responses.parse(
                    model="gpt-4o",
                    input=[
                        {
                            "role": "system",
                            "content": """Bạn là một chuyên gia trích xuất dữ liệu có cấu trúc.

                            # Nhiệm vụ
                            Phân tích bài báo dựa trên 2 dictionary đã cho (ở dạng CSV). Đầu ra là một danh sách các object theo schema đã cung cấp.

                            # Input Format
                            Là 1 file csv với các cột: id, title, content, tương ứng với id, tiêu đề và nội dung bài báo

                            # Mô tả
                            - Chỉ ra ngành được nhắc đến chủ yếu trong danh sách các ngành được cung cấp trong Dictionary 2.
                            - Tìm các công ty thuộc ngành đó được nhắc đến ở trong bài báo, đồng thời có trong dictionary 1.
                            - Một ngành có thể chứa nhiều công ty.

                            # Output Format
                            Là 1 json object, có dạng
                            {
                            id: tương ứng với id của input
                            article: tên bài báo,
                            sector: tên ngành,
                            companies: [
                                { 
                                    company_name: tên công ty, 
                                    company_stock_id: mã cổ phiếu
                                }
                            ]
                            }
                            """
                        },
                        {
                            "role": "user",
                            "content": f"""# Dictionary 1 (STT,Mã cp,Tên chính thức,Ngành,Từ khóa)
                            {company_dictionary}

                            # Dictionary 2 (STT,Ngành)
                            {sector_dictionary}

                            # Bài báo
                            {article_content}
                            """
                        }
                    ],
                    text_format=Sector,
                )

                results.append(convert_sector(response.output_parsed))
                print(f"✅ Phân tích xong bài báo {article_id}")
                print(f"✅ Output: {response.output_parsed}")
                article_id += 1
                time.sleep(1.5)

            except Exception as e:
                print(f"❌ Lỗi xử lý bài báo: {e}")
                continue

    except Exception as e:
        print(f"❌ Lỗi xử lý trang {i}: {e}")

results_as_dict = [sector_result_to_dict(sr) for sr in results]

with open('sectors_output.json', 'w', encoding='utf-8') as f:
    json.dump(results_as_dict, f, ensure_ascii=False, indent=4)
