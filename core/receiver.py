from core.docx_database_creater import create_database
from core.csv_database_creater import create_database_for_csv
from core.pdf_database_creater import create_database_for_pdf
from core.LLama_parse import pdf_to_md
from core.pdf_database_creater import keyword_search
from core.graph_query_graph import query_company_raw_text, query_thuyet_minh_raw_text, query_raw_text
from core.call_api_llm import call_api_gemi

# from docx_database_creater import create_database
# from csv_database_creater import create_database_for_csv
# from pdf_database_creater import create_database_for_pdf
# from LLama_parse import pdf_to_md
# from pdf_database_creater import keyword_search
# from graph_query_graph import query_company_raw_text, query_thuyet_minh_raw_text
# from call_api_llm import call_api_gemi


from sentence_transformers import SentenceTransformer
import os
from rank_bm25 import BM25Okapi
#read input file
def get_input_path() -> str:
    try:
        base_dir = os.path.dirname(__file__)
        input_path = os.path.abspath(os.path.join(base_dir, '..', '000000014601738_VI_BaoCaoTaiChinh_KiemToan_2024_HopNhat_14032025110908.docx'))
        return input_path
    
    except Exception as e:
        print('cant locate docx file')
        print(f'error: {e}')

def get_doc_from_notes_by_key_word(key_word, infor, temp_path):
    notes_raw_text = ''
    similar_k = []
    notes_infor = ''
    notes_page = ''
    notes = query_thuyet_minh_raw_text(company_name= infor[0], time= infor[2])
    for data in notes:
        notes_raw_text += data['raw_text'] + '\n'
        notes_page += "\n".join(map(str, data['pages']))
    notes_doc = find_information(infor_question= key_word, k=10, temp_path= temp_path, content = notes_raw_text)
    for i in range(len(key_word)):
        similar_k += retrieve(query=key_word[i] ,top_k=3, semantic_results=notes_doc[i], input_path = '', content= notes_raw_text)    
    similar_k = remove_same_content(similar_k)
    for i, k in enumerate(similar_k):
        notes_infor += f"Thông tin {i} trong Thuyết minh báo cáo tài chính \n " + f"{k['content']}" + "\n"  
    return notes_infor
#get vector database and metadatas
def get_database(input_model='all-MiniLM-L6-v2',temp_path=None, content = None, is_graph = False) -> tuple:
    if temp_path is None:
        input_path = get_input_path()
    input_path = temp_path
    
    #checking file type
    file_ext = os.path.splitext(input_path)[-1].lower()

    #get vector embedding for csv
    if file_ext == '.csv':
        try:
            index, metadatas = create_database_for_csv(input_path=input_path, embedding_model=input_model)
            return index, metadatas

        except Exception as e:
            print('cant get database for csv file')
            print(f'error: {e}')
            
    elif file_ext == '.pdf' or file_ext == ".png" or file_ext == ".jpg":
        try:
            if is_graph is True:
                print('đang tạo database')
                path_to_md, infor = pdf_to_md(input_path,file_ext)
                return  path_to_md, infor
            else:
                path_to_md, infor = pdf_to_md(input_path,file_ext)
                index, metadatas = create_database_for_pdf(input_path = path_to_md, embedding_model=input_model, content=content)
                return index, metadatas
        
        except Exception as e:
            print('cant get database for markdown file')
            print(f'error: {e}')

    #get vector embedding for docx
    else:
        try:
            index, metadatas = create_database(input_path=input_path, input_model=input_model)
            return index, metadatas

        except Exception as e:
            print('cant get database for docx file')
            print(f'error: {e}')
    print("None")

#get user prompt
def get_user_question() -> str:
    user_question = input('What do you want to know: ')
    return user_question

#embedd user question into a vector
def get_user_question_embedding(input_model='all-MiniLM-L6-v2', user_question = '') -> tuple:
    user_question = user_question
    model = SentenceTransformer(input_model)
    user_question_embeddings = model.encode([user_question])
    return user_question, user_question_embeddings[0]

def find_information_by_graph(temp_path = None, user_question = ''):
    path_to_md, infor = get_database(input_model='all-MiniLM-L6-v2',temp_path = temp_path, is_graph = True)
    # summary_section("BẢNG CÂN ĐỐI KẾ TOÁN",subsection=['TÀI SẢN NGẮN HẠN','TÀI SẢN DÀI HẠN','NỢ PHẢI TRẢ', 'VỐN CHỦ SỞ HỮU'], infor= infor, temp_path= temp_path)
    isBank = "KHÔNG"
    isIndex = "KHÔNG"
    if infor[3] == "Ngân hàng" or infor == "NGÂN HÀNG":
        isBank = "CÓ"
    if infor[3] == 'Chứng khoán':
        isIndex = "CÓ"
    prompt_requery_by_graph = f""" 
            Hãy dựa vào câu hỏi của người dùng xác định xem câu hỏi của người dùng sử dụng đến thông tin nào trong
            mục và mục con của chúng trong báo cáo tài chính. Các mục và mục con đó chỉ có thể là các mục sau 
            LƯU Ý CHỈ LẤY NHỮNG MỤC THẬT SỰ QUAN TRỌNG VÀ CẦN THIẾT vì những thông tin đó dài và để đưa vào prompt cho LLM chỉ tối đa: 
                Nếu có 1 mục lớn: không giới hạn mục con.
                Nếu có 2 mục lớn: tối đa mỗi mục 3 mục con.
                Nếu có 3,4 mục lớn: tối đa 1 mục lớn có 2 mục con và các mục còn lại 1 mục con.
            
            Đối với doanh nghiệp KHÔNG phải ngân hàng.
                0. Giới thiệu:
                    - Các thông tin từ ở phần trên báo cáo bao gồm cả BÁO CÁO CỦA BAN GIÁM ĐỐC, BÁO CÁO SOÁT XÉT BÁO CÁO TÀI CHÍNH,
                    BÁO CÁO KIỂM TOÁN nếu có.
                
                1. BẢNG CÂN ĐỐI KẾ TOÁN
                    1.1 TÀI SẢN NGẮN HẠN
                    1.2 TÀI SẢN DÀI HẠN
                    1.3 NỢ PHẢI TRẢ
                    1.4 VỐN CHỦ SỞ HỮU
                    
                2. BÁO CÁO KẾT QUẢ HOẠT ĐỘNG KINH DOANH
                    2.1 DOANH THU BÁN HÀNG VÀ CUNG CẤP DỊCH VỤ 
                        - gồm các mục như: 1. Doanh thu bán hàng và cung cấp dịch vụ	
                                        2. Các khoản giảm trừ doanh thu
                                        3. Doanh thu thuần về bán hàng và cung cấp dịch vụ (10= 01-02)	
                                        4. Giá vốn hàng bán	
                                        5. Lợi nhuận gộp về bán hàng và cung cấp dịch vụ (20=10 - 11)	
                        - Hoặc các mục có tên và ý nghĩa tương tự có thể có.
                    2.1 DOANH THU HOẠT ĐỘNG TÀI CHÍNH
                        - gồm các mục tiếp tục theo sau đó như: 6. Doanh thu hoạt động tài chính
                                                        7. Chi phí tài chính
                                                        - Trong đó: Chi phí lãi vay 
                                                        8. Chi phí bán hàng
                                                        9. Chi phí quản lý doanh nghiệp
                                                        10 Lợi nhuận thuần từ hoạt động kinh doanh
                                                        (30 = 20 + (21 - 22) - (25 + 26))
                        - Hoặc các mục có tên và ý nghĩa tương tự có thể có.
                                                        
                    2.2 THU NHẬP KHÁC
                        - gồm toàn bộ những mục còn lại như:
                                                11. Thu nhập khác
                                                12. Chi phí khác
                                                13. Lợi nhuận khác (40 = 31 - 32)
                                                14. Tổng lợi nhuận kế toán trước thuế (50 = 30 + 40)
                                                15. Chi phí thuế TNDN hiện hành
                                                16. Chi phí thuế TNDN hoãn lại
                                                17. Lợi nhuận sau thuế thu nhập doanh nghiệp (60=50 – 51 - 52)
                                                18. Lãi cơ bản trên cổ phiếu (*)
                                                19. Lãi suy giảm trên cổ phiếu (*)
                        - Các thông tin về LỢI NHUẬN sẽ nằm ở phần này 
                    
                3. BÁO CÁO LƯU CHUYỂN TIỀN TỆ
                    3.1 LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG KINH DOANH
                    3.2 LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG ĐẦU TƯ
                    3.3 LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG TÀI CHÍNH
                
                4. THUYẾT MINH BÁO CÁO TÀI CHÍNH
                
                      
            Đối với doanh nghiệp NGÂN HÀNG.
                0. Giới thiệu:
                    - Các thông tin từ ở phần trên báo cáo bao gồm cả BÁO CÁO CỦA BAN GIÁM ĐỐC, BÁO CÁO SOÁT XÉT BÁO CÁO TÀI CHÍNH,
                    BÁO CÁO KIỂM TOÁN nếu có.
            
                1. BẢNG CÂN ĐỐI KẾ TOÁN 
                    Tại đây sẽ trình bày các chuẩn mực kể toán và tối thiệu các khoản mục sau:
                     Khoản mục tài sản:
                        Tiền mặt, vàng bạc, đá quý;
                        Tiền gửi tại Ngân hàng Nhà nước;
                        Tín phiếu Kho bạc và các chứng chỉ có giá khác dùng tái chiết khấu với  Ngân hàng Nhà nước;
                        Trái phiếu Chính phủ và các chứng khoán khác được nắm giữ với mục đích thương mại;
                        Tiền gửi tại các Ngân hàng khác, cho vay và ứng trước cho các tổ chức tín dụng và các tổ chức tài chính tương tự khác;
                        Tiền gửi khác trên thị trường tiền tệ;
                        Cho vay và ứng trước cho khách hàng;
                        Chứng  khoán đầu tư;
                        Góp vốn đầu tư.
                     Khoản mục nợ phải trả:
                        Tiền gửi của các ngân hàng và các tổ chức tương tự khác;
                        Tiền gửi từ thị trường tiền tệ;
                        Tiền gửi của khách hàng;
                        Chứng chỉ tiền gửi;
                        Thương phiếu, hối phiếu và các chứng chỉ nhận nợ;
                        Các khoản đi vay khác.
                    Các khoản mục đó được chia vào các phần con như sau:
                    1.1 TÀI SẢN
                    1.2 TÀI SẢN CỐ ĐỊNH
                    1.3 NỢ PHẢI TRẢ
                    1.4 VỐN CHỦ SỞ HỮU
                    1.5 CHỈ TIÊU NGOÀI
                        - đây là mục chưa thông tin về các chỉ tiêu ngoài báo cáo tình hình tài chính
                    
                2. BÁO CÁO KẾT QUẢ HOẠT ĐỘNG KINH DOANH
                    Tại đây sẽ gồm các chuẩn mực kế toán khác và các mục tối thiểu như:
                    Thu nhập lãi và các khoản thu nhập tương tự;
                    Chi phí lãi và các chi phí tương tự;
                    Lãi được chia từ góp vốn và mua cổ phần;
                    Thu phí hoạt động dịch vụ;
                    Phí và chi phí hoa hồng;
                    Lãi hoặc lỗ thuần từ kinh doanh chứng khoán kinh doanh;
                    Lãi hoặc lỗ thuần từ kinh doanh chứng khoán đầu tư;
                    Lãi hoặc lỗ thuần hoạt động kinh doanh ngoại hối;
                    Thu nhập từ hoạt động khác;
                    Tổn thất khoản cho vay và ứng trước;
                    Chi phí quản lý; và
                    Chi phí hoạt động khác.
                    đượ chia làm các phần con chính như sau:
                    
                    2.1 THU NHẬP LÃI VÀ CÁC KHOẢN
                        - Gồm các khoản bắt đầu của báo cáo kết quả hoạt động kinh doanh như: 1. Thu nhập lãi và các khoản thu nhập tương tự,
                        2. Chi phí lãi và các chi phí tương tự, I Thu nhập lãi thuần, 3. Thu nhập từ hoạt động dịch vụ,4. Chi phí hoạt động dịch vụ,
                        II Lãi thuần từ hoạt động dịch vụ, III 	Lãi/(lỗ) thuần từ hoạt động kinh doanh ngoại hối,
                        IV Lãi/(lỗ) thuần từ mua bán chứng khoán kinh doanh/ đầu tư và các khoản tương đương có thể có.
                    2.2 THU NHẬP TỪ HOẠT ĐỘNG KHÁC
                        - Các khoản tiếp tục như: 5. Thu nhập từ hoạt động khác, 6. Chi phí hoạt động khác,
                        VIII. Lãi thuần từ hoạt động khác 	VII Thu nhập từ góp vốn, mua cổ phần, VIII	Chi phí hoạt động,
                        IX	Lợi nhuận thuần từ hoạt động kinh doanh trước chi phí dự phòng rủi ro tín dụng,
                        X	Chi phí dự phòng rủi ro tín dụng, XI	Tổng lợi nhuận trước thuế. Và các khoảng tương tự có thể có.
                    2.3 CHI PHÍ THUẾ

                        - Gồm các khoản còn lại: 7	Chi phí thuế thu nhập doanh nghiệp hiện hành, 8	Chi phí thuế thu nhập doanh nghiệp hoãn lại, XII	Chi phí thuế thu nhập doanh nghiệp,
                        XIII	Lợi nhuận sau thuế, XV	Lãi cơ bản trên cổ phiếu (đồng/cổ phiếu) và các khoản tương đương.
                        - Các thông tin về LỢI NHUẬN sẽ nằm ở phần này 
                        
                3. BÁO CÁO LƯU CHUYỂN TIỀN TỆ
                    3.1 LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG KINH DOANH
                    3.2 LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG ĐẦU TƯ
                    3.3 LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG TÀI CHÍNH
                    
                4. THUYẾT MINH BÁO CÁO TÀI CHÍNH
                

            Đối với doanh nghiệp là công ty CHỨNG KHOÁN:
                0. Giới thiệu:
                    - Các thông tin từ ở phần trên báo cáo bao gồm cả BÁO CÁO CỦA BAN GIÁM ĐỐC, BÁO CÁO SOÁT XÉT BÁO CÁO TÀI CHÍNH,
                    BÁO CÁO KIỂM TOÁN nếu có.
            
                1. BẢNG CÂN ĐỐI KẾ TOÁN
                    1.1 TÀI SẢN NGẮN HẠN
                    1.2 TÀI SẢN DÀI HẠN
                    1.3 NỢ PHẢI TRẢ
                    1.4 VỐN CHỦ SỞ HỮU
                    1.5 TÀI SẢN CỦA CÔNG TY CHỨNG KHOÁN
                        - gồm các thông tin như hoặc các thông tin liên quan tương tự:
                        1. Nợ khó đòi đã xử lý                                                                                      
                        2. Cổ phiếu đang lưu hành (số lượng)                                                                                                    
                        3. Tài sản tài chính niêm yết đăng ký giao dịch tại Tổng Công ty Lưu ký và Bù trừ chứng khoán Việt Nam ("VSDC") của CTCK 
                        4. Tài sản tài chính đã lưu ký tại VSDC và chưa giao dịch của CTCK                                              
                        5. Tài sản tài chính chờ về của CTCK                                                                            
                        6. Tài sản tài chính chưa lưu ký tại VSDC của CTCK                                                              
                        7. Tài sản tài chính được hưởng quyền của CTCK       
                                                                                           
                    1.6 TÀI SẢN VÀ CÁC KHOẢN PHẢI TRẢ
                        - Gồm các thông tin như: 
                            1. Tài sản tài chính niêm yết đăng ký giao dịch tại VSDC của Nhà đầu tư                                                  
                                1.1 Tài sản tài chính giao dịch tự do chuyển nhượng                                                                   
                                1.2 Tài sản tài chính hạn chế chuyển nhượng                                                                            
                                1.3 Tài sản tài chính giao dịch cầm cố                                                                                 
                                1.4 Tài sản tài chính phong tỏa, tạm giữ                                                                              
                                1.5 Tài sản tài chính chờ thanh toán                                                                                 
                            2. Tài sản tài chính đã lưu ký tại VSDC và chưa giao dịch của Nhà đầu tư                                               
                                2.1 Tài sản tài chính đã lưu ký tại VSDC và chưa giao dịch, tự do chuyển nhượng                                            
                                2.2 Tài sản tài chính đã lưu ký tại VSDC và chưa giao dịch; hạn chế chuyển nhượng                               
                            3. Tài sản tài chính chờ về của Nhà đầu tư 
                            4. Tài sản tài chính chưa lưu ký tại VSDC của Nhà đầu tư                                               
                            5. Tài sản tài chính được hưởng quyền của Nhà đầu tư                                                
                            6. Tiền gửi của khách hàng                                                                                         
                                6.1 Tiền gửi của Nhà đầu tư về giao dịch chứng khoán theo phương thức CTCK quản lý                 
                                6.2 Tiền gửi ký quỹ của Nhà đầu tư tại VSDC                                                         
                                6.3 Tiền gửi tổng hợp giao dịch chứng khoán cho khách hàng                                         
                                6.4 Tiền gửi bù trừ và thanh toán giao dịch chứng khoán                                                                    
                                - Tiền gửi bù trừ và thanh toán giao dịch chứng khoán của Nhà đầu tư trong nước                                              
                                - Tiền gửi bù trừ và thanh toán giao dịch chứng khoán của Nhà đầu tư nước ngoài                                            
                                6.5 Tiền gửi của Tổ chức phát hành chứng khoán                                                      
                            7. Phải trả Nhà đầu tư về tiền gửi giao dịch chứng khoán theo phương thức CTCK quản lý              
                                7.1 Phải trả Nhà đầu tư trong nước về tiền gửi giao dịch chứng khoán theo phương thức CTCK quản lý                         
                                7.2 Phải trả Nhà đầu tư nước ngoài về tiền gửi giao dịch chứng khoán theo phương thức CTCK quản lý                             
                                7.3 Phải trả Tiền gửi ký quỹ của Nhà đầu tư tại VSDC                                                                        
                            8. Phải trả cổ tức, gốc và lãi trái phiếu                                                                                                                              

                    
                2. BÁO CÁO KẾT QUẢ HOẠT ĐỘNG KINH DOANH
                    2.1 DOANH THU HOẠT ĐỘNG
                        - Gồm các khoản từ mục I.  Doanh thu hoạt động của các công ty chứng khoán.
                       
                    2.2 CHI PHÍ HOẠT ĐỘNG
                        - Gồm các khoản từ mục II. Chi phí hoạt động của các công ty chứng khoán.
                        
                    2.3 DOANH THU HOẠT ĐỘNG TÀI CHÍNH
                        - Gồm các khoản từ mục III. Doanh thu hoạt động tài chính.
                       
                    2.4 CHI PHÍ TÀI CHÍNH
                        - Gồm các mục IV. Chi phí tài chính, V. Chí phí quản lý công ty chứng khoán, VI. Kết quả hoạt động.
                    
                    2.5 THU NHẬP KHÁC
                        - Gồm các mục từ VII. Thu thập khác và chi phí khác, VIII tổng lợi nhuận kế toàn toán trước thuế, IX Chi phí thuế thu nhập doanh nghiệp,
                         X. Lợi nhuận kế toán sau thuế, XI. lợi nhuận trên cổ phiếu cổ đông. Và các mục còn lại nếu có.
                        - Các thông tin về LỢI NHUẬN sẽ nằm ở phần này 
            
                3. BÁO CÁO LƯU CHUYỂN TIỀN TỆ
                    3.1 LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG KINH DOANH
                    3.2 LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG ĐẦU TƯ
                    3.3 LƯU CHUYỂN TIỀN TỪ HOẠT ĐỘNG TÀI CHÍNH
                    3.4 PHẦN LƯU CHUYỂN TIỀN TỆ HOẠT ĐỘNG MÔI GIỚI
                
                4. BÁO CÁO TÌNH HÌNH BIẾN ĐỘNG VỐN CHỦ SỞ HỮU
                5. THUYẾT MINH BÁO CÁO TÀI CHÍNH

                     
             Ưu tiên thông tin ở các mục 1 2 3, Chú ý hạn chế sử dụng thông tin ở THUYẾT MINH BÁO CÁO TÀI CHÍNH nhất có thể.
             Lưu ý nếu người dùng muốn tìm kiếm thông tin về doanh nghiệp như: tên ngành nghề, mã cổ phiếu, ... hoặc các thông tin về báo cáo tài chính như: loại báo cáo, kỳ báo cáo,... sử dụng THUYẾT MINH BÁO CÁO TÀI CHÍNH. 
             Hãy trả về dưới định dạng sau KHÔNG GIẢI THÍCH THÊM các section và subsection, 
             sử dụng tên cụ thể như ở trên và bỏ các số thứ tự ở đầu. LƯU Ý: các section và subsection đã được nêu tên theo đúng như mô tả không sử dụng tên khác thay thế:
                section1: subsection1, subsection2,... ; section2: subsection2, subsection2,... 
             Nếu phải dùng đến THUYẾT MINH BÁO CÁO TÀI CHÍNH THÌ cách trả về cũng tương tự tuy nhiên thay các subsection thày các key word để tìm kiếm, các key word  dùng để tìm các 
             đoạn thông tin có liên quan đến câu hỏi của người dùng nhất. Ví dụ:
                section1: subsection1, subsection2,... ; section2: subsection2, subsection2,...; THUYẾT MINH BÁO CÁO TÀI CHÍNH: key_word1, key_word2,...
            Lưu ý mục giới thiệu không có subsection.
            Lưu ý với từng lĩnh vực hoạt động khác nhau của doanh nghiệp có các subsection trong các section khác nhau dựa trên hướng dẫn trên và thông tin về lĩnh vực doanh nghiệp dưới đây.
            Câu hỏi người dùng: {user_question}, và công ty {isBank} là ngân hàng, doanh nghiệp trên {isIndex} là công ty Chứng khoán.
                       
    """
    features = call_api_gemi(prompt_requery_by_graph)
    features = [x.strip() for x in features.split(";") if x.strip()]
    result = ''
    notes_infor  = ''
    extra_infor = ''
    print(features)

    for f in features:
        if ':' in f:
            section = f.split(':')[0].strip()
        else:
            section = f.strip()
        if section == "BÁO CÁO TÌNH HÌNH TÀI CHÍNH":
            section = "BẢNG CÂN ĐỐI KẾ TOÁN"
        if section == "THUYẾT MINH BÁO CÁO TÀI CHÍNH":
            print("Tìm thông tin của Thuyết minh báo cáo tài chính")
            key_word = [sub.strip() for sub in  f[f.find(':') + 1 : ].split(',') if sub.strip()]
            notes_infor = get_doc_from_notes_by_key_word(key_word= key_word, infor= infor, temp_path= temp_path)
        if section == 'BÁO CÁO TÌNH HÌNH BIẾN ĐỘNG VỐN CHỦ SỞ HỮU':
            data_query = query_raw_text(company_name= infor[0],section=section, time= infor[2])
            for data in data_query:
                extra_infor += data['raw_text'] + '\n' + data['time']
                extra_infor += "\n".join(map(str, data['pages']))
        if section == 'Giới thiệu':
            data_query = query_raw_text(company_name= infor[0], section=section ,time= infor[2])
            for data in data_query:
                extra_infor += data['raw_text'] + '\n' + data['time']
                extra_infor += "\n".join(map(str, data['pages']))
        else:
            subsection = [sub.strip() for sub in  f[f.find(':') + 1 : ].split(',') if sub.strip()]
            for sub in subsection:
                doc = (query_company_raw_text(company_name= infor[0], time= infor[2], section=section, subsection= sub))
                for data in doc:
                    result += 'Thời điểm của dữ liệu: ' + data['time'] + '\n' + data['table_structure'] + '\n' + data['raw_text'] + '\n' + "\n".join(map(str, data['pages']))
    print(extra_infor)
    result = infor[0] + ' ' + infor[1] + ' ' + infor [2] + '\n' + result + '\n' + "Thông tin Thuyết minh báo cáo tài chính (có thể có hoặc không): " + notes_infor + 'Một số thông tin thêm (nếu có): \n' + extra_infor
    return result

#find k similar information in vector database
def find_information(input_model='all-MiniLM-L6-v2', k=20, infor_question = '',temp_path = None, content = None) -> tuple:
    index, metadatas = get_database(input_model='all-MiniLM-L6-v2',temp_path = temp_path,content = content, is_graph = False)
    similar_infos = []
    for promot in infor_question:
        user_question, user_question_vector = get_user_question_embedding(input_model=input_model, user_question = promot)

        #search for similar information in FAISS database
        D, I = index.search(user_question_vector.reshape(1, -1), k)  # D: distances, I: indices
        
        similar_info = []
        for idx in I[0]: 
            similar_info.append(metadatas[idx])
        similar_infos.append(similar_info)
        
    return similar_infos

def hybrid_search(query, top_k,semantic_results, input_path, content = None):
    keyword_results = keyword_search(query, 3, input_path, content = content)
    print("đang hybrid_search")
    # Ghép kết quả, loại trùng (theo content)
    seen = set()
    candidates = []
    for item in semantic_results + keyword_results:
        if item["content"] not in seen:
            candidates.append(item)
            seen.add(item["content"])
    return candidates

def remove_same_content(similar_doc):
    seen = set()
    candidates = []
    for item in similar_doc:
        if item["content"] not in seen:
            candidates.append(item)
            seen.add(item["content"])
    return candidates

from sentence_transformers import CrossEncoder
reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")

def rerank(query, candidates, top_k=5):
    print("Đang re-rank")
    pairs = [[query, doc["content"]] for doc in candidates]
    print(len(candidates))
    scores = reranker.predict(pairs)
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    print("Đã re-rank xong !")
    
    return [doc for doc, score in ranked[:top_k]]

def retrieve(query, top_k=5,semantic_results= '',input_path = '', content = None):
    # 1. Hybrid search
    
    candidates = hybrid_search(query, top_k,semantic_results=semantic_results,input_path= input_path, content= content)
    
    # 2. Re-rank
    final_docs = rerank(query, candidates, top_k)
    return final_docs
