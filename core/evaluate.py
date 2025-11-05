# from output_generator import respond_user
# import os

# import random

# questions = {
#     "Cơ bản": [
#         "Doanh thu thuần của doanh nghiệp trong giai đoạn gần nhất là bao nhiêu?",
#         "Lợi nhuận sau thuế giai đoạn gần nhất tăng hay giảm so với giai đoạn trước đó? Tăng/giảm bao nhiêu %?",
#         "Tổng tài sản cuối giai đoạn gần nhất là bao nhiêu?",
#         "Nợ phải trả chiếm bao nhiêu % trong tổng nguồn vốn cuối giai đoạn gần nhất?",
#         "Chi phí bán hàng trong giai đoạn gần nhất là bao nhiêu?",
#         "Lưu chuyển tiền thuần từ hoạt động kinh doanh trong giai đoạn gần nhất là bao nhiêu?",
#         "Doanh nghiệp có chia cổ tức bằng tiền trong giai đoạn gần nhất không? Nếu có thì số tiền là bao nhiêu?"
#     ],
#     "Trung bình": [
#         "Hệ số thanh toán hiện hành của công ty trong giai đoạn gần nhất là bao nhiêu?",
#         "Biên lợi nhuận gộp trong giai đoạn gần nhất đạt bao nhiêu %?",
#         "Vòng quay hàng tồn kho trong giai đoạn gần nhất là bao nhiêu vòng?",
#         "Tỷ lệ nợ trên vốn chủ sở hữu trong giai đoạn gần nhất là bao nhiêu?",
#         "Tốc độ tăng trưởng doanh thu thuần của giai đoạn gần nhất so với giai đoạn trước đó là bao nhiêu %?",
#         "ROE trong giai đoạn gần nhất là bao nhiêu %?",
#         "EPS trong giai đoạn gần nhất là bao nhiêu?"
#     ],
#     "Nâng cao": [
#         "Nếu xu hướng lợi nhuận ròng của hai giai đoạn gần nhất tiếp tục, dự báo lợi nhuận trong giai đoạn tới sẽ khoảng bao nhiêu?",
#         "Dựa trên báo cáo lưu chuyển tiền tệ, công ty có đang phụ thuộc nhiều vào vay nợ để tài trợ cho hoạt động không?",
#         "Cấu trúc vốn của công ty thay đổi như thế nào trong hai giai đoạn gần nhất?",
#         "Doanh thu và lợi nhuận có tăng trưởng đồng đều trong hai giai đoạn gần nhất không?",
#         "Với hệ số thanh toán nhanh trong giai đoạn gần nhất, công ty có đủ khả năng trả nợ ngắn hạn không?",
#         "Tỷ suất lợi nhuận gộp và lợi nhuận ròng trong giai đoạn gần nhất chênh lệch nhiều, điều này phản ánh vấn đề gì?",
#         "So sánh hệ số nợ (D/E) của công ty trong giai đoạn gần nhất so với giai đoạn trước đó, xu hướng biến động thế nào?"
#     ]
# }
# reports = "report"
# import json

# def extract_reports_and_questions(json_path):
#     """
#     Đọc file JSON Q-A-C và trích xuất danh sách (report, question)
#     Trả về list of dict: [{'report': ..., 'question': ...}, ...]
#     """
#     with open(json_path, "r", encoding="utf-8") as f:
#         data = json.load(f)
    
#     result = []
#     for item in data:
#         report = item.get("report")
#         question = item.get("question")
#         if report and question:
#             result.append({"report": report, "question": question})
#     return result
# def generate_random_questions(report_folder):
#     reports = [f for f in os.listdir(report_folder) if os.path.isfile(os.path.join(report_folder, f))]
#     result = {}

#     for report in reports:
#         report_path = os.path.join(report_folder, report)
#         result[report] = {
#             level: random.sample(q_list, 3)  # chọn ngẫu nhiên 3 câu hỏi từ mỗi cấp độ
#             for level, q_list in questions.items()
#         }

#     return result
# import time
# # selected_questions = generate_random_questions(reports)
# qa_list = extract_reports_and_questions("data_test_GEMI.json")
# print(len(qa_list))
# for qa in qa_list[5:]:
#     print(qa["report"], " -> ", qa["question"])
#     respond_user(qa['question'],qa['report'])