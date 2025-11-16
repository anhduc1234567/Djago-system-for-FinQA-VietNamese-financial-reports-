import os
from core.graph_KD import add_new_data
# from graph_KD import add_new_data

from llama_index.core import Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_cloud_services import LlamaParse
import json
from dotenv import load_dotenv
load_dotenv()

os.environ["LLAMA_CLOUD_API_KEY"] = os.getenv("LLAMA_CLOUD_API_KEY")
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API")
# Settings.llm = Gemini(model="gemini-2.5-flash")
# Settings.embed_model = GeminiEmbedding()

def clear_folder_files(folder_path):
    """
    Xóa tất cả file trong folder_path, không xóa thư mục con.
    """
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' không tồn tại.")
        return
    
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                print(f"Đã xóa file: {file_path}")
            except Exception as e:
                print(f"Lỗi khi xóa file {file_path}: {e}")

# file_path = "20250724 - ACB - BCTC hop nhat Quy 02 nam 2025.pdf"
import asyncio
import sys

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
def pdf_to_md(file_path,type):    
    parser = LlamaParse(
    # result_type="markdown",
    # num_workers=4,
    model="openai-gpt-4-1-mini",
    # auto_mode=True,
    language='vi',
    parse_mode="parse_page_with_agent",
    high_res_ocr=True,
    outlined_table_extraction=True,
    page_separator="\n\n---\n\n",
    precise_bounding_box=True,
    # output_tables_as_HTML=True,
    adaptive_long_table=True,
    # auto_mode_trigger_on_image_in_page=True,
    # auto_mode_trigger_on_table_in_page=True
    # auto_mode_trigger_on_text_in_page="<text_on_page>"
    # auto_mode_trigger_on_regexp_in_page="<regexp_on_page>"
    )
    name_file =  os.path.splitext(os.path.basename(file_path))[0]

    save_path = f'database/{name_file}.md'
    # print(save_path)
    if os.path.exists(save_path):
        print("File pdf này đã được xử lý.")
        infor = add_new_data(save_path, is_build= True)
        
        return save_path, infor
    print("đang xử lý viết")
    
    results =  parser.parse(file_path)
    markdown_documents = results.get_markdown_documents(split_by_page=True)
    documents = markdown_documents
    
    output_folder = "preprocessed_md"
    os.makedirs(output_folder, exist_ok=True)
    clear_folder_files(output_folder)
    document_to_one_file(documents,save_path)
    for i, page in enumerate(results.pages):
        with open(f"{output_folder}/page_{i}.md", "w", encoding="utf-8") as f:
            f.write(f'{page.text} +\n {page.md} + \n + {page.layout} \n {page.structuredData}')
    infor = add_new_data(save_path)
    return save_path, infor

def document_to_one_file(documents,save_path):
    report = ''
    for i in range(len(documents)):
        report += documents[i].text + '\n'
        report += f"-----------Page {i}"
        
    with open(f"{save_path}", "w", encoding="utf-8") as f:
            f.write(report)
        