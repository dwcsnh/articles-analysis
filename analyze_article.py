import os
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
import re
import time 
load_dotenv()

# HEADERS = {
#     'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
# }

# requests.packages.urllib3.disable_warnings()

# all_titles = [] # Changed from all_threads to all_titles for clarity
# all_links = []
# all_dates = [] # Changed from all_dts to all_dates for clarity
# all_contents = [] # New list to store article content

# # Loop through pages to get article links
# # We will collect more than 18 links initially to ensure we have enough
# # in case some articles are problematic, and then slice to 18 later.
# # Let's aim for 2 pages to be safe, as each page has multiple articles.
# # Adjust the range if you find 2 pages don't yield enough unique articles for your needs.
# for i in range(1, 4): # Iterate through page 1 and 2
#     print(f'Getting article links from page: {i}')
#     page_url = f'https://vneconomy.vn/chung-khoan.htm?trang={i}'
#     try:
#         response = requests.get(page_url, headers=HEADERS, verify=False, timeout=10) # Added timeout
#         response.raise_for_status() # Raise an exception for bad status codes
#         soup = bs(response.content, 'html.parser')

#         threads = soup.find_all('article', class_='story story--featured story--timeline')
#         for thrd in threads:
#             title = thrd.find('h3').text.strip()
#             link = thrd.find('figure').find('a')['href']
#             date = thrd.find('header').find('time').text.strip() # Directly find time within header

#             # Ensure the link is absolute
#             if not link.startswith('http'):
#                 link = 'https://vneconomy.vn' + link

#             all_titles.append(title)
#             all_links.append(link)
#             all_dates.append(date)
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching page {i}: {e}")
#     time.sleep(1) # Add a small delay between page requests

# print(f"Found {len(all_links)} article links. Now fetching content for the first 18 unique articles.")

# # Create a DataFrame from collected links to easily manage unique links
# df_links = pd.DataFrame({
#     'date': all_dates,
#     'title': all_titles,
#     'link': all_links
# })

# # Convert date to datetime, sort, and remove duplicates to get the latest 18 unique articles
# df_links['date'] = pd.to_datetime(df_links['date'], format='%d/%m/%Y')
# df_links.sort_values(by='date', ascending=False, inplace=True) # Sort descending to get latest
# df_links.drop_duplicates(subset=['link'], inplace=True) # Remove duplicate links
# df_to_crawl = df_links.head(18) # Take the first 18 unique articles

# # Now, iterate through the selected links and fetch content
# for index, row in df_to_crawl.iterrows():
#     article_link = row['link']
#     print(f'Getting content for: {article_link}')
#     try:
#         article_response = requests.get(article_link, headers=HEADERS, verify=False, timeout=10) # Added timeout
#         article_response.raise_for_status() # Raise an exception for bad status codes
#         article_soup = bs(article_response.content, 'html.parser')

#         # Find the content using the class provided
#         content_div = article_soup.find('div', class_='detail__content')
#         if content_div:
#             # Extract text from all <p> tags within the content_div
#             paragraphs = content_div.find_all('p')
#             article_text = "\n".join([p.get_text(separator=' ', strip=True) for p in paragraphs])
#             all_contents.append(article_text)
#         else:
#             all_contents.append("Nội dung không tìm thấy")
#             print(f"Warning: Content div not found for {article_link}")

#     except requests.exceptions.RequestException as e:
#         all_contents.append(f"Lỗi khi tải nội dung: {e}")
#         print(f"Error fetching content for {article_link}: {e}")
#     time.sleep(1.5) # Add a delay between article requests to avoid overwhelming the server

# # Create the final DataFrame
# # Ensure the length of all_contents matches the number of articles we actually tried to crawl
# # If there were errors, all_contents might be shorter or have "Nội dung không tìm thấy" placeholders.
# # We'll re-create the DataFrame based on the actually crawled articles.
# final_df = pd.DataFrame({
#     'date': df_to_crawl['date'].reset_index(drop=True),
#     'title': df_to_crawl['title'].reset_index(drop=True),
#     'link': df_to_crawl['link'].reset_index(drop=True),
#     'content': all_contents # This list should now match the length of df_to_crawl
# })

# # Save to Excel
# final_df.to_csv('economy_articles.csv', index=False)
# print("Data saved to economy_articles.csv")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
    
company_dictionary = read_file("dictionary_companies.csv")
sector_dictionary = read_file("dictionary_sectors.csv")
article_content = read_file("economy_articles.csv")

class Company(BaseModel):
    company_name: str
    company_stock_id: str

class Sector(BaseModel):
    id: int
    article: str
    sector: str
    companies: list[Company]

response = client.responses.parse(
    model="gpt-4o",
    input=[
        {
            "role": "system",
            "content": """Bạn là một chuyên gia trích xuất dữ liệu có cấu trúc.

            # Nhiệm vụ
            Phân tích bài báo dựa trên 2 dictionary đã cho (ở dạng CSV). Đầu ra là một danh sách các object theo schema đã cung cấp.

            # Mô tả
            - Input là 1 file csv với các cột date, title, link, content. Mỗi dòng tương ứng với 1 bài báo
            - Đối với mỗi bài báo, chỉ ra ngành được nhắc đến chủ yếu trong danh sách các ngành được cung cấp trong Dictionary 2.
            - Tìm các công ty thuộc ngành đó được nhắc đến ở trong bài báo, đồng thời có trong dictionary 1.
            - Một ngành có thể chứa nhiều công ty.

            # Output Format
            Là 1 mảng json object, mỗi object có dạng
            {
            id: số thứ tự,
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
        },
    ],
    text_format=list[Sector],
)

# Access the structured output
research_paper = response.output_parsed

print(research_paper)
