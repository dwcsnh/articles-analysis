import pandas as pd
from rapidfuzz import fuzz
import csv
import os

# ========== 1. Đọc và chuẩn hóa dữ liệu ==========

def clean_column_names(df):
    df.columns = df.columns.str.strip().str.replace(" ", "_")
    return df

def load_company_dictionary(path):
    df = pd.read_csv(path)
    df = clean_column_names(df)
    df['Từ_khóa'] = df['Từ_khóa'].fillna("").apply(lambda x: [kw.strip().lower() for kw in x.split(",") if kw.strip()])
    df['Tên_công_ty'] = df['Tên_chính_thức'].str.lower()
    return df.to_dict(orient="records")

def load_sector_dictionary(path):
    df = pd.read_csv(path)
    df = clean_column_names(df)
    sector_dict = {}
    for _, row in df.iterrows():
        sector = row['Ngành'].strip()
        keywords = [kw.strip().lower() for kw in row['Từ_khóa'].split(",") if kw.strip()]
        sector_dict[sector] = keywords
    return sector_dict

# ========== 2. So khớp mờ ==========

def is_similar(text1, text2, threshold=85):
    return fuzz.partial_ratio(text1.lower(), text2.lower()) >= threshold

# ========== 3. Phân tích bài báo ==========

def analyze_article_fuzzy(article_text, company_dict, sector_dict, threshold=85):
    article_lower = article_text.lower()
    results = []
    stt = 1

    for company in company_dict:
        matched = False
        # So khớp tên công ty
        if is_similar(article_lower, company['Tên_công_ty'], threshold):
            matched = True
        # So khớp từng từ khóa công ty
        if not matched:
            for kw in company['Từ_khóa']:
                if is_similar(article_lower, kw, threshold):
                    matched = True
                    break
        if matched:
            results.append({
                "STT": stt,
                "Tên công ty": company['Tên_chính_thức'],
                "Mã cổ phiếu": company['Mã_cp'],
                "Tên ngành": company['Ngành']
            })
            stt += 1

    # Nếu không tìm thấy công ty nào, kiểm tra ngành
    if not results:
        for sector, keywords in sector_dict.items():
            for kw in keywords:
                if is_similar(article_lower, kw, threshold):
                    results.append({
                        "STT": stt,
                        "Tên công ty": "",
                        "Mã cổ phiếu": "",
                        "Tên ngành": sector
                    })
                    stt += 1
                    break
    return results

# ========== 4. Ghi kết quả ra file CSV ==========

def save_results_to_csv(results, output_path="output_analysis.csv"):
    if not results:
        print("Không tìm thấy công ty hoặc ngành.")
        return
    keys = results[0].keys()
    with open(output_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)
    print(f"✅ Kết quả đã lưu vào: {output_path}")

# ========== 5. Đọc bài báo từ file TXT ==========

def read_article_from_txt(path):
    if not os.path.exists(path):
        print(f"❌ Không tìm thấy file bài báo: {path}")
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# ========== 6. Chạy chương trình ==========

if __name__ == "__main__":
    # Đường dẫn file
    company_csv = "dictionary_companies.csv"
    sector_csv = "dictionary_sectors.csv"
    article_txt = "article.txt"  # <-- Đặt tên file văn bản bài báo ở đây

    # Đọc dữ liệu
    article = read_article_from_txt(article_txt)
    company_dict = load_company_dictionary(company_csv)
    sector_dict = load_sector_dictionary(sector_csv)

    # Phân tích và lưu
    results = analyze_article_fuzzy(article, company_dict, sector_dict)
    save_results_to_csv(results)
