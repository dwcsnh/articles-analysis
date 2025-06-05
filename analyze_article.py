import os
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
    
company_dictionary = read_file("dictionary_companies.csv")
sector_dictionary = read_file("dictionary_sectors.csv")
article_content = read_file("article.txt")

class Company(BaseModel):
    company_name: str
    company_stock_id: str

class Sector(BaseModel):
    id: int
    sector: str
    companies: list[Company]

class ResearchPaperExtraction(BaseModel):
    sector: str
    company: str
    stock_id: str

response = client.responses.parse(
    model="gpt-4o",
    input=[
        {
            "role": "system",
            "content": """Bạn là một chuyên gia trích xuất dữ liệu có cấu trúc.

            # Nhiệm vụ
            Phân tích bài báo dựa trên 2 dictionary đã cho (ở dạng CSV). Đầu ra là một danh sách các object theo schema đã cung cấp.

            # Mô tả
            - Chỉ ra bài báo chủ yếu nhắc đến ngành nào trong Dictionary 2.
            - Tìm các công ty thuộc ngành đó được nhắc đến ở trong bài báo, đồng thời có trong dictionary 1.
            - Một ngành có thể chứa nhiều công ty.

            # Output Format
            Mỗi phần tử là một object:
            {
            id: số thứ tự,
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
        },
    ],
    text_format=Sector,
)

# Access the structured output
research_paper = response.output_parsed

print(research_paper)
