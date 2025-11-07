# Tổng quan doanh nghiệp
# → Giới thiệu ngắn về công ty, ngành nghề, năm tài chính, mục tiêu.

# Phân tích bảng cân đối kế toán (Balance Sheet)
# → Tài sản, nợ phải trả, vốn chủ sở hữu, khả năng thanh toán.

# Phân tích báo cáo kết quả hoạt động kinh doanh (Income Statement)
# → Doanh thu, chi phí, lợi nhuận gộp, lợi nhuận thuần, chi phí tài chính.

# Phân tích dòng tiền (Cash Flow)
# → Dòng tiền từ hoạt động kinh doanh, đầu tư, tài chính.

# Chỉ số tài chính (Financial Ratios)
# → ROE, ROA, Current Ratio, Debt-to-Equity, Gross Margin, Net Margin.

# Phân tích xu hướng & dự báo (Trends & Outlook)
# → Xu hướng doanh thu, biên lợi nhuận, cảnh báo rủi ro, cơ hội.

# Nhận định tổng kết (Conclusion)
# → Nhấn mạnh điểm mạnh, điểm yếu, khuyến nghị hành động.

# from graph_query_graph import query_company_raw_text, query_thuyet_minh_raw_text, query_gioi_thieu_raw_text
# from call_api_llm import call_api_gemi
# from receiver import find_information, retrieve, remove_same_content, get_database, get_doc_from_notes_by_key_word

from core.graph_query_graph import query_company_raw_text, query_thuyet_minh_raw_text, query_gioi_thieu_raw_text
from core.call_api_llm import call_api_gemi
from core.receiver import find_information, retrieve, remove_same_content, get_database, get_doc_from_notes_by_key_word, normalize_for_prompt
import os
import random
import pypandoc
import os
import random
import markdown
from weasyprint import HTML, CSS

SUBSECTION_BALANCE_SHEET = ['TÀI SẢN NGẮN HẠN', 'TÀI SẢN DÀI HẠN', 'NỢ PHẢI TRẢ', 'VỐN CHỦ SỞ HỮU']
SUBSECTION_INCOME_STATEMENT = ['DOANH THU BÁN HÀNG VÀ CUNG CẤP DỊCH VỤ', 'DOANH THU HOẠT ĐỘNG TÀI CHÍNH', 'THU NHẬP KHÁC']
SUBSECTION_CASH_FLOW = ['LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG KINH DOANH', 'LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG ĐẦU TƯ', 'LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG TÀI CHÍNH']

# Cho ngân hàng
SUBSECTION_BALANCE_SHEET_FOR_BANK = ['TÀI SẢN', 'TÀI SẢN CỐ ĐỊNH', 'NỢ PHẢI TRẢ', 'VỐN CHỦ SỞ HỮU','CHỈ TIÊU NGOÀI']
SUBSECTION_INCOME_STATEMENT_FOR_BANK = [ "THU NHẬP LÃI VÀ CÁC KHOẢN", "THU NHẬP TỪ HOẠT ĐỘNG KHÁC", "CHI PHÍ THUẾ" ]

# Cho chứng khoán

SUBSECTION_BALANCE_SHEET_FOR_INDEX = ['TÀI SẢN NGẮN HẠN', 'TÀI SẢN DÀI HẠN', 'NỢ PHẢI TRẢ', 'VỐN CHỦ SỞ HỮU', "TÀI SẢN CỦA CÔNG TY CHỨNG KHOÁN",
    "TÀI SẢN VÀ CÁC KHOẢN PHẢI TRẢ"]
SUBSECTION_INCOME_STATEMENT_FOR_INDEX = [ "DOANH THU HOẠT ĐỘNG", "CHI PHÍ HOẠT ĐỘNG", "DOANH THU HOẠT ĐỘNG TÀI CHÍNH", "CHI PHÍ TÀI CHÍNH", "THU NHẬP KHÁC"
]
SUBSECTION_CASH_FLOW_FOR_INDEX = ['LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG KINH DOANH', 'LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG ĐẦU TƯ', 'LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG TÀI CHÍNH', 'PHẦN LƯU CHUYỂN TIỀN TỆ HOẠT ĐỘNG MÔI GIỚI']


def summary_finacial_statement(subsection, temp_path, infor, key_words, isBank = 'Không', isIndex = "Không"):
    section = "BẢNG CÂN ĐỐI KẾ TOÁN"
    result = ''
    notes_infor = ''
    for sub in subsection:
        doc = (query_company_raw_text(company_name= infor[0], time= infor[2], section=section, subsection= sub))
        for data in doc:
            result += data['table_structure'] + '\n' + data['raw_text'] + '\n' + "\n".join(map(str, data['pages']))
        
    notes_infor = get_doc_from_notes_by_key_word(key_word= key_words, infor= infor, temp_path= temp_path)  
        
    prompt_gen_summary = f'''
        Bạn là 1 chuyên gia trong lĩnh vực tài chính, vai trò của bạn là đọc hiểu và phân tính báo cáo tài chính hỗ trợ người dùng,
        Nhiệm vụ lần này của bạn là:
        Dựa vào thông tin về Bảng cân đối kế toán và thuyết minh báo cáo tương ứng. Hãy sinh ra 1 đoạn phân tích dựa trên các thông tin đó để tạo ra 1 file summary tóm tắt 
        hết sức NGẮN GỌN lại những điểm nổi bật có trong Bảng cân đối kế toán của công ty đó, dựa trên hướng dẫn sau:
        Cách đọc Bảng cân đối kế toán 
        LƯU Ý: Các thông tin đề cập trong cách đọc có thể tinh chỉnh cho phù hợp với lĩnh vực của công ty ví dụ Ngân hàng, chứng khoán, ... không bó buộc phải tuân theo hoàn toàn.
            Mục tiêu: Đọc báo cáo này để hiểu rõ tài sản và nguồn vốn của doanh nghiệp đến từ đâu và tập trung vào lĩnh vực nào.
            Cách đọc bảng cân đối kế toán gồm các bước sau:
                Bước 1: Xác định các nội dung chính trong hạng mục tài sản và nguồn vốn.
                Bước 2: Tính toán tỷ lệ của từng khoản mục trong 2 phần này và so sánh sự thay đổi của chúng qua các kỳ.
                Bước 3: Ghi nhận những khoản chiếm tỷ trọng lớn hoặc có sự biến động lớn về giá trị.
            Sau khi hoàn thành 3 bước, cần trả lời được các câu hỏi sau:
            Phần nguồn vốn:
                - Nguồn vốn của doanh nghiệp đến từ nợ và vốn chủ sở hữu là bao nhiêu, nguồn nào chiếm tỷ trọng lớn hơn;
                - Nợ phải trả chủ yếu là nợ ngắn hạn hay nợ dài hạn;
                - So sánh giữa đầu kỳ và cuối kỳ, nguồn nào tăng, nguồn nào giảm, và mức độ thay đổi có hợp lý không...
            Phần tài sản:
                - Tổng giá trị tài sản là bao nhiêu và gồm những loại tài sản nào;
                - Phần lớn tài sản của doanh nghiệp tập trung vào đâu;
                - So sánh giữa đầu kỳ và cuối kỳ, tài sản nào tăng, tài sản nào giảm, và tỷ lệ thay đổi như thế nào...
            Đánh giá sau khi đọc bảng cân đối kế toán:
            người mới bắt đầu nên chú ý các chỉ số như: khoản phải thu của khách hàng (tài khoản 131), khoản phải trả cho nhà cung cấp (tài khoản 331), và vốn lưu động.
            Kết cấu bảng cân đối kế toán
            Bảng cân đối kê toán gồm có 2 phần tài sản và nguồn vốn:
            Phần tài sản: Tài sản của doanh nghiệp phản ánh quy mô và nguồn lực mà doanh nghiệp đang nắm giữ.
                - Tài sản ngắn hạn: Đây là những tài sản có thời gian sử dụng dưới 12 tháng hoặc trong một chu kỳ kinh doanh bình thường và thường xuyên thay đổi giá trị trong quá trình sử dụng. Đối với doanh nghiệp, tài sản ngắn hạn thường bao gồm: tiền mặt và các khoản tương đương tiền, hàng tồn kho, các khoản phải thu, và các khoản đầu tư ngắn hạn.
                - Tài sản dài hạn: Là những tài sản có thời gian sử dụng, luân chuyển và thu hồi trên 12 tháng hoặc kéo dài qua nhiều chu kỳ kinh doanh. Tài sản dài hạn thường bao gồm: tài sản cố định, các khoản đầu tư tài chính dài hạn, các khoản phải thu dài hạn, và các tài sản như nhà xưởng, máy móc, thiết bị, tạo nền tảng cho hoạt động sản xuất kinh doanh.
            Phần nguồn vốn: Nguồn vốn phản ánh tài sản của doanh nghiệp đến từ đâu và những nghĩa vụ pháp lý, kinh tế mà doanh nghiệp phải thực hiện đối với các nguồn này. Ví dụ, để đầu tư mua máy móc thiết bị, doanh nghiệp có thể sử dụng vốn tự có, vay ngân hàng, hoặc kết hợp cả hai. Cơ cấu nguồn vốn được chia thành nợ phải trả và vốn chủ sở hữu.
                - Nợ phải trả: Gồm nợ ngắn hạn và nợ dài hạn, tương ứng với các nghĩa vụ nợ dưới 1 năm và trên 1 năm của doanh nghiệp. Nợ phải trả là nguồn vốn quan trọng để đáp ứng nhu cầu kinh doanh, nhưng cần được quản lý hiệu quả để đảm bảo khả năng thanh toán và tích lũy cho sự phát triển của doanh nghiệp.
                - Vốn chủ sở hữu: Đây là nguồn vốn từ chính chủ sở hữu doanh nghiệp, và là phần còn lại của tài sản sau khi đã thanh toán các khoản nợ. Vốn chủ sở hữu rất quan trọng vì nó là nguồn vốn dài hạn và không có nghĩa vụ thanh toán, giúp doanh nghiệp duy trì và phát triển hoạt động.

    Trả về kết quả trước tiếp mà không cần lời giới thiệu giải thích theo mẫu sau:
        ## 2. Phân tích bảng cân đối kế toán.
            [Nội dung ]
    Dưới đây là thông tin về Bảng cân đối kế toán: {result}, thuyết minh tương ứng: {notes_infor}, đây là doanh nghiệp {isBank} là ngân hàng, {isIndex} là chứng khoán.
    '''
    response = call_api_gemi(prompt_gen_summary, model='2.0-flash')
    
    return response

def cal_financial_radio(infor,isBank = None, isIndex = None):
    sections = ['BẢNG CÂN ĐỐI KẾ TOÁN', 'BÁO CÁO KẾT QUẢ HOẠT ĐỘNG KINH DOANH', 'BÁO CÁO LƯU CHUYỂN TIỀN TỆ']
    result = ''
    for i, sec in enumerate(sections):
        result += sec + '\n'
        subsection = []
        if i == 0:
            if isBank ==  'CÓ':
                subsection = SUBSECTION_BALANCE_SHEET_FOR_BANK
            elif isIndex == 'CÓ':
                subsection == SUBSECTION_BALANCE_SHEET_FOR_INDEX
            else:
                subsection = SUBSECTION_BALANCE_SHEET
        elif i == 1:
            if isBank == 'CÓ':
                subsection = SUBSECTION_INCOME_STATEMENT_FOR_BANK
            elif isIndex == 'CÓ':
                subsection = SUBSECTION_INCOME_STATEMENT_FOR_INDEX
            else:
                subsection = SUBSECTION_INCOME_STATEMENT
        elif i == 2:
            if isIndex == 'CÓ':
                subsection = SUBSECTION_CASH_FLOW_FOR_INDEX
            subsection = SUBSECTION_CASH_FLOW
            
        for sub in subsection:
            doc = (query_company_raw_text(company_name= infor[0], time= infor[2], section=sec, subsection= sub))
            for data in doc:
                result += data['table_structure'] + '\n' + data['raw_text'] + '\n' + "\n".join(map(str, data['pages']))
    prompt_cal_radio = f'''
        Dựa vào thông tin được cung cấp hãy tính những chỉ số tài chính quan trọng sau dựa trên hướng dẫn sau:
        LƯU Ý: đây chỉ là tính toán trên 1 báo cáo tài chính trong 1 giai đoạn nhất định (theo quý, năm, hoặc 6 tháng). Hãy tận dùng những thông tin số liệu được cung cấp, có thể tính toán 
        dựa theo công thức có thể áp dụng cho quý, giai đoạn, hoặc năm (có chú thích nếu cần).
        LƯU Ý: công thức cũng có thể điều chỉnh để áp dụng có các doanh nghiệp ngân hàng chứng khoán hoặc bất kỳ dữ liệu nào phù hợp có trong tài liệu được cung cấp, có thể tính toán thêm những chỉ số 
        nếu cần.
            1. Chỉ số thanh khoản (Khả năng thanh toán)

            Đánh giá khả năng doanh nghiệp đáp ứng nghĩa vụ tài chính ngắn hạn.

            | Chỉ số | Công thức | Ý nghĩa |
            |--------|------------|---------|
            | Thanh khoản hiện hành | Tài sản ngắn hạn / Nợ ngắn hạn | >1 là tốt. Khả năng thanh toán ngắn hạn. |
            | Thanh khoản nhanh | (Tài sản ngắn hạn - Hàng tồn kho) / Nợ ngắn hạn | Loại trừ hàng tồn kho, sát thực hơn. |
            | Thanh khoản tức thời | Tiền và tương đương tiền / Nợ ngắn hạn | Khả năng trả nợ tức thời, rất nghiêm ngặt. |


            2. Chỉ số đòn bẩy tài chính

            Phản ánh mức độ sử dụng nợ và khả năng trả nợ.

            | Chỉ số | Công thức | Ý nghĩa |
            |--------|------------|---------|
            | Hệ số nợ | Tổng nợ / Tổng tài sản | Phần tài sản tài trợ bằng nợ. Cao → rủi ro tài chính lớn. |
            | Nợ trên vốn chủ | Tổng nợ / Vốn chủ sở hữu | Đo lường mức đòn bẩy tài chính. |
            | Khả năng thanh toán lãi vay | EBIT / Chi phí lãi vay | Khả năng trả lãi. >3 là an toàn. |


            3. Chỉ số hiệu quả hoạt động

            Đánh giá hiệu quả quản lý tài sản và hoạt động kinh doanh.

            | Chỉ số | Công thức | Ý nghĩa |
            |--------|------------|---------|
            | Vòng quay hàng tồn kho | Giá vốn hàng bán / Hàng tồn kho bình quân | Quản lý hàng tồn kho. Cao → hiệu quả. |
            | Vòng quay khoản phải thu | Doanh thu thuần / Khoản phải thu bình quân | Quản lý công nợ khách hàng. |
            | Vòng quay tổng tài sản | Doanh thu thuần / Tổng tài sản bình quân | Hiệu quả sử dụng tài sản. |


            4. Chỉ số lợi nhuận

            Đánh giá khả năng sinh lời của doanh nghiệp.

            | Chỉ số | Công thức | Ý nghĩa |
            |--------|------------|---------|
            | Biên lợi nhuận gộp | Lợi nhuận gộp / Doanh thu thuần | Biên độ lợi nhuận trước chi phí. |
            | Biên lợi nhuận ròng | Lợi nhuận sau thuế / Doanh thu thuần | Lợi nhuận giữ lại trên mỗi đồng doanh thu. |
            | ROA (Hiệu quả tài sản) | Lợi nhuận sau thuế / Tổng tài sản bình quân | Khả năng sinh lời trên tài sản. |
            | ROE (Hiệu quả vốn chủ sở hữu) | Lợi nhuận sau thuế / Vốn chủ sở hữu bình quân | Khả năng sinh lời trên vốn chủ. |


            5. Chỉ số định giá (phục vụ đầu tư cổ phiếu)

            Dành cho nhà đầu tư phân tích giá trị cổ phiếu.

            | Chỉ số | Công thức | Ý nghĩa |
            |--------|------------|---------|
            | EPS | Lợi nhuận sau thuế / Số cổ phiếu lưu hành | Lợi nhuận trên mỗi cổ phiếu. |
            | P/E | Giá thị trường / EPS | Giá cổ phiếu so với thu nhập. Cao → kỳ vọng tăng trưởng. |
            | P/B | Giá thị trường / Giá trị sổ sách (BVPS) | Định giá so với tài sản. <1 có thể là định giá thấp. |


            6. Các chi tiêu cơ bản khác phân tích theo năm

            | Chỉ tiêu | Công thức / Ý nghĩa |
            |-----------|----------------------|
            | Doanh thu Thuần | Doanh thu bán - (trừ) Giảm giá hàng bán, hàng bán bị trả lại |
            | Giá vốn |  |
            | Lợi nhuận gộp | Doanh thu Thuần - Giá vốn |
            | Lợi nhuận trước thuế Thu nhập Doanh nghiệp |  |
            | Lợi nhuận sau thuế Thu nhập Doanh nghiệp |  |
            

            7. Tăng trưởng Doanh thu, lợi nhuận, Giá vốn,… Chi phí các năm

            Công thức: (năm nay - năm trước) / năm trước * 100 (%)

            Dùng để tính tỷ lệ tăng trưởng (%), thể hiện mức thay đổi của các chỉ tiêu tài chính như Doanh thu, Giá vốn, Lợi nhuận, Chi phí… giữa hai năm liên tiếp.
            
            8. Dòng tiền.
            
            DOANH THU THUẦN (Net Cash Flow from Operating Activities - CFO)
                Tỷ lệ này giúp cho chúng ta biết doanh nghiệp nhận được bao nhiêu đồng trên 1 đồng doanh thu thuần. Mặc dù không có một con số cụ thể để tham chiếu, 
                tuy nhiên rõ ràng là tỷ lệ này càng cao thì càng tốt. Và chúng ta cũng nên so sánh với dữ liệu quá khứ để phát hiện ra các sai sót khác.
                CFO dương: Doanh nghiệp tạo ra lượng tiền dương từ hoạt động kinh doanh chính. Đây là một dấu hiệu tích cực.
                CFO âm: Doanh nghiệp đang tiêu tốn tiền mặt trong hoạt động kinh doanh
            TỶ SUẤT DÒNG TIỀN TỰ DO (Free Cash Flow to Equity - FCFE)
                Tỷ suất này giúp chúng ta phản ánh được chất lượng dòng tiền của doanh nghiệp. Dòng tiền tự do phản ánh số tiền sẵn có nhằm sử dụng cho các hoạt động của doanh nghiệp.
                Trong đó:
                    Dòng tiền tự do (Free Cashflow)	=	Lưu chuyển tiền thuần từ hợp đồng kinh doanh - Dòng tiền đầu tư cho tài sản cố định
                    Doanh nghiệp phải trừ đi Dòng tiền cho hoạt động đầu tư tài sản cố định, bởi vì dòng tiền đầu tư tài sản cố định được xem như là để duy trì lợi thế cạnh tranh và hiệu quả hoạt động cho doanh nghiệp.
                    Như vậy, dòng tiền tự do càng lớn, chứng tỏ tình hình tài chính của doanh nghiệp càng tích cực.
            XU HƯỚNG CỦA DÒNG TIỀN
                    Để thực hiện phân tích xu hướng dòng tiền, số liệu dòng tiền của từng hoạt động sẽ được cộng dồn theo từng năm.
                    Mục đích của việc phân tích xu hướng của dòng tiền là để loại bỏ sự biến động về dòng tiền tại một thời điểm cụ thể. Ngoài ra, việc quan sát dòng tiền trong một giai đoạn dài sẽ giúp chúng ta xác định được doanh nghiệp đang trong giai đoạn nào của chu kỳ kinh doanh. Đây chính là yếu tố quan trọng để chúng ta đưa ra quyết định về việc có nên tài trợ vốn cho doanh nghiệp trong giai đoạn hiện tại hay không?
            LƯU Ý: Trả lời trình bày thật dễ hiểu và hết sức ngắn gọn logic sử dụng trình bày kiểu Bảng để quat sát nội dung một cách logic hơn.
            Nếu chỉ số không tính được hãy chú thích đầy đủ bên cách lý do
            vì sao không tính được, Trả lời thẳng trực tiếp NGẮN GỌN không cần giải thích và mở đầu câu trả lời như sau:
                ## 5. Các chỉ số tài chính cơ bản.

                [Nội dung]
                    
            Tài liệu được cung cấp: {result}, Doanh nghiệp {isBank} là ngân hàng, Doanh nghiêp {isBank} là công ty tài chính.
    '''
    response = call_api_gemi(prompt=prompt_cal_radio)
    print(result)
    # print(response)
    return response

def summary_income_statement(subsection, temp_path, infor, key_words, isBank = 'Không', isIndex = 'Có'):
    section = "BÁO CÁO KẾT QUẢ HOẠT ĐỘNG KINH DOANH"
    result = ''
    notes_raw_text = ''
    notes_infor = ''
    similar_k = []
    for sub in subsection:
        doc = (query_company_raw_text(company_name= infor[0], time= infor[2], section=section, subsection= sub))
        for data in doc:
            result += data['table_structure'] + '\n' + data['raw_text'] + '\n' + "\n".join(map(str, data['pages']))
        
    notes = query_thuyet_minh_raw_text(company_name= infor[0], time= infor[2])
    for data in notes:
        notes_raw_text += data['raw_text'] + '\n'
    notes_doc = find_information(infor_question= key_words, k=10, temp_path = temp_path, content = notes_raw_text)
    
    for i in range(len(key_words)):
        similar_k += retrieve(query=key_words[i] ,top_k=3,semantic_results=notes_doc[i], input_path = '', content= notes_raw_text)    
    similar_k = remove_same_content(similar_k)
    for i, k in enumerate(similar_k):
        notes_infor += f"Thông tin {i} trong Thuyết minh báo cáo tài chính \n " + f'{k['content']}' + "\n"  
        
    prompt_gen_summary = f'''
        Bạn là 1 chuyên gia trong lĩnh vực tài chính, vai trò của bạn là đọc hiểu và phân tính báo cáo tài chính hỗ trợ người dùng,
        Nhiệm vụ lần này của bạn là:
        Dựa vào thông tin về Báo cáo kết quả hoạt động kinh doanh hay báo cáo kết quả hoạt động (nếu doanh nghiệp là ngân hàng) và thuyết minh báo cáo tương ứng. 
        Hãy sinh ra 1 đoạn phân tích dựa trên các thông tin đó để tạo ra 1 file summary hết sức NGẮN GỌN tóm tắt lại những điểm nổi bật có trong Báo cáo kết quả hoạt động kinh doanh 
        hay báo cáo kết quả hoạt động (nếu doanh nghiệp là ngân hàng) của doanh nghiệp đó, dựa trên hướng dẫn sau:
         Cách đọc báo cáo kết quả hoạt động kinh doanh
        LƯU Ý: Các thông tin đề cập trong cách đọc có thể tinh chỉnh cho phù hợp với lĩnh vực của công ty ví dụ Ngân hàng, chứng khoán, ... không bó buộc phải tuân theo hoàn toàn.
            Việc đọc báo cáo kết quả hoạt động kinh doanh giúp bạn hiểu rõ tình hình kinh doanh của doanh nghiệp, 
            bao gồm tổng doanh thu, chi phí, kết quả kinh doanh, lãi hay lỗ. Báo cáo này gồm các phần:
                - Kết quả từ hoạt động kinh doanh
                - Kết quả từ hoạt động tài chính
                - Kết quả từ hoạt động khác
            Hướng dẫn đọc báo cáo kết quả kinh doanh cho người mới:
                - Bước 1: Xác định và phân loại các khoản chi phí và doanh thu.
                - Bước 2: Tính toán tỷ lệ của từng khoản mục so với tổng doanh thu và tổng chi phí, sau đó so sánh sự thay đổi giữa các kỳ.
                - Bước 3: Phân tích và đánh giá sự thay đổi của từng khoản mục.
            Các chỉ số cần chú ý khi đọc báo cáo kết quả kinh doanh:
                - Lợi nhuận gộp từ bán hàng và cung cấp dịch vụ
                - Doanh thu thuần từ bán hàng và cung cấp dịch vụ
                - Lợi nhuận sau thuế
            Kết cấu báo cáo kết quả hoạt động kinh doanh:

            Khi đọc báo cáo kết quả hoạt động kinh doanh, cần nắm các thông tin quan trọng sau:
                - Tổng doanh thu, chi phí, và lợi nhuận với giá trị tuyệt đối là bao nhiêu;
                - Lợi nhuận chính đến từ hoạt động nào: kinh doanh, tài chính, hay hoạt động khác;
                - Doanh thu, chi phí, và lợi nhuận có xu hướng thay đổi theo cùng chiều hay không;
                - Chi phí từ hoạt động hoặc giai đoạn nào đang gây ra vấn đề đáng chú ý.
    Trả về kết quả trực tiếp mà không cần lời giới thiệu hay giải thích, comment theo mẫu sau.
        ## 3. Báo cáo kết quả hoạt động kinh doanh:
        [Nội dung]

    Dưới đây là thông tin về báo cáo kết quả hoạt động kinh doanh {result}, thuyết minh tương ứng: {notes_infor}, đây là doanh nghiệp {isBank} là ngân hàng, {isIndex} là chứng khoán.
    '''
    response = call_api_gemi(prompt_gen_summary,model = '2.0-flash', temperture= 0)
    return response

def summary_cash_flow(subsection, temp_path, infor, key_words, isBank = 'Không', isIndex = 'Có'):
    section = "BÁO CÁO LƯU CHUYỂN TIỀN TỆ"
    result = ''
    notes_raw_text = ''
    notes_infor = ''
    similar_k = []
    for sub in subsection:
        doc = (query_company_raw_text(company_name= infor[0], time= infor[2], section=section, subsection= sub))
        for data in doc:
            result += data['table_structure'] + '\n' + data['raw_text'] + '\n' + "\n".join(map(str, data['pages']))
        
    notes = query_thuyet_minh_raw_text(company_name= infor[0], time= infor[2])
    for data in notes:
        notes_raw_text += data['raw_text'] + '\n'
    notes_doc = find_information(infor_question= key_words, k=10, temp_path = temp_path, content = notes_raw_text)
    
    for i in range(len(key_words)):
        similar_k += retrieve(query=key_words[i] ,top_k=3,semantic_results=notes_doc[i], input_path = '', content= notes_raw_text)    
    similar_k = remove_same_content(similar_k)
    for i, k in enumerate(similar_k):
        notes_infor += f"Thông tin {i} trong Thuyết minh báo cáo tài chính \n " + f'{k['content']}' + "\n"  
        
    prompt_gen_summary = f'''
        Bạn là 1 chuyên gia trong lĩnh vực tài chính, vai trò của bạn là đọc hiểu và phân tính báo cáo tài chính hỗ trợ người dùng,
        Nhiệm vụ lần này của bạn là:
        Dựa vào thông tin về BÁO CÁO LƯU CHUYỂN TIỀN TỆ và thuyết minh báo cáo tương ứng. 
        Hãy sinh ra 1 đoạn phân tích dựa trên các thông tin đó để tạo ra 1 file summary hết sức NGẮN GỌN logic tóm tắt lại những điểm nổi bật có trong BÁO CÁO LƯU CHUYỂN TIỀN TỆ 
        của doanh nghiệp đó, dựa trên hướng dẫn sau:
         Cách đọc BÁO CÁO LƯU CHUYỂN TIỀN TỆ
        LƯU Ý: Các thông tin đề cập trong cách đọc có thể tinh chỉnh cho phù hợp với lĩnh vực của công ty ví dụ Ngân hàng, chứng khoán, ... không bó buộc phải tuân theo hoàn toàn.
            Việc đọc báo cáo lưu chuyển tiền tệ giúp nắm bắt tình hình thu chi và biến động dòng tiền của doanh nghiệp, được chia thành ba hoạt động chính: kinh doanh, đầu tư và tài chính. Dòng tiền ra được thể hiện bằng số âm, trong khi dòng tiền vào là số dương.
            Khi đọc báo cáo lưu chuyển tiền tệ, cần chú ý đến các thông tin chính sau:
                + Dòng tiền tổng và dòng tiền từ từng hoạt động là âm hay dương, giá trị tuyệt đối của chúng;
                + Tiền được tạo ra từ hoạt động nào và tỷ trọng của từng dòng tiền so với tổng dòng tiền vào;
                + Dòng tiền đang tăng hay giảm, và nguyên nhân của sự biến động đó;
                + Tiền được sử dụng cho mục đích gì, liệu doanh nghiệp có sử dụng tiền vay không đúng mục đích hay không, và liệu doanh nghiệp có đủ khả năng trả cổ tức;
                + Nhu cầu tài trợ từ các nguồn bên ngoài của doanh nghiệp.
            Các chỉ số cần lưu ý khi đọc báo cáo lưu chuyển tiền tệ:
            Nhà đầu tư, đặc biệt là người mới tìm hiểu, cần chú ý đến chỉ số lưu chuyển tiền từ hoạt động kinh doanh.
                + Xu hướng tích cực: Chỉ số này dương trong nhiều kỳ, cho thấy doanh nghiệp có dòng tiền ổn định để duy trì hoạt động.
                + Xu hướng tiêu cực: Chỉ số này âm trong nhiều kỳ, cho thấy doanh nghiệp phải vay để bù đắp thiếu hụt.
            Kết cấu của báo cáo lưu chuyển tiền tệ:
                + Dòng tiền từ hoạt động kinh doanh: Dòng tiền này phát sinh từ các giao dịch liên quan đến hoạt động kinh doanh thường nhật như thu tiền từ bán hàng, thanh toán cho nhà cung cấp, trả lương nhân viên. Đây là dòng tiền mà doanh nghiệp tự tạo ra, không phải từ vốn đầu tư hay vay nợ, vì vậy nó rất được chú ý để đánh giá khả năng tạo tiền và độ bền vững của lợi nhuận trong báo cáo kết quả kinh doanh.
                + Dòng tiền từ hoạt động đầu tư: Bao gồm dòng tiền vào và ra từ các hoạt động liên quan đến đầu tư, mua sắm, thanh lý tài sản cố định, và các khoản đầu tư tài chính, tài sản dài hạn.
                + Dòng tiền từ hoạt động tài chính: Liên quan đến sự tăng/giảm vốn chủ sở hữu (như nhận vốn góp mới, phát hành cổ phiếu, trả cổ tức) và vay nợ (chi trả nợ gốc, nhận nợ mới).
            Phương trình lưu chuyển tiền tệ:
                Dòng tiền của doanh nghiệp được thể hiện qua phương trình:
                Tiền tồn đầu kỳ + Tiền thu trong kỳ - Tiền chi trong kỳ = Tiền tồn cuối kỳ.
    Trả về kết quả trực tiếp mà không cần lời giới thiệu giải thích, comment theo mẫu sau.
        ## 4. Báo cáo lưu chuyển tiền tệ .
        [Nội dung]
    Dưới đây là thông tin về báo cáo kết quả hoạt động kinh doanh {result}, thuyết minh tương ứng: {notes_infor}, đây là doanh nghiệp {isBank} là ngân hàng, {isIndex} là chứng khoán.
    '''
    response = call_api_gemi(prompt_gen_summary, temperture= 0)
    return response

def summary_info_company(infor):
    infor_raw = ''
    # // lấy nửa đầu thuyết minh
    infor = query_thuyet_minh_raw_text(company_name= infor[0], time= infor[2])
    for data in infor:
        infor_raw += data['raw_text'] + '\n'
    infor_raw = infor_raw[ :16384]
    prompt_infor = f'''Dựa vào đọc thông tin sau hãy đưa ra một bản tóm tắt giới thiệu ngắn về doanh nghiệp và xem doanh nghiệp có tuân theo chuẩn kế toán nào không hay một số nguyên tắc ngắn ngọn.
        hết sức NGẮN GỌN trả về dưới trực tiếp không cần giải thích, comment mở đầu câu trả lời như sau:
        ## 1. Tổng quan về doanh nghiệp.
        [Nội dung]
        {infor_raw}
    '''
    response = call_api_gemi(prompt_infor, temperture = 0)
    return response

def analysis_ratio(ratio, isBank = 'Không', isIndex = 'Không'):
    prompt_instruction = f'''
        Bạn là chuyên gia trong phân tích báo cáo tài chính qua 1 giai đoạn theo năm hoặc quý của. Vài trò của bạn là hỗ trợ người dùng phân tích những điểm quan trọng trong báo cáo
        tài chính, nhận định hỗ trợ các quyết định của người dùng, nhiệm vụ của bạn lần này là:
        Dựa vào bảng chỉ số sau:
        {ratio}
        Lĩnh vực của doanh nghiệp {isBank} ngân hàng, {isIndex}là chứng khoán.
        Hãy phân tích theo hướng dẫn sau:
        LƯU Ý: Hướng dẫn có thể sử dụng những thuật ngữ chung trong kinh doanh, không bắt buộc phải tuân theo hoàn toàn, bạn hoàn toàn có thể tùy chỉnh để phù hợp với lĩnh vực 
        hoạt động của doanh nghiệp như ngân hàng, chứng khoán, ... Hay chỉ dựa vào để tham khảo.
            1. Phân tích cơ cấu nguồn vốn và cơ cấu tài sản
                TỶ LỆ VỐN CHỦ SỞ HỮU
                    Đây là hệ số phản ánh sức tài chính và mức độ độc lập của doanh nghiệp.
                    Một số đánh giá có thể đưa ra khi phân tích tỷ lệ vốn chủ sở hữu:
                Tỷ lệ vốn chủ sở hữu cao:
                    Doanh nghiệp đang sử dụng nhiều vốn của cổ đông, ít phụ thuộc vào vốn vay >> sức khỏe tài chính tốt.
                    Hoặc doanh nghiệp đang sử dụng vốn không hiệu quả và có thể gặp khó khăn khi tăng trưởng nếu không có đủ nguồn vốn.
                Tỷ lệ vốn chủ sở hữu thấp:
                    Doanh nghiệp phụ thuộc nhiều vào vốn vay dễ gặp rủi ro tài chính nếu phải trả lãi và gốc vay.
                    Hoặc doanh nghiệp đang sử dụng hiệu quả các nguồn vốn và có cơ hội sinh lời cao từ đây.
                TỶ LỆ ĐẦU TƯ VÀO TÀI SẢN NGẮN HẠN, TÀI SẢN DÀI HẠN
                    Đây là chỉ số đánh giá khả năng thanh khoản và khả năng sinh lời của doanh nghiệp.
                Một số đánh giá khi phân tích tỷ lệ đầu tư vào tài sản ngắn hạn, tài sản dài hạn:
                - Đối với tài sản ngắn hạn: Giúp doanh nghiệp duy trì tính thanh khoản cao và khả năng chi trả ngắn hạn:
                    + Tỷ lệ đầu tư vào tài sản ngắn hạn cao: Doanh nghiệp đang tập trung đầu tư vào tài sản ngắn hạn và có thể gặp khó khăn khi đầu tư vào các tài sản dài hạn.
                    + Tỷ lệ đầu tư vào tài sản ngắn hạn thấp: Doanh nghiệp đang tập trung đầu tư vào tài sản dài hạn và thiếu tính linh hoạt khi thực hiện thanh toán các khoản chi ngắn hạn.
                - Đối với tài sản dài hạn: Đánh giá mức độ đầu tư vào các tài sản dài hạn và chiến lược tăng trưởng của doanh nghiệp.
                    + Tỷ lệ đầu tư vào tài sản dài hạn cao: Doanh nghiệp đang tập trung phát triển và mở rộng hoạt động sản xuất kinh doanh trong dài hạn. Tuy nhiên, nếu tỷ lệ này quá cao có thể khiến doanh nghiệp gặp các rủi ro tài chính:
                        Không tận dụng hiệu quả các tài sản dài hạn để tạo ra lợi nhuận.
                        Không có đủ thanh khoản để đối phó với nhu cầu ngắn hạn
                Tỷ lệ đầu tư vào tài sản dài hạn thấp:
            
            2. Phân tích khả năng thanh toán
                Doanh nghiệp chỉ có thể tồn tại khi có khả năng thanh toán các khoản nợ khi đến hạn. Để đánh giá khả năng này doanh nghiệp cần sử dụng một số hệ số thanh toán sau:
                HỆ SỐ THANH TOÁN HIỆN HÀNH (Current Ratio)
                    Đây là hệ số đánh giá khả năng thanh toán các khoản nợ ngắn hạn của doanh nghiệp.
                    Một số đánh giá có thể đưa ra:
                    - Nếu hệ số thanh toán >1: Doanh nghiệp hoàn toàn có khả năng thanh toán các khoản nợ ngắn hạn bằng tài sản lưu động. Tuy nhiên, nếu hệ số này quá cao cũng phản ánh rằng doanh nghiệp đang không tận dụng hiệu quả tiền mặt hoặc tài sản lưu động.
                    - Nếu hệ số thanh toán <1: Doanh nghiệp sẽ gặp phải khó khăn trong việc thanh toán các khoản nợ. Đây là dấu hiệu xảy ra rủi ro về thanh toán mà doanh nghiệp có thể gặp.
                    - Hệ số thanh toán nằm trong khoảng 1,5-2: Đây là một hệ số tốt cho thấy tài sản ngắn hạn đủ lớn để thanh toán các khoản nợ một cách an toàn.
                HỆ SỐ KHẢ NĂNG THANH TOÁN LÃI VAY (Interest Coverage Ratio)
                    Đây là hệ số đánh giá được doanh nghiệp có đủ lợi nhuận để thanh toán được các khoản nợ lãi hay không nhắm đảm bảo rằng doanh nghiệp không
                    gặp khó khăn khi trả lãi vay và duy trì sức khỏe tài chính ổn định.
                    Hệ số khả năng thanh toán lãi vay tiêu chuẩn là 1,5. Nếu hệ số này:
                        - <1,5: Doanh nghiệp có khả năng vỡ nợ cao, khiến các nhà đầu tư sẽ không muốn tiếp tục đầu tư.
                        - <1: Doanh nghiệp sẽ phải chi trả một khoản tiền dự trữ để đáp ứng chi phí chênh lệch hoặc vay thêm. Nếu doanh nghiệp để tình trạng này diễn ra thường xuyên và không thể xử lý thì công ty sẽ có nguy cơ bị phá sản.
                HỆ SỐ VÒNG QUAY KHOẢN PHẢI THU (Receivable Turnover Ratio)
                    Đây là hệ số đánh giá được sau bao lâu thì doanh nghiệp thu hồi được tiền từ khách hàng. 
                    Doanh nghiệp có thể gặp khó khăn trong hoạt động sản xuất kinh doanh nếu không thu được tiền.
                    - Vòng quay khoản phải thu	=	Doanh thu bán hàng / Các khoản phải thu bình quân
                    Từ đó ta tính được kỳ thu tiền bình quân trong 1 năm như sau:

                    -  Kỳ thu tiền bình quân (ngày)	=	360 / Vòng quay các khoản phải thu

                    Nếu hệ số vòng quay khoản phải thu bằng 12 hoặc kỳ thu tiền bình quân là 30 ngày thì có nghĩa là doanh nghiệp sẽ cần khoảng 30 ngày để thu hồi được các khoản phải thu.
                HỆ SỐ VÒNG QUAY HÀNG TỒN KHO (Inventory turnover ratio)
                    Hệ số này đánh giá các rủi ro khi lưu trữ hàng tồn kho của doanh nghiệp.
                   -  Hệ số hàng tồn kho thấp: Hàng tồn kho được lưu trữ trong thời gian dài, khả năng tiêu thụ chậm có thể gây hư hỏng, hết hạn sử dụng hoặc giảm giá trị làm ảnh hưởng đến lợi nhuận và tình hình tài chính của doanh nghiệp.
                   -  Hệ số hàng tồn kho cao: Hàng tồn kho ít, sản phẩm được tiêu thụ nhanh và vốn không bị ứ đọng ở hàng tồn kho. Tuy nhiên, để kết luận hệ số này tốt hay xấu thì doanh nghiệp cần xem xét đến đặc điểm ngành nghề kinh doanh và chính sách hàng tồn kho.
            
            3. Phân tích đòn bẩy tài chính
                    Để phân tích đòn bẩy tài chính doanh nghiệp cần sử dụng hệ số nợ (Debt to Equity Ratio) để biết được tỷ trọng nợ trong tổng nguồn vốn của doanh nghiệp.
                    Trên thực tế, rất khó để chúng ta đánh giá được tỷ lệ nợ như thế nào là hợp lý đối với doanh nghiệp. Bởi vì, tỷ lệ này phụ thuộc vào nhiều yếu tố như: hình thức doanh nghiệp, quy mô doanh nghiệp hay mục đích vay,…
                    Tuy nhiên, thông thường có thể đánh giá:
                    - Hệ số nợ thấp: Doanh nghiệp tài chính tốt không phụ thuộc vào vốn vay và có khả năng thanh toán nợ tốt. Tuy nhiên, điều này cũng giới hạn khả năng mở rộng kinh doanh của doanh nghiệp
                    - Hệ số nợ cao: Doanh nghiệp sử dụng vốn vay nhiều hơn vốn chủ sở hữu cho hoạt động kinh doanh. Điều này, có thể giúp doanh nghiệp tăng trưởng vượt bậc nhưng tiềm ẩn nhiều rủi ro khi trả nợ.
            
            4. Phân tích khả năng sinh lời
                    TỶ SUẤT LỢI NHUẬN SAU THUẾ TRÊN DOANH THU (Return On Sale - ROS)
                        Chỉ số này thể hiện cho chúng ta thấy: việc 1 đồng doanh thu thuần thì doanh nghiệp sẽ thu về bao nhiêu đồng lợi nhuận sau thuế.
                        Điều này giúp phản ánh hiệu quả trong việc quản lý chi phí của doanh nghiệp.
                        Doanh nghiệp nào có tỷ lệ ROS ổn định và cao hơn đối thủ là các doanh nghiệp có lợi thế cạnh tranh lớn và có hiệu quả quản trị chi phí tốt. Thậm chí đây còn là các doanh nghiệp hàng đầu trong lĩnh vực kinh doanh đó.
                        Tỷ suất lợi nhuận này phụ thuộc vào đặc điểm kinh tế, kỹ thuật của ngành kinh doanh và chiến lược cạnh tranh của doanh nghiệp.
                    TỶ SUẤT LỢI NHUẬN SAU THUẾ TRÊN TỔNG TÀI SẢN (Return On Asset - ROA)
                        Hệ số này giúp chúng ta phản ánh: 1 đồng tài sản tạo ra bao nhiêu đồng lợi nhuận sau thuế? Hay hiệu quả sử dụng tài sản của doanh nghiệp ra sao? 
                        Thông thường, ROA càng cao càng tốt.
                    Đặc biệt, đối với các doanh nghiệp trong ngành sản xuất cơ bản như sắt thép, giấy, hóa chất,… thì ROA là chỉ tiêu vô cùng quan trọng. Vì các doanh nghiệp này sử dụng tài sản dài hạn là máy móc, thiết bị,… để nâng cao tỷ suất lợi nhuận.
                    ROA cao cho thấy việc doanh nghiệp quản lý hiệu quả các chi phí khấu hao, chi phí đầu vào.
                    TỶ SUẤT LỢI NHUẬN SAU THUẾ TRÊN VỐN CHỦ SỞ HỮU (Return on Equity - ROE)
                        Hệ số này thể hiện mức lợi nhuận sau thuế thu được trên mỗi 1 đồng vốn chủ bỏ ra trong kỳ. 
                        ROE càng cao càng thể hiện hiệu quả trong việc sử dụng vốn chủ sở hữu.
                        Chỉ số này giúp chúng ta phản ánh tổng hợp các khía cạnh về trình độ quản trị tài chính, trình độ quản trị chi phí, trình độ quản trị tài sản, trình độ quản trị nguồn vốn của doanh nghiệp.
                    Dựa và ROE, chúng ta cũng có thể đánh giá liệu doanh nghiệp có lợi thế cạnh tranh hay không?
                Các doanh nghiệp có ROE cao (thường > 20%) và ổn định trong nhiều năm (kể cả khi thị trường rơi vào khó khăn) là các doanh nghiệp có lợi thế cạnh tranh bền vững.
                Tuy nhiên, ROE quá cao cũng không phải là điều tốt, mà có thể hoạt động kinh doanh của doanh nghiệp không có gì thay đổi, nhưng doanh nghiệp lại đang mua lại cổ phiếu quỹ hoặc doanh nghiệp này đang tách ra từ công ty mẹ khiến cho vốn cổ phần giảm, cho nên khiến ROE tăng.
                THU NHẬP MỘT CỔ PHẦN THƯỜNG (Earnings Per Share - EPS)
                Chỉ tiêu này giúp chúng ta phản ánh 1 cổ phần thường trong năm thu được bao nhiêu đồng lợi nhuận sau thuế? Hay còn gọi là chỉ số EPS.
                EPS càng cao có nghĩa là mỗi cổ phiếu mang lại một khoản lợi nhuận càng lớn. Đây là điều tích cực và hấp dẫn đối với các nhà đầu tư.
            5. Phân tích dòng tiền
                    DOANH THU THUẦN (Net Cash Flow from Operating Activities - CFO)
                        Tỷ lệ này giúp cho chúng ta biết doanh nghiệp nhận được bao nhiêu đồng trên 1 đồng doanh thu thuần. Mặc dù không có một con số cụ thể để tham chiếu, tuy nhiên rõ ràng là tỷ lệ này càng cao thì càng tốt. Và chúng ta cũng nên so sánh với dữ liệu quá khứ để phát hiện ra các sai sót khác.
                            CFO dương: Doanh nghiệp tạo ra lượng tiền dương từ hoạt động kinh doanh chính. Đây là một dấu hiệu tích cực.
                            CFO âm: Doanh nghiệp đang tiêu tốn tiền mặt trong hoạt động kinh doanh
                    TỶ SUẤT DÒNG TIỀN TỰ DO (Free Cash Flow to Equity - FCFE)
                        Tỷ suất này giúp chúng ta phản ánh được chất lượng dòng tiền của doanh nghiệp. Dòng tiền tự do phản ánh số tiền sẵn có nhằm sử dụng cho các hoạt động của doanh nghiệp.
                        Trong đó:
                            Dòng tiền tự do (Free Cashflow)	=	Lưu chuyển tiền thuần từ hợp đồng kinh doanh - Dòng tiền đầu tư cho tài sản cố định
                            Doanh nghiệp phải trừ đi Dòng tiền cho hoạt động đầu tư tài sản cố định, bởi vì dòng tiền đầu tư tài sản cố định được xem như là để duy trì lợi thế cạnh tranh và hiệu quả hoạt động cho doanh nghiệp.
                            Như vậy, dòng tiền tự do càng lớn, chứng tỏ tình hình tài chính của doanh nghiệp càng tích cực.
                    XU HƯỚNG CỦA DÒNG TIỀN
                        Để thực hiện phân tích xu hướng dòng tiền, số liệu dòng tiền của từng hoạt động sẽ được cộng dồn theo từng năm.
                        Mục đích của việc phân tích xu hướng của dòng tiền là để loại bỏ sự biến động về dòng tiền tại một thời điểm cụ thể. Ngoài ra, việc quan sát dòng tiền trong một giai đoạn dài sẽ giúp chúng ta xác định được doanh nghiệp đang trong giai đoạn nào của chu kỳ kinh doanh. Đây chính là yếu tố quan trọng để chúng ta đưa ra quyết định về việc có nên tài trợ vốn cho doanh nghiệp trong giai đoạn hiện tại hay không?
            Lưu ý khi phân tích báo cáo tài chính
                Một số lưu ý khi phân tích báo cáo tài chính:
                So sánh với kỳ đánh giá trước để xem xu hướng phát triển theo chiều ngang của doanh nghiệp.
                So sánh với đánh giá của các doanh nghiệp cùng ngành hoặc với trung bình của ngành để nhận định được điểm mạnh, điểm yếu của doanh nghiệp.
                Khi tính toán và phân tích các chỉ số, chúng ta cần quan tâm xem con số đó thể hiện tính chất thời điểm hay thời kỳ để từ đó có thể nhận xét đúng nhất về tình hình của doanh nghiệp. Ví du: Các chỉ số tài chính thuộc “Bảng Cân Đối Kế Toán” sẽ là các con số mang tính thời điểm; còn ở “Báo Cáo Kết Quả Kinh Doanh” sẽ mang tính thời kỳ.
            Trả về bản phân tích NGẮN GỌN trực tiếp không giải thích và comment, mở đầu câu trả lời dưới dạng như sau:
                ## 6. Phân tích các chỉ số cơ bản.
                        [Nội dung]
            
                '''
    respose = call_api_gemi(prompt= prompt_instruction)
    return respose

def check_valid_reports(infor, isBank = 'Không', isIndex = 'Không'):
    sections = ['BẢNG CÂN ĐỐI KẾ TOÁN', 'BÁO CÁO KẾT QUẢ HOẠT ĐỘNG KINH DOANH']
    result = ''
    for i, sec in enumerate(sections):
        result += sec + '\n'
        subsection = []
        if i == 0:
            if isBank ==  'CÓ':
                subsection = SUBSECTION_BALANCE_SHEET_FOR_BANK
            elif isIndex == 'CÓ':
                subsection == SUBSECTION_BALANCE_SHEET_FOR_INDEX
            else:
                subsection = SUBSECTION_BALANCE_SHEET
        elif i == 1:
            if isBank == 'CÓ':
                subsection = SUBSECTION_INCOME_STATEMENT_FOR_BANK
            elif isIndex == 'CÓ':
                subsection = SUBSECTION_INCOME_STATEMENT_FOR_INDEX
            else:
                subsection = SUBSECTION_INCOME_STATEMENT
        for sub in subsection:
            doc = (query_company_raw_text(company_name= infor[0], time= infor[2], section=sec, subsection= sub))
            for data in doc:
                result += data['table_structure'] + '\n' + data['raw_text'] + '\n' + "\n".join(map(str, data['pages']))
    result = normalize_for_prompt(result)
    prompt_check = f'''
        Bạn là một chuyên gia độc hiểu phân tích báo cáo tài chính.
        Dựa trên 2 quy định về cách lập bảng cân đối kế toán của VAS 21 và báo cáo kết quả hoạt động kinh doanh sau. Hãy xác định xem liệu doanh nghiệp đó có tuân theo khung có sẵn đó không.
        Lưu ý: các mục trong báo cáo có thể có tiêu đề, tên gọi khác trong quy định tuy nhiên có chức năng giống nhau và ý nghĩa giống nhau, hãy dựa vào ngữ nghĩa, kiến thức về tài chính để xác định chính xác và không cần theo thứ tự như 
        trong tài liệu quy định. Không cần phải khớp quá mức. 
        Hãy đưa ra nhận xét đầy đủ về các thông tin, chính xác và ngắn gọn bằng cách chỉ nêu nên những phần thật sự bị thiếu (các mục chỉ nằm trong hướng dẫn) hoặc bất thường.
        Bảng cân đối kế toán phải bao gồm các khoản mục chủ yếu sau đây :
            1. Tiền và các khoản tương đương tiền;
            2. Các khoản đầu tư tài chính ngắn hạn;
            3. Các khoản phải thu thương mại và phải thu khác;
            4. Hàng tồn kho;
            5. Tài sản ngắn hạn khác;
            6. Tài sản cố định hữu hình;
            7. Tài sản cố định vô hình;
            8. Các khoản đầu tư tài chính dài hạn;
            9. Chi phí xây dựng cơ bản dở dang;
            10. Tài sản dài hạn khác;
            11. Vay ngắn hạn;
            12. Các khoản phải trả thương mại và phải trả ngắn hạn khác;
            13. Thuế và các khoản phải nộp Nhà nước;
            14. Các khoản vay dài hạn và nợ phải trả dài hạn khác;
            15. Các khoản dự phòng;
            16. Phần sở hữu của cổ đông thiểu số;
            17. Vốn góp;
            18. Các khoản dự trữ;
            19. Lợi nhuận chưa phân phối.
        Báo cáo kết quả hoạt động kinh doanh phải bao gồm các khoản mục chủ yếu sau đây:
            1. Doanh thu bán hàng và cung cấp dịch vụ;
            2. Các khoản giảm trừ;
            3. Doanh thu thuần về bán hàng và cung cấp dịch vụ;
            4. Giá vốn hàng bán;
            5. Lợi nhuận gộp về bán hàng và cung cấp dịch vụ;
            6. Doanh thu hoạt động tài chính;
            7. Chi phí tài chính;
            8. Chi phí bán hàng;
            9. Chi phí quản lý doanh nghiệp;
            10. Thu nhập khác;
            11. Chi phí khác;
            12. Phần sở hữu trong lãi hoặc lỗ của công ty liên kết và liên doanh được kế toán theo phương pháp vốn chủ sở hữu (Trong Báo cáo kết quả hoạt động kinh doanh hợp nhất);
            13. Lợi nhuận từ hoạt động kinh doanh;
            14. Thuế thu nhập doanh nghiệp;
            15. Lợi nhuận sau thuế;
            16. Phần sở hữu của cổ đông thiểu số trong lãi hoặc lỗ sau thuế (Trong Báo cáo kết quả hoạt động kinh doanh hợp nhất);
            17. Lợi nhuận thuần trong kỳ.
        Dưới đây bảng cân đối kế toán và báo cáo kết quả hoạt động kinh doanh của doanh nghiệp: {result}
        Trả về thẳng trực tiếp bỏ qua phần giải thích giới thiệu mở đầu như sau:
        Sử dụng từ chuẩn mực kế toán https://docs.kreston.vn/vbpl/ke-toan/chuan-muc-ke-toan/vas-21/?fbclid=IwY2xjawNdNT1leHRuA2FlbQIxMABicmlkETFpaXZob3U2SmVVOUdweW5rAR7nOOYcBONlC5i3UIGChRHcbapRraCWP2J2q11HheBYd5wr3cII7baZW3BcqQ_aem_UC_uYedaDz6kVPcIOrItTQ
        nếu muốn trích dẫn nguồn
          **Bảng cân đối kế toán**
          [Nội dung]
          **Báo cáo kết quả hoạt động kinh doanh**
          [Nội dung]
    '''
    prompt_check_for_bank = f'''
        Dựa trên 2 quy định về cách lập bảng cân đối kế toán và báo cáo kết quả hoạt động kinh doanh dành cho NGÂN HÀNG của VAS sau. Hãy xác định xem liệu doanh nghiệp đó có tuân theo khung có sẵn đó không.
        ưu ý: các mục trong báo cáo có thể có tiêu đề, tên gọi khác trong quy định tuy nhiên có chức năng giống nhau và ý nghĩa giống nhau, hãy dựa vào ngữ nghĩa, kiến thức về tài chính để xác định chính xác và không cần theo thứ tự như 
        trong tài liệu quy định. Không cần phải khớp quá mức. 
        Hãy đưa ra nhận xét đầy đủ về các thông tin, chính xác và ngắn gọn bằng cách chỉ nêu nên những phần thật sự bị thiếu (các mục chỉ nằm trong hướng dẫn) hoặc bất thường.
            Ngoài các yêu cầu của chuẩn mực kế toán khác, Bảng cân đối kế toán hoặc Bản thuyết minh báo cáo tài chính của Ngân hàng phải trình bày tối thiểu các khoản mục tài sản và nợ phải trả sau đây:
            Khoản mục tài sản:
                - Tiền mặt, vàng bạc, đá quý;
                - Tiền gửi tại Ngân hàng Nhà nước;
                - Tín phiếu Kho bạc và các chứng chỉ có giá khác dùng tái chiết khấu với  Ngân hàng Nhà nước;
                - Trái phiếu Chính phủ và các chứng khoán khác được nắm giữ với mục đích thương mại;
                - Tiền gửi tại các Ngân hàng khác, cho vay và ứng trước cho các tổ chức tín dụng và các tổ chức tài chính tương tự khác;
                - Tiền gửi khác trên thị trường tiền tệ;
                - Cho vay và ứng trước cho khách hàng;
                - Chứng  khoán đầu tư;
                - Góp vốn đầu tư.
            Khoản mục nợ phải trả:
                - Tiền gửi của các ngân hàng và các tổ chức tương tự khác;
                - Tiền gửi từ thị trường tiền tệ;
                - Tiền gửi của khách hàng;
                - Chứng chỉ tiền gửi;
                - Thương phiếu, hối phiếu và các chứng chỉ nhận nợ;
                - Các khoản đi vay khác.
            
            Ngoài các yêu cầu của chuẩn mực kế toán khác, Báo cáo kết quả hoạt động kinh doanh hay Bản thuyết minh báo cáo tài chính của 
            Ngân hàng phải trình bày tối thiểu các khoản mục thu nhập, chi phí sau đây:
                - Thu nhập lãi và các khoản thu nhập tương tự;
                - Chi phí lãi và các chi phí tương tự;
                - Lãi được chia từ góp vốn và mua cổ phần;
                - Thu phí hoạt động dịch vụ;
                - Phí và chi phí hoa hồng;
                - Lãi hoặc lỗ thuần từ kinh doanh chứng khoán kinh doanh;
                - Lãi hoặc lỗ thuần từ kinh doanh chứng khoán đầu tư;
                - Lãi hoặc lỗ thuần hoạt động kinh doanh ngoại hối;
                - Thu nhập từ hoạt động khác;
                - Tổn thất khoản cho vay và ứng trước;
                - Chi phí quản lý; và
                - Chi phí hoạt động khác.
        Dưới đây bảng cân đối kế toán và báo cáo kết quả hoạt động kinh doanh của doanh nghiệp: {result}    
        Trả về thẳng trực tiếp bỏ qua phần giải thích giới thiệu mở đầu như sau:
        Lưu ý nội dung trả về hết sức ngắn gọn và logic để người đọc có thể nhìn thấy ngay.
        Sử dụng từ chuẩn mực kế toán https://docs.kreston.vn/vbpl/ke-toan/chuan-muc-ke-toan/vas-21/?fbclid=IwY2xjawNdNT1leHRuA2FlbQIxMABicmlkETFpaXZob3U2SmVVOUdweW5rAR7nOOYcBONlC5i3UIGChRHcbapRraCWP2J2q11HheBYd5wr3cII7baZW3BcqQ_aem_UC_uYedaDz6kVPcIOrItTQ
        nếu muốn trích dẫn nguồn.
          **Bảng cân đối kế toán**
          [Nội dung]
          **Báo cáo kết quả hoạt động kinh doanh**
          [Nội dung]
        
    '''
    print ("ĐỘ DÀI PROMPT: ", len(prompt_check))
    response = ''
    if isBank == 'CÓ':
        response = call_api_gemi(prompt = prompt_check_for_bank, temperture= 0)
    else:
        response = call_api_gemi(prompt= prompt_check, temperture= 0)
    return response

def check_valid_cash_flow(infor, isBank = 'Không', isIndex = 'Không'):
    sections = ['BÁO CÁO LƯU CHUYỂN TIỀN TỆ']
    result = ''
    for i, sec in enumerate(sections):
        result += sec + '\n'
        subsection = []
        if isIndex == 'CÓ':
            subsection = SUBSECTION_CASH_FLOW_FOR_INDEX
        subsection = SUBSECTION_CASH_FLOW
            
        for sub in subsection:
            doc = (query_company_raw_text(company_name= infor[0], time= infor[2], section=sec, subsection= sub))
            for data in doc:
                result += data['table_structure'] + '\n' + data['raw_text'] + '\n' + "\n".join(map(str, data['pages']))
                
    prompt_check = f'''
        Bạn là một chuyên gia độc hiểu phân tích báo cáo tài chính.
        Dựa trên một số mẫu lập báo cáo lưu chuyển tiền tệ khác nhau phù hợp với các lĩnh vực hoạt động khác nhau của doanh nghiệp hãy đưa nhận xét xem báo cáo lưu chuyển tiền tệ của doanh nghiệp này có theo một trong số mẫu nào dưới đây không.
        Lưu ý: các đầu mục có thể không theo thứ tự và tên gọi có thể khác nhau nhưng về mặt ý nghĩa tài chính là giống nhau. 
        BÁO CÁO LƯU CHUYỂN TIỀN TỆ MẪU 1 (PHƯƠNG PHÁP TRỰC TIẾP)
        Đơn vị tính: ………
        | Chỉ tiêu                                                                 | Mã số | Kỳ trước | Kỳ này |
        |-------------------------------------------------------------------------|:----:|:--------:|:------:|
        | **I. Lưu chuyển tiền từ hoạt động kinh doanh**                          |      |          |        |
        | Tiền thu từ bán hàng, cung cấp dịch vụ và doanh thu khác                |  01  |          |        |
        | Tiền chi trả cho người cung cấp hàng hóa và dịch vụ                     |  02  |          |        |
        | Tiền chi trả cho người lao động                                         |  03  |          |        |
        | Tiền chi trả lãi vay                                                    |  04  |          |        |
        | Tiền chi nộp thuế thu nhập doanh nghiệp                                 |  05  |          |        |
        | Tiền thu khác từ hoạt động kinh doanh                                   |  06  |          |        |
        | Tiền chi khác cho hoạt động kinh doanh                                  |  07  |          |        |
        | **Lưu chuyển tiền thuần từ hoạt động kinh doanh**                       |  20  |          |        |

        | **II. Lưu chuyển tiền từ hoạt động đầu tư**                             |      |          |        |
        | Tiền chi để mua sắm, xây dựng TSCĐ và tài sản dài hạn khác              |  21  |          |        |
        | Tiền thu từ thanh lý, nhượng bán TSCĐ và tài sản dài hạn khác           |  22  |          |        |
        | Tiền chi cho vay, mua các công cụ nợ của đơn vị khác                    |  23  |          |        |
        | Tiền thu hồi cho vay, bán lại các công cụ nợ của đơn vị khác            |  24  |          |        |
        | Tiền chi đầu tư góp vốn vào đơn vị khác                                 |  25  |          |        |
        | Tiền thu hồi đầu tư góp vốn vào đơn vị khác                             |  26  |          |        |
        | Tiền thu lãi cho vay, cổ tức và lợi nhuận được chia                     |  27  |          |        |
        | **Lưu chuyển tiền thuần từ hoạt động đầu tư**                           |  30  |          |        |

        | **III. Lưu chuyển tiền từ hoạt động tài chính**                         |      |          |        |
        | Tiền thu từ phát hành cổ phiếu, nhận vốn góp chủ sở hữu                 |  31  |          |        |
        | Tiền chi trả vốn góp cho chủ sở hữu, mua lại cổ phiếu đã phát hành      |  32  |          |        |
        | Tiền vay ngắn hạn, dài hạn nhận được                                    |  33  |          |        |
        | Tiền chi trả nợ gốc vay                                                 |  34  |          |        |
        | Tiền chi trả nợ thuê tài chính                                          |  35  |          |        |
        | Cổ tức, lợi nhuận đã trả cho chủ sở hữu                                 |  36  |          |        |
        | **Lưu chuyển tiền thuần từ hoạt động tài chính**                        |  40  |          |        |

        | **Lưu chuyển tiền thuần trong kỳ (20 + 30 + 40)**                        |  50  |          |        |
        | Tiền và tương đương tiền đầu kỳ                                         |  60  |          |        |
        | Ảnh hưởng của thay đổi tỷ giá hối đoái                                  |  61  |          |        |
        | **Tiền và tương đương tiền cuối kỳ (50 + 60 + 61)**                     |  70  |          |        |

        BÁO CÁO LƯU CHUYỂN TIỀN TỆ MẪU 2 (PHƯƠNG PHÁP GIÁN TIẾP)
        Đơn vị tính: ………

        | Chỉ tiêu                                                                                                   | Mã số | Kỳ trước | Kỳ này |
        |------------------------------------------------------------------------------------------------------------|:----:|:--------:|:------:|
        | **I. Lưu chuyển tiền từ hoạt động kinh doanh**                                                             |      |          |        |
        | Lợi nhuận trước thuế                                                                                       |  01  |          |        |
        | **Điều chỉnh cho các khoản:**                                                                              |      |          |        |
        | - Khấu hao TSCĐ                                                                                             |  02  |          |        |
        | - Các khoản dự phòng                                                                                       |  03  |          |        |
        | - Lãi, lỗ chênh lệch tỷ giá hối đoái chưa thực hiện                                                        |  04  |          |        |
        | - Lãi, lỗ từ hoạt động đầu tư                                                                              |  05  |          |        |
        | - Chi phí lãi vay                                                                                          |  06  |          |        |
        | **Lợi nhuận từ hoạt động kinh doanh trước thay đổi vốn lưu động**                                         |  08  |          |        |
        | - Tăng, giảm các khoản phải thu                                                                           |  09  |          |        |
        | - Tăng, giảm hàng tồn kho                                                                                  |  10  |          |        |
        | - Tăng, giảm các khoản phải trả (không kể lãi vay phải trả, thuế TNDN phải nộp)                            |  11  |          |        |
        | - Tăng, giảm chi phí trả trước                                                                             |  12  |          |        |
        | - Tiền lãi vay đã trả                                                                                      |  13  |          |        |
        | - Thuế thu nhập đã nộp                                                                                    |  14  |          |        |
        | - Tiền thu khác từ hoạt động kinh doanh                                                                    |  15  |          |        |
        | - Tiền chi khác từ hoạt động kinh doanh                                                                    |  16  |          |        |
        | **Lưu chuyển tiền thuần từ hoạt động kinh doanh**                                                          |  20  |          |        |

        | **II. Lưu chuyển tiền từ hoạt động đầu tư**                                                                |      |          |        |
        | Tiền chi để mua sắm, xây dựng TSCĐ và tài sản dài hạn khác                                                 |  21  |          |        |
        | Tiền thu từ thanh lý, nhượng bán TSCĐ và tài sản dài hạn khác                                              |  22  |          |        |
        | Tiền chi cho vay, mua các công cụ nợ của đơn vị khác                                                       |  23  |          |        |
        | Tiền thu hồi cho vay, bán lại các công cụ nợ của đơn vị khác                                               |  24  |          |        |
        | Tiền chi đầu tư góp vốn vào đơn vị khác                                                                    |  25  |          |        |
        | Tiền thu hồi đầu tư góp vốn vào đơn vị khác                                                                |  26  |          |        |
        | Tiền thu lãi cho vay, cổ tức và lợi nhuận được chia                                                        |  27  |          |        |
        | **Lưu chuyển tiền thuần từ hoạt động đầu tư**                                                              |  30  |          |        |

        | **III. Lưu chuyển tiền từ hoạt động tài chính**                                                            |      |          |        |
        | Tiền thu từ phát hành cổ phiếu, nhận vốn góp của chủ sở hữu                                                |  31  |          |        |
        | Tiền chi trả vốn góp cho chủ sở hữu, mua lại cổ phiếu đã phát hành                                         |  32  |          |        |
        | Tiền vay ngắn hạn, dài hạn nhận được                                                                       |  33  |          |        |
        | Tiền chi trả nợ gốc vay                                                                                    |  34  |          |        |
        | Tiền chi trả nợ thuê tài chính                                                                             |  35  |          |        |
        | Cổ tức, lợi nhuận đã trả cho chủ sở hữu                                                                    |  36  |          |        |
        | **Lưu chuyển tiền thuần từ hoạt động tài chính**                                                           |  40  |          |        |

        | **Lưu chuyển tiền thuần trong kỳ (20 + 30 + 40)**                                                          |  50  |          |        |
        | Tiền và tương đương tiền đầu kỳ                                                                            |  60  |          |        |
        | Ảnh hưởng của thay đổi tỷ giá hối đoái quy đổi ngoại tệ                                                    |  61  |          |        |
        | **Tiền và tương đương tiền cuối kỳ (50 + 60 + 61)**                                                        |  70  |          |        |

        BÁO CÁO LƯU CHUYỂN TIỀN TỆ MẪU 3 (PHƯƠNG PHÁP TRỰC TIẾP - TỔ CHỨC TÍN DỤNG)
        Đơn vị tính: ………

        | Chỉ tiêu                                                                                                  | Mã số | Kỳ trước | Kỳ này |
        |-----------------------------------------------------------------------------------------------------------|:----:|:--------:|:------:|
        | **I. Lưu chuyển tiền từ hoạt động kinh doanh**                                                            |      |          |        |
        | Tiền chi cho vay                                                                                          |  01  |          |        |
        | Tiền thu hồi cho vay                                                                                      |  02  |          |        |
        | Tiền thu từ hoạt động huy động vốn                                                                        |  03  |          |        |
        | Trả lại tiền huy động vốn                                                                                 |  04  |          |        |
        | Nhận tiền gửi và trả lại tiền gửi cho ngân hàng, tổ chức tín dụng và tổ chức tài chính khác               |  05  |          |        |
        | Gửi tiền và nhận lại tiền gửi tại ngân hàng, tổ chức tín dụng và tổ chức tài chính khác                   |  06  |          |        |
        | Thu và chi các loại phí, hoa hồng dịch vụ                                                                 |  07  |          |        |
        | Tiền lãi cho vay, lãi tiền gửi đã thu                                                                     |  08  |          |        |
        | Tiền lãi đi vay, nhận tiền gửi đã trả                                                                     |  09  |          |        |
        | Lãi, lỗ mua bán ngoại tệ                                                                                  |  10  |          |        |
        | Tiền thu vào hoặc chi ra về mua bán chứng khoán ở doanh nghiệp kinh doanh chứng khoán                     |  11  |          |        |
        | Tiền chi mua chứng khoán vì mục đích thương mại                                                            |  12  |          |        |
        | Tiền thu từ bán chứng khoán vì mục đích thương mại                                                         |  13  |          |        |
        | Thu nợ khó đòi đã xóa sổ                                                                                  |  14  |          |        |
        | Tiền thu khác từ hoạt động kinh doanh                                                                     |  15  |          |        |
        | Tiền chi khác từ hoạt động kinh doanh                                                                     |  16  |          |        |
        | **Lưu chuyển tiền thuần từ hoạt động kinh doanh**                                                         |  20  |          |        |

        | **II. Lưu chuyển tiền từ hoạt động đầu tư**                                                               |      |          |        |
        | Tiền chi để mua sắm, xây dựng TSCĐ và tài sản dài hạn khác                                                |  21  |          |        |
        | Tiền thu từ thanh lý, nhượng bán TSCĐ và tài sản dài hạn khác                                             |  22  |          |        |
        | Tiền chi mua các công cụ nợ của đơn vị khác vì mục đích đầu tư                                            |  23  |          |        |
        | Tiền thu từ bán lại các công cụ nợ của đơn vị khác vì mục đích đầu tư                                     |  24  |          |        |
        | Tiền chi đầu tư góp vốn vào đơn vị khác                                                                   |  25  |          |        |
        | Tiền thu hồi đầu tư góp vốn vào đơn vị khác                                                               |  26  |          |        |
        | Tiền thu cổ tức và lợi nhuận được chia                                                                    |  27  |          |        |
        | Tiền thu lãi của hoạt động đầu tư                                                                         |  28  |          |        |
        | **Lưu chuyển tiền thuần từ hoạt động đầu tư**                                                             |  30  |          |        |

        | **III. Lưu chuyển tiền từ hoạt động tài chính**                                                           |      |          |        |
        | Tiền thu từ phát hành cổ phiếu, nhận vốn góp của chủ sở hữu                                               |  31  |          |        |
        | Tiền chi trả vốn góp cho các chủ sở hữu, mua lại cổ phiếu đã phát hành                                    |  32  |          |        |
        | Tiền vay ngắn hạn, dài hạn nhận được                                                                      |  33  |          |        |
        | Tiền chi trả nợ gốc vay                                                                                   |  34  |          |        |
        | Tiền chi trả nợ thuê tài chính                                                                            |  35  |          |        |
        | Cổ tức, lợi nhuận đã trả cho chủ sở hữu                                                                   |  36  |          |        |
        | **Lưu chuyển tiền thuần từ hoạt động tài chính**                                                          |  40  |          |        |

        | **Lưu chuyển tiền thuần trong kỳ (20 + 30 + 40)**                                                         |  50  |          |        |
        | Tiền và tương đương tiền đầu kỳ                                                                           |  60  |          |        |
        | Ảnh hưởng của thay đổi tỷ giá hối đoái quy đổi ngoại tệ                                                   |  61  |          |        |
        | **Tiền và tương đương tiền cuối kỳ (50 + 60 + 61)**                                                       |  70  |          |        |
    
    Dưới đây là báo cáo lưu chuyển tiền tệ của doanh nghiệp {result}.
    Hãy nhận xét ngắn gọn xem báo cáo đó có đúng theo một mẫu nào đó không, thừa thiếu phần nào. Trả về thẳng trực tiếp không giải thích.
    
    '''
    response = call_api_gemi(prompt= prompt_check, temperture= 0)
    return response


def summary_section(temp_path):
    path_to_md, infor = get_database(input_model='all-MiniLM-L6-v2',temp_path = temp_path, is_graph = True)
    isBank = "KHÔNG"
    isIndex = "KHÔNG"
    if infor[3] == "Ngân hàng" or infor == "NGÂN HÀNG":
        isBank = "CÓ"
    if infor[3] == 'Chứng khoán':
        isIndex = "CÓ"
    prompt_find_note = f"""
        Hãy giúp tôi những key_word để tìm các đoạn tài liệu trong bản thuyết minh báo cáo tài chính của một doanh nghiệp liên quan đến
        bảng cẩn đối kế toán, báo cáo kết quả hoạt động kinh doanh,
        và báo cáo lưu chuyển tiền tệ.
        Để phục vụ cho việc tìm kiếm thông tin trong 1 bản thuyết minh báo cáo tài chính cả trăm trang dễ dàng hơn chính xác hơn,
        những key_word đó sẽ phù hợp với từ bản tương ứng nhắm mục đích lấy thêm thông tin để phục vụ việc phân tích 1 trong 3 bản báo cáo kia, dựa trên hướng dẫn sau:
        Hướng dẫn cách đọc thuyết minh báo cáo tài chính
                - Mục đích của việc đọc thuyết minh báo cáo tài chính là để hiểu rõ thông tin về ngành nghề,
                hoạt động của doanh nghiệp, kỳ kế toán, đơn vị tiền tệ, chuẩn mực kế toán được áp dụng, cũng như chi tiết các số liệu liên quan đến các báo cáo tài chính khác.
                - Thuyết minh còn cung cấp thêm các thông tin quan trọng như nợ tiềm tàng, các cam kết, sự kiện sau ngày kết thúc kỳ kế toán,
                và thông tin về các bên liên quan. Những thông tin này rất quan trọng và cần được các nhà quản trị và nhà đầu tư xem xét kỹ lưỡng.
                - Sau khi đọc thuyết minh, nhà quản trị cần có phân tích chi tiết hơn về các số liệu kế toán trong năm, so sánh với các năm trước
                và đối thủ cạnh tranh, hoặc với các chỉ số trung bình ngành để có cái nhìn rõ ràng hơn về tình hình tài chính của doanh nghiệp.
        trả về dưới dạng sau:
            BẢNG CÂN ĐỐI KẾ TOÁN: key_word1, key_word2, ... ; BÁO CÁO KẾT QUẢ HOẠT ĐỘNG KINH DOANH: key_word1, key_word2, ...; BÁO CÁO LƯU CHUYỂN TIỀN TỆ: key_word1, key_word2, ...
        Lưu ý không giải thích gì thêm chỉ trả về đúng định dạng như yêu cầu và số lượng keyword tối đa cho mỗi bảng là 10 vì vậy hãy sử dụng những key word có liên quan nhất.
        Lĩnh vực của doanh nghiệp {isBank} là Ngân hàng
        Lĩnh vực của doanh nghiệp {isIndex} là Chứng khoán
    """
    anwser_llm = call_api_gemi(prompt_find_note)
    features = [x.strip() for x in anwser_llm.split(";") if x.strip()]
    
    f = features[0]
    f2 = features[1]
    f3 = features[2]
    key_words = [sub.strip() for sub in  f[f.find(':') + 1 : ].split(',') if sub.strip()]
    key_words_income_statement = [sub.strip() for sub in  f2[f2.find(':') + 1 : ].split(',') if sub.strip()]
    key_words_cash_flow = [sub.strip() for sub in  f3[f3.find(':') + 1 : ].split(',') if sub.strip()]
    summary_fs = ''
    summary_is = ''
    summary_cf = ''
    summary_info = ''
    finacial_radio = ''
    analysis_ratio_text = ''
    if isBank == 'CÓ':
        summary_fs = summary_finacial_statement(subsection = SUBSECTION_BALANCE_SHEET_FOR_BANK, temp_path= temp_path, infor= infor, key_words= key_words, isBank='CÓ')
        summary_is = summary_income_statement(subsection = SUBSECTION_INCOME_STATEMENT_FOR_BANK, temp_path= temp_path, infor= infor, key_words= key_words_income_statement, isBank='CÓ')
        summary_cf = summary_cash_flow(subsection = SUBSECTION_CASH_FLOW, temp_path = temp_path, infor= infor, key_words=key_words_cash_flow, isBank= 'CÓ')
        finacial_radio = cal_financial_radio(infor=infor, isBank='CÓ')
        summary_info = summary_info_company(infor) + '\n **Kiểm tra tính chính xác của các thông tin trong báo cáo tài chính** \n' + \
        check_valid_reports(infor= infor, isBank= 'CÓ') + '\n **Báo cáo lưu chuyển tiền tệ:**' + check_valid_cash_flow(infor= infor, isBank = ' Có')
        analysis_ratio_text = analysis_ratio(finacial_radio, isBank='CÓ')
        
    elif isIndex == 'CÓ':
        summary_fs = summary_finacial_statement(subsection = SUBSECTION_BALANCE_SHEET_FOR_INDEX, temp_path= temp_path, infor= infor, key_words= key_words, isIndex='CÓ')
        summary_is = summary_income_statement(subsection = SUBSECTION_BALANCE_SHEET_FOR_INDEX, temp_path= temp_path, infor= infor, key_words= key_words_income_statement,isIndex='CÓ')
        summary_cf = summary_cash_flow(subsection = SUBSECTION_CASH_FLOW_FOR_INDEX, temp_path = temp_path, infor= infor, key_words=key_words_cash_flow,isIndex='CÓ')
        finacial_radio = cal_financial_radio(infor=infor,isIndex='CÓ')
        summary_info = summary_info_company(infor) + '\n **Kiểm tra tính chính xác của các thông tin trong báo cáo tài chính** \n' + \
        check_valid_reports(infor= infor, isIndex= 'CÓ')+  '\n **Báo cáo lưu chuyển tiền tệ:**' + check_valid_cash_flow(infor= infor, isIndex = ' Có')
        analysis_ratio_text = analysis_ratio(finacial_radio,isIndex='CÓ')
        
        
    else:
        summary_fs = summary_finacial_statement(subsection=['TÀI SẢN NGẮN HẠN', 'TÀI SẢN DÀI HẠN', 'NỢ PHẢI TRẢ', 'VỐN CHỦ SỞ HỮU'], temp_path= temp_path, infor= infor, key_words= key_words)
        summary_is = summary_income_statement(subsection=['DOANH THU BÁN HÀNG VÀ CUNG CẤP DỊCH VỤ', 'DOANH THU HOẠT ĐỘNG TÀI CHÍNH', 'THU NHẬP KHÁC'], temp_path= temp_path, infor= infor, key_words= key_words_income_statement)
        summary_cf = summary_cash_flow(subsection=['LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG KINH DOANH', 'LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG ĐẦU TƯ', 'LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG TÀI CHÍNH'], temp_path = temp_path, infor= infor, key_words=key_words_cash_flow)
        finacial_radio = cal_financial_radio(infor=infor)
        summary_info = summary_info_company(infor) + '\n **Kiểm tra tính chính xác của các thông tin trong báo cáo tài chính** \n' + \
        check_valid_reports(infor= infor) + '\n **Báo cáo lưu chuyển tiền tệ:**  \n' + check_valid_cash_flow(infor= infor)
        analysis_ratio_text = analysis_ratio(finacial_radio)
        
    filename = 'files_database/summaries/summary.md'
    content = summary_info + '\n' + summary_fs + '\n' + summary_is + "\n" + summary_cf + '\n'  \
    + finacial_radio + '\n' + analysis_ratio_text  
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
        
    return save_content_to_pdf(content = content)
    
    # print(finacial_radio)
def save_content_to_pdf(content: str):
    base_dir = os.path.join(os.getcwd(), "files_database", "summaries")
    os.makedirs(base_dir, exist_ok=True)

    rand_id = random.randint(100000, 999999)
    pdf_path = os.path.join(base_dir, f"out_{rand_id}.pdf")

    # Markdown -> HTML
    html_content = markdown.markdown(content, extensions=['tables'])

    # CSS để format PDF
    css = CSS(string='''
        @page { size: A4; margin: 2cm; }
        body { font-family: Arial, sans-serif; font-size: 12pt; line-height: 1.5; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #333; padding: 5px; text-align: left; }
        th { background-color: #f0f0f0; }
    ''')

    # HTML -> PDF
    HTML(string=html_content).write_pdf(pdf_path, stylesheets=[css])

    print(f"✅ PDF đã được lưu tại: {pdf_path}")
    return pdf_path