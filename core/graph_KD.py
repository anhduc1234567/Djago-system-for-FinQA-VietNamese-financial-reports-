from sentence_transformers import SentenceTransformer, util
import json
import json
from collections import defaultdict
import unicodedata
from sentence_transformers import SentenceTransformer
import re
from core.graph_db import add_new_report
from core.call_api_llm import call_api_gemi

# from graph_db import add_new_report
# from call_api_llm import call_api_gemi
 #https://aistudio.google.com/apikey truy cập để lấy API
from dotenv import load_dotenv
import os
load_dotenv()

DEVICE = os.getenv("DEVICE")
names = [
    "BÁO CÁO CỦA BAN GIÁM ĐỐC",
    "BÁO CÁO SOÁT XÉT",
    "BÁO CÁO KIỂM TOÁN",
    
    "BÁO CÁO TÌNH HÌNH TÀI CHÍNH",
    "BẢNG CÂN ĐỐI KẾ TOÁN",
    "CÁC CHỈ TIÊU NGOÀI BÁO CÁO TÌNH HÌNH TÀI CHÍNH",
    
    "BÁO CÁO KẾT QUẢ HOẠT ĐỘNG KINH DOANH",
    "BÁO CÁO KẾT QUẢ HOẠT ĐỘNG",
    "BÁO CÁO KẾT QUẢ KINH DOANH",
    
    "BÁO CÁO LƯU CHUYỂN TIỀN TỆ",
    
    "THUYẾT MINH BÁO CÁO TÀI CHÍNH",
    
    "BÁO CÁO TÌNH HÌNH BIẾN ĐỘNG VỐN CHỦ SỞ HỮU"
]

subtitles_of_balance_sheet = [
    "TÀI SẢN NGẮN HẠN",
    "TÀI SẢN DÀI HẠN",
    "NỢ PHẢI TRẢ",
    "VỐN CHỦ SỞ HỮU"
]

subtitles_of_cash_flow = [
    "LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG KINH DOANH",
    "LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG ĐẦU TƯ",
    "LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG TÀI CHÍNH",
    
    "LƯU CHUYỂN TIỀN THUẦN TỪ HOẠT ĐỘNG KINH DOANH",
    "LƯU CHUYỂN TIỀN THUẦN TỪ HOẠT ĐỘNG ĐẦU TƯ",
    "LƯU CHUYỂN TIỀN THUẦN TỪ HOẠT ĐỘNG TÀI CHÍNH",
    
    "LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG SẢN XUẤT",
    "LƯU CHUYỂN TIỀN TỆ TỪ HOẠT ĐỘNG SXKD",
]

subtitles_of_income_statement= [
    "DOANH THU BÁN HÀNG",
    "DOANH THU CUNG CẤP DỊCH VỤ",
    "TỔNG DOANH THU",
    
    "DOANH THU HOẠT ĐỘNG TÀI CHÍNH",
    
    "THU NHẬP KHÁC"
    
    # "LỢI NHUẬN KẾT TOÁN TRƯỚC THUẾ"
]

subtitles_of_income_statement_for_bank= [
    "THU NHẬP LÃI VÀ CÁC KHOẢN",
    
    "THU NHẬP TỪ HOẠT ĐỘNG KHÁC",
    
    "CHI PHÍ THUẾ"
]
subtitles_of_balance_sheet_for_bank = [
    "TÀI SẢN",
    "TÀI SẢN CỐ ĐỊNH",
    "NỢ PHẢI TRẢ",
    "VỐN CHỦ SỞ HỮU",
    "CHỈ TIÊU NGOÀI"
]

subtitles_of_balance_sheet_for_index = [
    "TÀI SẢN NGẮN HẠN",
    
    "TÀI SẢN DÀI HẠN",
    
    "NỢ PHẢI TRẢ",
    
    "VỐN CHỦ SỞ HỮU",
    
    "TÀI SẢN CỦA CÔNG TY CHỨNG KHOÁN",
    
    "TÀI SẢN VÀ CÁC KHOẢN PHẢI TRẢ"
]

subtitles_of_income_statement_for_index = [
  "DOANH THU HOẠT ĐỘNG",
  
  "CHI PHÍ HOẠT ĐỘNG",
  
  "DOANH THU HOẠT ĐỘNG TÀI CHÍNH",
  
  "CHI PHÍ TÀI CHÍNH",
  
  "THU NHẬP KHÁC"
]

subtitles_of_cash_flow_for_index = [
    "LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG KINH DOANH",
    "LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG ĐẦU TƯ",
    "LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG TÀI CHÍNH",
    
    "LƯU CHUYỂN TIỀN THUẦN TỪ HOẠT ĐỘNG KINH DOANH",
    "LƯU CHUYỂN TIỀN THUẦN TỪ HOẠT ĐỘNG ĐẦU TƯ",
    "LƯU CHUYỂN TIỀN THUẦN TỪ HOẠT ĐỘNG TÀI CHÍNH",
    
    "PHẦN LƯU CHUYỂN TIỀN TỆ HOẠT ĐỘNG MÔI GIỚI"
]

def clean_text(text: str) -> str:
    text = text.replace("\n", " ").replace("\t", " ")
    text = re.sub(r"[^a-zA-Z0-9À-ỹ\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

model = SentenceTransformer("bkai-foundation-models/vietnamese-bi-encoder",device=DEVICE)
def remove_accents(text):
    if not text:
        return ""

    # 1. Loại bỏ tag HTML <br>, </br>, <br/>
    text = re.sub(r"</?br\s*/?>", " ", text, flags=re.IGNORECASE)

    # 2. Loại bỏ ký tự không phải chữ, số, dấu tiếng Việt, khoảng trắng, dấu câu cơ bản
    # Giữ lại: chữ, số, khoảng trắng, ., ,, :, ;, -, / 
    text = re.sub(r"[^0-9A-Za-zÀ-ỹ.,:;\/\-\s]", " ", text)

    # 3. Chuẩn hóa Unicode (tránh lỗi dấu)
    text = unicodedata.normalize("NFC", text)

    # 4. Xóa nhiều khoảng trắng → 1 khoảng trắng
    text = re.sub(r"\s+", " ", text)

    # 5. Trim hai đầu
    text = text.strip()

    return text
    # text = unicodedata.normalize('NFD', text)
    # return ''.join(c for c in text if unicodedata.category(c) != 'Mn')

def embedding_similarity(sent1: str, sent2: str) -> float:
    emb1 = model.encode(sent1)
    emb2 = model.encode(sent2)
    similarity = util.cos_sim(emb1, emb2)
    return float(similarity.item())

def find_max_simlar(sentance, labels):
    max = 0
    most_similar_label = labels[0]
    for l in labels:
        temp = embedding_similarity(sentance, l)
        if l in sentance:
            temp += 0.25
        if temp > max:
            max = temp
            most_similar_label = l
    return max, most_similar_label

def label_page(lines,labels, num_page, type_report):
    most_similar_label = ''
    max = 0
    line_max = ''
    
    for l in lines:
        l = clean_text(l)
        # is_label_in_line = find_label_page(l, labels)
        if l.strip().upper() == type_report.strip().upper() and num_page != 0:
            continue
        temp_max, temp_most_similar_label = find_max_simlar(l.strip().upper(), labels)
        if temp_max > max:
            max = temp_max
            most_similar_label = temp_most_similar_label
            line_max = l
    print(max, num_page, most_similar_label,"--", line_max, len(line_max))
    
    if len(line_max) > 180:
        most_similar_label = "None"
    
    if num_page == 0 and max < 0.9:
        most_similar_label = "None"
    if max < 0.67 and 1 < num_page + 1 < 6 :
        most_similar_label = "None"
    elif max < 0.57:
        most_similar_label = "None"
            
    return most_similar_label

def find_label_page(l, labels):
    for label in labels:
        if label.strip().upper() in l.strip().upper():
            return True
    return False

def find_name_company(page):
    lines = page.splitlines()
    for line in lines:
        if len(line) != 0 :
            return " ".join(line.split())


def get_name_report_and_times(pages1):
    prompt = f"""
        Hãy dựa vào thông tin sau của báo cáo tài chính này hãy trả lời cho tôi:
        Tên doanh nghiệp là gì, tên báo cáo chung là gì, Báo cáo ở thời điểm nào, Doanh nghiệp thuộc lĩnh vực nào. 
        Thông tin trang đầu:{pages1}
        - Hãy trả về các thông tin tôi cần trực tiếp và cách nhau bởi dấu phẩy, thứ tự như tôi đã yêu đâu ở trên.
        - Chú ý lĩnh vực của doanh nghiệp phải nằm 1 trong 11 lĩnh vực sau:
        1. Năng lượng
        2. Nguyên vật liệu
        3. Công nghiệp
        4. Hàng tiêu dùng thiết yếu
        5. Hàng tiêu dùng không thiết yếu
        6. Y tế
        7. Chứng khoán
        8. Công nghệ thông tin
        9. Viễn thông và Truyền thông
        10. Hạ tầng tiện ích 
        11. Bất động sản
        12. Ngân hàng
        - Thời điểm báo cáo phải nằm trong 6 thời điểm sau hãy trả về tên gọi đơn giản nhất ví dụ Quý 1 [năm]:
            - Quý 1 [năm]   (Cho kỳ 3 tháng (01/01 - 31/03))
            - Quý 2  [năm]   (Cho kỳ 3 tháng (01/04 - 30/06))
            - Bán niên  [năm] (Cho kỳ 6 tháng (01/01 - 30/06))
            - Quý 3   [năm]  (Cho kỳ 3 tháng (01/07 - 30/09))
            - Quý 4  [năm]   (Cho kỳ 3 tháng (01/10 - 31/12))
            - Năm   [năm]    (Cho kỳ 12 tháng (01/01 - 31/12))
        Không giải thích mở đầu trả lời thẳng luôn (Hãy sửa lại chính tả theo ngôn ngữ Tiếng Việt nếu cần)
    """
    response = call_api_gemi(prompt)
    return [x.strip() for x in response.split(",") if x.strip()]

def build_json(pages, names, is_Built = False):
    data = []
    doc_to_find_infor = ''
    for i in range(0, 8):
        doc_to_find_infor += pages[i] + '\n'
    infor_report = get_name_report_and_times(doc_to_find_infor)
    if is_Built is True:
        print(infor_report)
        return data, infor_report
    print(infor_report)
    company_data = {
        "company_name": infor_report[0],
        "type_report":  infor_report[1],
        "times": infor_report[2],
        "sector": infor_report[3],
        "pages": []
    }
    current_title = "Giới thiệu"
    for i, page in enumerate(pages):
        lines = [l for l in page.splitlines() if l.strip() != ""]
        # Lấy title từ label_page (ví dụ bạn đã có sẵn hàm)
        if current_title != "THUYẾT MINH BÁO CÁO TÀI CHÍNH":  
            title = label_page(lines[:10],names, i , infor_report[1])
            current_title = title
        else:
            title = "THUYẾT MINH BÁO CÁO TÀI CHÍNH"
            

        if title == "BÁO CÁO CỦA BAN GIÁM ĐỐC" or title == "BÁO CÁO SOÁT XÉT" or title ==  "BÁO CÁO KIỂM TOÁN":
            title = "Giới thiệu"
    
        if title == "BÁO CÁO TÌNH HÌNH TÀI CHÍNH" or title == "CÁC CHỈ TIÊU NGOÀI BÁO CÁO TÌNH HÌNH TÀI CHÍNH":
            title = "BẢNG CÂN ĐỐI KẾ TOÁN"
            
        if title == "BÁO CÁO KẾT QUẢ KINH DOANH" or title == "BÁO CÁO KẾT QUẢ HOẠT ĐỘNG":
            title = "BÁO CÁO KẾT QUẢ HOẠT ĐỘNG KINH DOANH"

        content = "\n".join(lines)

        company_data["pages"].append({
            "number": i + 1,   # đánh số trang từ 1
            "title": title,
            "content": content + f'\n Trang {i + 1}'
        })
     

    data.append(company_data)
    
    return data, infor_report


def merge_between_introductions(sections, target_title="Giới thiệu"):
    # chuẩn hóa tiêu đề để so sánh
    titles = [sec["title"].strip().upper() for sec in sections]

    try:
        first_idx = titles.index(target_title.upper())
        last_idx = len(titles) - 1 - titles[::-1].index(target_title.upper())
        if first_idx != 0:
            first_idx = 0
        print(first_idx, last_idx)
    except ValueError:
        # nếu không có "Giới thiệu" -> trả nguyên
        return sections

    if first_idx == last_idx:
        # chỉ có 1 giới thiệu -> giữ nguyên
        return sections

    # gom tất cả sections trong khoảng [first_idx, last_idx]
    merged_pages = []
    merged_content = []
    for i in range(first_idx, last_idx + 1):
        merged_pages.extend(sections[i]["pages"])
        merged_content.append(sections[i]["content"])

    merged_section = {
        "title": target_title,
        "pages": sorted(list(set(merged_pages))),
        "content": "\n".join(merged_content)
    }

    # giữ lại các section ngoài khoảng này
    new_sections = sections[:first_idx] + [merged_section] + sections[last_idx+1:]

    return new_sections

def merge_section(data):
    pages = data[0]["pages"]

    sections = []
    current_section = None

    for page in pages:
        title = page["title"].strip()
        content = page["content"].strip()

        # Nếu title là "none" thì coi như tiếp tục section hiện tại
        if title.lower() == "none" and current_section:
            current_section["pages"].append(page["number"])
            current_section["content"] += "\n" + content
            continue

        if current_section is None:
            # Bắt đầu section đầu tiên
            current_section = {"title": title, "pages": [page["number"]], "content": content}
        else:
            # Nếu gặp title mới khác "none" và khác title hiện tại → đóng section cũ, mở section mới
            if title != current_section["title"]:
                sections.append(current_section)
                current_section = {"title": title, "pages": [page["number"]], "content": content}
            else:
                # Nếu title giống section hiện tại thì gộp thêm nội dung
                current_section["pages"].append(page["number"])
                current_section["content"] += "\n" + content

    # Thêm section cuối cùng
    if current_section:
        sections.append(current_section)
    # sections = merge_between_introductions(sections)
    # Xuất ra JSON mới (có metadata gốc)
    grouped_report = {
        "company_name": data[0]["company_name"],
        "type_report": data[0]["type_report"],
        "times": data[0]["times"],
        "sector": data[0]["sector"],
        "sections": sections
    }

    with open("graph_json/report_grouped.json", "w", encoding="utf-8") as f:
        json.dump(grouped_report, f, ensure_ascii=False, indent=4)

    print("✅ Đã tạo file report_grouped.json")
    
def split_balance_content(content, subtitles):
    lines = content.splitlines()
    subsections = []
    current_sub = None
    used = set()
    table_structure = None   # chứa 5 dòng trước subtitle đầu tiên

    first_sub_index = None

    for i, line in enumerate(lines):
        clean_line = line.strip().upper()
 
        # Kiểm tra subtitle mới
        matched_subs = [sub for sub in subtitles if remove_accents(sub) in remove_accents(clean_line) and sub not in used]
        if matched_subs:
            # lưu index của subtitle đầu tiên
            if first_sub_index is None:
                first_sub_index = i

            # nếu có section hiện tại thì lưu lại
            if current_sub:
                subsections.append(current_sub)

            matched_sub = matched_subs[0]
            used.add(matched_sub)
            if matched_sub == "DOANH THU BÁN HÀNG" or matched_sub == "TỔNG DOANH THU" or  matched_sub == "DOANH THU CUNG CẤP DỊCH VỤ":
                current_sub = {"subtitle": "DOANH THU BÁN HÀNG VÀ CUNG CẤP DỊCH VỤ", "raw_text": line}
         
            elif matched_sub == "LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG SẢN XUẤT" or matched_sub == "LƯU CHUYỂN TIỀN TỆ TỪ HOẠT ĐỘNG SXKD":
                current_sub = {"subtitle": "LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG KINH DOANH", "raw_text": line} 
                
            else:
                current_sub = {"subtitle": matched_sub, "raw_text": line}
        else:
            # gộp nội dung vào section hiện tại
            if current_sub:
                current_sub["raw_text"] += "\n" + line

    # lưu section cuối cùng
    if current_sub:
        subsections.append(current_sub)

    # tạo table_structure: lấy 5 dòng trước subtitle đầu tiên
    if first_sub_index is not None:
        start = max(0, first_sub_index - 5)
        table_structure = "\n".join(lines[start:first_sub_index])

    return {
        "subsections": subsections,
        "table_structure": table_structure
    }
    
def normalize_report(report):
    sections_out = []
    for sec in report["sections"]:
        title = sec["title"].upper()
        if title == "None":
            title = "Giới thiệu"
        content = sec["content"]

        if title.startswith("Giới thiệu") or title.startswith("THUYẾT MINH"):
            sections_out.append({
                "title": sec["title"],
                "pages":sec["pages"],
                "raw_text": content
            })
        elif "CÂN ĐỐI KẾ TOÁN" in title:
            if report['sector'] == 'Ngân hàng':
                sections_out.append({
                "title": sec["title"],
                "pages":sec["pages"],
                "subsections": split_balance_content(content, subtitles_of_balance_sheet_for_bank)["subsections"],
                "table_structure": split_balance_content(content, subtitles_of_balance_sheet_for_bank)["table_structure"]
            })
            elif report['sector'] == 'Chứng khoán':
                sections_out.append({
                "title": sec["title"],
                "pages":sec["pages"],
                "subsections": split_balance_content(content, subtitles_of_balance_sheet_for_index)["subsections"],
                "table_structure": split_balance_content(content, subtitles_of_balance_sheet_for_index)["table_structure"]
            })
            else:
                sections_out.append({
                    "title": sec["title"],
                     "pages":sec["pages"],
                    "subsections": split_balance_content(content, subtitles_of_balance_sheet)["subsections"],
                    "table_structure": split_balance_content(content, subtitles_of_balance_sheet)["table_structure"]
                })
        elif "KẾT QUẢ" in title:
            if report['sector'] == "Ngân hàng":
                sections_out.append({
                "title": sec["title"],
                "pages":sec["pages"],
                "subsections": split_balance_content(content, subtitles_of_income_statement_for_bank)["subsections"],
                "table_structure": split_balance_content(content, subtitles_of_income_statement_for_bank)["table_structure"]
            })
            elif report['sector'] == "Chứng khoán":
                sections_out.append({
                "title": sec["title"],
                "pages":sec["pages"],
                "subsections": split_balance_content(content, subtitles_of_income_statement_for_index)["subsections"],
                "table_structure": split_balance_content(content, subtitles_of_income_statement_for_index)["table_structure"]
            })
            else:
                sections_out.append({
                    "title": sec["title"],
                    "pages":sec["pages"],
                    "subsections": split_balance_content(content, subtitles_of_income_statement)["subsections"],
                    "table_structure": split_balance_content(content, subtitles_of_income_statement)["table_structure"]
                })
        elif "LƯU CHUYỂN TIỀN" in title:
            if report['sector'] == "Chứng khoán":
                sections_out.append({
                "title": sec["title"],
                "pages":sec["pages"],
                "subsections": split_balance_content(content, subtitles_of_cash_flow_for_index)["subsections"],
                "table_structure": split_balance_content(content, subtitles_of_cash_flow_for_index)["table_structure"]
            })
            else:
                sections_out.append({
                    "title": sec["title"],
                    "pages":sec["pages"],
                    "subsections": split_balance_content(content, subtitles_of_cash_flow)["subsections"],
                    "table_structure": split_balance_content(content, subtitles_of_cash_flow)["table_structure"]
                })
        else:
            sections_out.append({
                "title": sec["title"],
                "pages":sec["pages"],
                "raw_text": content
            })

    return {
        "report": {
            "company": report["company_name"],
            "type":  report["type_report"],
            "times": report["times"],
            "sector": report["sector"],
            "sections": sections_out
        }
    }
def normalize_subtitle(name: str) -> str:
    name = name.upper()
    if "LƯU CHUYỂN TIỀN THUẦN TỪ HOẠT ĐỘNG KINH DOANH" in name:
        return "LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG KINH DOANH"
    elif "LƯU CHUYỂN TIỀN THUẦN TỪ HOẠT ĐỘNG ĐẦU TƯ" in name:
        return "LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG ĐẦU TƯ"
    elif "LƯU CHUYỂN TIỀN THUẦN TỪ HOẠT ĐỘNG TÀI CHÍNH" in name:
        return "LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG TÀI CHÍNH"
    return name.strip()

def normalize_report_final(data):
    report = data.get("report", {})
    sections = report.get("sections", [])

    normalized_sections = []
    intro_merged = {
        "title": "Giới thiệu",
        "pages": [],
        "raw_text": ""
    }
    biendongvonchusohuu_merged = {
        "title": "BÁO CÁO TÌNH HÌNH BIẾN ĐỘNG VỐN CHỦ SỞ HỮU",
        "pages": [],
        "raw_text": ""
    }

    for sec in sections:
        # Bỏ qua nếu không có raw_text hoặc rỗng
        if "raw_text" in sec and (sec["raw_text"] is None or sec["raw_text"].strip() == ""):
            continue

        # Nếu title là None thì gán thành "Giới thiệu"
        if sec.get("title") == "None":
            sec["title"] = "Giới thiệu"

        # ✅ Gom tất cả section có title "Giới thiệu"
        if sec.get("title") == "Giới thiệu":
            intro_merged["pages"].extend(sec.get("pages", []))
            intro_merged["raw_text"] += ("\n" + sec.get("raw_text", "").strip())
            continue  # Không thêm ngay, sẽ thêm sau khi duyệt hết
        if sec.get("title") == "BÁO CÁO TÌNH HÌNH BIẾN ĐỘNG VỐN CHỦ SỞ HỮU":
            biendongvonchusohuu_merged["pages"].extend(sec.get("pages", []))
            biendongvonchusohuu_merged["raw_text"] += ("\n" + sec.get("raw_text", "").strip())
            continue  # Không thêm ngay, sẽ thêm sau khi duyệt hết
        
        # Giữ nguyên xử lý subsections gốc
        if "subsections" in sec:
            merged = defaultdict(list)
            for sub in sec["subsections"]:
                subtitle = sub.get("subtitle", "").strip()
                raw_text = sub.get("raw_text", "").strip()
                if raw_text:
                    key = normalize_subtitle(subtitle)
                    merged[key].append(raw_text)
            new_subsections = []
            for subtitle, texts in merged.items():
                new_subsections.append({
                    "subtitle": subtitle,
                    "raw_text": "\n".join(texts)
                })

            sec["subsections"] = new_subsections

        if "subsections" in sec and not sec["subsections"]:
            continue

        normalized_sections.append(sec)

    # ✅ Sau khi duyệt xong, nếu có phần giới thiệu thì thêm vào đầu danh sách
    if intro_merged["raw_text"].strip():
        intro_merged["pages"] = sorted(set(intro_merged["pages"]))
        normalized_sections.insert(0, intro_merged)
        
    if biendongvonchusohuu_merged["raw_text"].strip():
        normalized_sections.insert(3, biendongvonchusohuu_merged)
    
    
    report["sections"] = normalized_sections
    data["report"] = report
    return data

def add_new_data(file_path = None, is_build = False):
    pages = []
    with open(file_path, "r", encoding="utf-8") as f:
        current_page = []
        for line in f:
            # Nếu gặp dòng đánh dấu page
            if line.strip().startswith("-----------Page"):
                if current_page:  # nếu current_page có dữ liệu, thêm vào pages
                    pages.append("".join(current_page))
                    current_page = []
            else:
                current_page.append(line)
        
        # Thêm page cuối cùng nếu có
        if current_page:
            pages.append("".join(current_page))
    
    if is_build is True:
        print('Báo cáo này đã có đồ thị')
        json_data, infor = build_json(pages, names, is_Built= True)
        return infor
    json_data, infor = build_json(pages, names, is_Built= False)
    
    merge_section(json_data)
    with open("graph_json/report_grouped.json", "r", encoding="utf-8") as f:
        grouped_report = json.load(f)
    normalized = normalize_report(grouped_report)
    normalized = normalize_report_final(normalized)
    with open("graph_json/report_normalized.json", "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=4)
    add_new_report(normalized)
    print("✅ Đã tạo file report_normalized.json")
    return infor

# pages = []
# file_path = "reports_test/20250830 - BBC - BCTC HOP NHAT BAN NIEN 2025.md"
# with open(file_path, "r", encoding="utf-8") as f:
#     current_page = []
#     for line in f:
#         # Nếu gặp dòng đánh dấu page
#         if line.strip().startswith("-----------Page"):
#             if current_page:  # nếu current_page có dữ liệu, thêm vào pages
#                 pages.append("".join(current_page))
#                 current_page = []
#         else:
#             current_page.append(line)
    
#     # Thêm page cuối cùng nếu có
#     if current_page:
#         pages.append("".join(current_page))
# json_data = build_json(pages, names)
    
# merge_section(json_data)
    

# with open("report_grouped.json", "r", encoding="utf-8") as f:
#     grouped_report = json.load(f)
# normalized = normalize_report(grouped_report)
# normalized = normalize_report_final(normalized)
# with open("report_normalized.json", "w", encoding="utf-8") as f:
#     json.dump(normalized, f, ensure_ascii=False, indent=4)

# print("✅ Đã tạo file report_normalized.json")
