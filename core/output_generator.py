from core.receiver import find_information, retrieve, remove_same_content, find_information_by_graph
from core.call_api_llm import call_api_gemi
from core.generate_summary import summary_section


# from receiver import find_information, retrieve, remove_same_content, find_information_by_graph
# from call_api_llm import call_api_gemi
# from generate_summary import summary_section
from huggingface_hub import InferenceClient
from google import genai
import os
import json
import re
import markdown
from openai import OpenAI
import bleach
from django.utils.safestring import mark_safe
from typing import List


 #https://aistudio.google.com/apikey truy cập để lấy API
# client = genai.Client(api_key= GOOGLE_API)

ALLOWED_TAGS = [
    'p', 'ul', 'ol', 'li', 'strong', 'em', 'h1', 'h2', 'h3',
    'table', 'thead', 'tbody', 'tr', 'th', 'td', 'br'
]
ALLOWED_ATTRS = {'*': ['class', 'style']}
#get user question and similar information -> create a prompt for LLM
# os.environ["GEMINI_API_KEY"] = GOOGLE_API
SYSTEM_PROMPT = "Hãy tưởng tượng bạn là một chuyên gia trong lĩnh vực tài chính \
        hãy trả lời chính xác và đưa ra dẫn chứng cho câu hỏi [user_question] [] \
            .....\
         nếu những thông tin vừa rồi không liên quan đến câu hỏi không cố trả lời hãy trả về không có thông tin cho câu hỏi \
        "
def get_user_prompt_docx(user_question, similar_infos: list[dict]):
    user_prompt = 'Từ các thông tin sau:\n'
    for similar_info in similar_infos:
        user_prompt += f"Tiêu đề: {similar_info['title']}\nNội dung: {similar_info['text']}\n"
    user_prompt += 'Hãy trả lời câu hỏi:\n'
    user_prompt += user_question
    return user_prompt

def get_user_prompt_csv(user_question, similar_infos: list[dict]):
    user_prompt = 'Từ các thông tin sau:\n'
    for similar_info in similar_infos:
        user_prompt += f"Hạng mục: {similar_info['Hạng mục']}\nMã số: {similar_info['Mã số']}\nGiá trị: {similar_info['Giá trị']}\n"
    user_prompt += 'Hãy trả lời câu hỏi:\n'
    user_prompt += user_question
    return user_prompt

def get_user_prompt_md(user_question, similar_infos: list[dict]):
    user_prompt = 'Dựa vào những thông tin sau: \n'
    for similar_info in similar_infos:
        user_prompt += f"Trang: {similar_info['Page']}\nNội dung: {similar_info['content']}\n"
    # user_prompt += 'Hãy trả lời câu hỏi:\n'

    final_prompt = f"""Hãy tưởng tượng bạn là một chuyên gia trong lĩnh vực tài chính \
        hãy trả lời chính xác và đưa ra dẫn chứng cho câu hỏi, nếu câu hỏi không yêu cầu phân tích nhận xét đánh giá hoặc các
        yêu cầu tương tự mà chỉ hỏi về số liệu thì hãy trả lời ngắn gọn. Lưu ý trong việc tính toán các chỉ số ở một số lĩnh vực những chỉ số cần tính toán có thể sẽ khác nhau hãy tự xác định 
        lĩnh vực dựa vào thông tin cung cấp và sử dụng những chỉ số tương đương NẾU ĐÚNG.
        {user_question} {user_prompt} 
            .....\
         nếu những thông tin vừa rồi không liên quan đến câu hỏi không cố trả lời hãy trả về không có thông tin cho câu hỏi. 
        """
    return final_prompt

def get_user_prompt(input_model='all-MiniLM-L6-v2', num_sim_docx=10, user_question = '',temp_path = None, prompt_chunk = None) ->str:
    similar_k = []
    similar_infos = find_information(input_model=input_model, k = num_sim_docx, infor_question = prompt_chunk, temp_path=temp_path)
    save_path = f'database/{os.path.splitext(os.path.basename(temp_path))[0]}.md'
    for i in range(len(prompt_chunk)):
        #todo: identify if metadatas if of docx or csv or md
        similar_k += retrieve(query=prompt_chunk[i] ,top_k=3,semantic_results=similar_infos[i], input_path = save_path)    
    similar_k = remove_same_content(similar_k)
    keys = list(similar_k[0].keys())
    
    if 'title' in keys:
        user_prompt = get_user_prompt_docx(user_question=user_question, similar_infos=similar_k)
    elif 'Mã số' in keys:
        user_prompt = get_user_prompt_csv(user_question=user_question, similar_infos=similar_k)
    else:
        user_prompt = get_user_prompt_md(user_question=user_question, similar_infos=similar_k)

    return user_prompt, similar_k

def get_user_prompt_from_graph(user_question = '',temp_path = None):
    # summary_section(temp_path= temp_path)
    
    doc = find_information_by_graph(temp_path=temp_path, user_question = user_question)
    if doc:
        prompt = f"""
        Bạn là một chuyên gia trong lĩnh vực tài chính hãy giúp người dùng trả lời những câu hỏi của họ đóng vài trò như một trợ lý trong 
        việc đọc hiểu và phân tích báo cáo tài chính. Hãy sử dụng những kiến thức tài chính để trả lời phân tích câu hỏi. Nếu câu hỏi ngắn gọn
        trả lời ngắn gọn. Mục tiêu trả lời đúng trọng tâm chính xác dựa trên tài liệu được cung cấp kèm trích dẫn số trang. Nếu nội dùng tài liệu cung cấp không liên quan đến
        câu hỏi không cố trả lời mà hãy trả về không có thông tin cho câu hỏi.
        Nếu có thông tin từ thuyết mình nói rõ thông tin trích từ thuyết minh báo cáo tài chính.
        Câu hỏi người dùng: {user_question}
        Tài liệu cung cấp : {doc} 
        Lưu ý quan sát kỹ tài liệu cung cấp và câu hỏi người dùng. 
        Nếu tài liệu cung cấp không liên quan gì đến tài chính, báo cáo tài chính hoặc các thông tin liên quan đến tài chính;
        hoặc Nếu thông tin được cung cấp không đủ để trả lời câu hỏi của người dùng
        trả về một từ duy nhất: NO không cần giải thích mô tả gì thêm.
        """
        response = call_api_gemi(prompt=prompt, model = "2.5-flash", temperture = 0.7)
        if response == 'NO':
            response, doc = respond_user_none_graph(user_question= user_question, temp_path= temp_path)
            return response, doc
            
        return response, doc
    else:
        response, doc = respond_user_none_graph(user_question= user_question, temp_path= temp_path)
        return response, doc

def use_local_model(prompt):
    client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")
    MODEL = "qwen/qwen3-8b"
    messages = [
    {"role": "assistant", "content": f"Let's answer all of my question by VietNamese and my instructions: {prompt}"}
    ]
    response = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                )
    return response.choices[0].message.content
    
def evaluate_LLM(question,answer,contexts,report_path, is_graph = True):
    if is_graph is False:
        contexts = [doc["content"] for doc in contexts] 
    log_entry = {
        "report": report_path,
        "question": question,
        "answer": answer,
        "contexts": contexts,
        "isGraph": is_graph
    }
    log_file = 'data_evalu_graph.json'
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []

    logs.append(log_entry)

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

    return answer, contexts

def parse_suggestions(text: str):
    items = re.split(r"\d+\.\s*", text)
    suggestions = [item.strip(" ,\n") for item in items if item.strip()]
    return suggestions

def render_markdown(md_text: str):
    # B1: convert markdown -> html
    html = markdown.markdown(md_text, extensions=['fenced_code', 'tables', 'nl2br'])
    # B2: sanitize html để chống XSS
    clean_html = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
    # B3: mark_safe để Django không escape
    return mark_safe(clean_html)
def parse_requery_output(llm_output: str):
    return [x.strip() for x in llm_output.split(",") if x.strip()]

# prompt_requery = f"""
#            Bạn là một trợ lý phân tích tài chính. Người dùng sẽ đưa ra câu hỏi dựa trên báo cáo tài chính.
#             Hãy xử lý lại câu hỏi để phục vụ việc tìm kiếm trong cơ sở dữ liệu vector theo nguyên tắc:
#             1. Nếu câu hỏi chỉ hỏi về một chỉ tiêu có thể tìm trực tiếp trong báo cáo (ví dụ: Doanh thu, Chi phí, Lợi nhuận gộp), hãy viết lại thành đúng cụm từ trong văn phong báo cáo tài chính (ví dụ: "tổng nợ" → "Nợ phải trả"). Trả về dạng chuỗi đơn.
#             2. Nếu câu hỏi liên quan đến một chỉ số không có sẵn trực tiếp (ví dụ: ROE, ROA, EPS, Biên lợi nhuận,...), hãy 
#             viết lại thành các hạng mục có thể có trong báo cáo tài chính để có dữ liệu cần thiết để tính toán chỉ số đó, các hạng mục cách nhau bằng dấu phẩy.
#             - ROE → Lợi nhuận sau thuế, Vốn chủ sở hữu
#             - ROA → Lợi nhuận sau thuế, Tổng tài sản
#             - EPS → Lợi nhuận sau thuế, Số lượng cổ phiếu lưu hành
#             - Biên lợi nhuận gộp → Lợi nhuận gộp, Doanh thu thuần
#             3. Nếu câu hỏi mang tính phân tích, suy luận, dự đoán hãy chỉ ra các hạng mục thông tin cần thiết để hỗ trợ đầy đủ thông phân tích suy luận dự đoán
#             các thông tin đó có thể được tìm thấy trong các bản báo cáo tài chính thường dùng của doanh nghiệp để tìm kiếm, nối lại thành một chuỗi, mỗi mục cách nhau bằng dấu phẩy.
#             4. Loại bỏ mọi yếu tố về thời gian (ví dụ: năm gần nhất, quý vừa qua...).
#             5. Chỉ trả về chuỗi kết quả, không kèm giải thích, không kèm ký hiệu ```json hay dấu ngoặc vuông.
#             6. Hãy tổng hợp thông tin dưới dạng 1 chuỗi các từ khóa cách nhau bởi dấu phảy, các từ khóa này phải là các hạng mục thường
#             có nằm trong BÁO CÁO TÀI CHÍNH của doanh nghiệp,do các doanh nghiệp có thể thuộc nhiều lĩnh vực khác nhau như: tài chính, ngân hàng, dịch vụ số,...
#             và một số thông tin hạng mục có thể có tên gọi khác nhau qua các lĩnh vực. Do đó hãy đưa hết các tên gọi có thể đảm báo việc tìm kiếm trên 
#             cơ sở dữ liệu vector tối ưu. 
           
#             Câu hỏi của người dùng: {user_question}
#             """
def respond_user_none_graph(user_question = '', temp_path = ''):
    prompt_requery = f"""
                Hãy tưởng tượng bạn là một trợ lý tài chính chuyên phân tích đọc hiểu BÁO CÁO TÀI CHÍNH. Giả sử người dùng đưa ra câu hỏi. Hãy suy nghĩ xem 
                bạn cần tìm những thông tin gì trong báo cáo tài chính để có thể trả lời phân tích suy luận diễn giải cho người dùng đầy đủ nhất, chi tiết nhất.
                - Nếu câu hỏi của người dùng là 1 thông tin trực tiếp không cần tính toán mà có thể tìm kiếm thẳng ở trong bao báo luôn thì hãy viết lại thành đúng cụm từ trong
                văn phong báo cáo tài chính trả về dạng chuỗi đơn.
                - Lưu ý các thông tin phải là thông tin có trực tiếp trong báo cáo tài chính. Với những thông tin KHÔNG CÓ SẴN cần tính toán như các chỉ số, tỷ lệ, hệ số, khả năng thanh khoản... KHÔNG ĐƯA TRỰC TIẾP 
                cần đưa các số liệu cần thiết để tính thay vì tính trực tiếp. Số liệu đó phải được tìm thấy trong các bảng báo cáo của báo cáo tài chính ví dụ như:
                    - ROE → Lợi nhuận sau thuế, Vốn chủ sở hữu
                    - ROA → Lợi nhuận sau thuế, Tổng tài sản
                    - EPS → Lợi nhuận sau thuế, Số lượng cổ phiếu lưu hành
                    - Biên lợi nhuận gộp → Lợi nhuận gộp, Doanh thu thuần
                - Hãy tổng hợp các thông tin đó dưới dạng dưới dạng keyword và các thông tin cách nhau bởi dấu "," ví dụ: thông tin1, thông tin2, ....
                - Hãy chỉ đưa ra câu trả lời trực tiếp và không cần giải thích thêm.
                - Hãy bỏ qua thông tin liên quan đến thời gian.
                - Lưu ý các ngành nghề, lĩnh vực khác, các thông tin sẽ có những cách gọi tên khác nhau, hãy đưa ra hết các tên gọi có thể có.
                - Mục định để phục vụ tìm kiếm trong cơ sở dữ liệu vector.
                - Lưu ý trả về tối đa 10 mục hãy ưu tiên để lấy được nhiều thông tin nhất.
                có thể được thay thế nhất trành trùng lặp quá nhiều không cần thiết.
                Câu hỏi của người dùng: {user_question}
            """
    query_rewriting = call_api_gemi(prompt_requery)
    features = parse_requery_output(query_rewriting)  
    print(features)
    user_prompt, contexts = get_user_prompt(input_model='all-MiniLM-L6-v2', num_sim_docx=10, user_question=user_question,temp_path=temp_path,prompt_chunk = features )
    response = call_api_gemi(user_prompt, model='2.5-flash')
    evaluate_LLM(user_question, response, contexts,temp_path, is_graph= False)
    return response, contexts
    
def respond_user(user_question, temp_path, useGraph = True, isSummary = False):
    if useGraph is False:
        response = respond_user_none_graph(user_question= user_question, temp_path= temp_path)
        return response, []
    if isSummary is True:
        print(isSummary)
        pdf_path = summary_section(temp_path= temp_path)
        return pdf_path
    else:
        try:
            response, contexts = get_user_prompt_from_graph(user_question=user_question, temp_path= temp_path)
            evaluate_LLM(user_question, response, contexts, temp_path)  
            return response, []
        except Exception as e:
            print(f"[Unhandled Error] {e}")
            print('Đồ thị lỗi')
            response, contexts = respond_user_none_graph(user_question= user_question, temp_path= temp_path)
            return response, []
