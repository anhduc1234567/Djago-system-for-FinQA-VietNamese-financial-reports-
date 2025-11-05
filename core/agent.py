# # agent_runner.py
# import os
# from google import genai
# from langchain.agents import Tool, initialize_agent, AgentType
# from langchain_google_genai import ChatGoogleGenerativeAI
# from receiver import find_information, retrieve

# GOOGLE_API = "AIzaSyD8I_NEiSOc-VSxJpwpafPTiotiarIVMlE"

# # Khởi tạo Gemini LLM cho Agent
# llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# # --- Tool 1: Viết lại câu hỏi (ReQuery) ---
# def tool_requery(user_question: str) -> str:
#     client = genai.Client(api_key=GOOGLE_API)
#     prompt = f"""
#     Bạn là một trợ lý phân tích tài chính.
#     Hãy viết lại câu hỏi để phục vụ việc tìm kiếm dữ liệu vector (câu hỏi: {user_question}).
#     Chỉ trả về câu hỏi đã viết lại.
#     """
#     result = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
#     return result.text.strip()

# # --- Factory cho Tool 2: Retrieval (giữ temp_path) ---
# def make_tool_retrieve(temp_path):
#     def _retrieve(query: str, k=5) -> str:
#         similar_infos = find_information(
#             input_model='all-MiniLM-L6-v2',
#             k=15,
#             infor_question=query,
#             temp_path=temp_path   # ✅ luôn có giá trị
#         )
#         # similar_k = retrieve(query=query, top_k=k, semantic_results=similar_infos)
#         return "\n".join([doc["content"] for doc in similar_infos])
#     return _retrieve

# # --- Tool 3: Sinh câu trả lời từ Gemini ---
# def tool_answer(prompt: str) -> str:
#     client = genai.Client(api_key=GOOGLE_API)
#     response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
#     return response.text

# # Hàm chạy agent
# def run_agent(user_question: str, temp_path: str):
#     # tạo tool với temp_path cụ thể
#     retrieval_tool = Tool(
#         name="Retriever",
#         func=make_tool_retrieve(temp_path),
#         description="Truy xuất các đoạn dữ liệu liên quan nhất từ báo cáo tài chính"
#     )

#     tools = [
#         Tool(name="ReQuery", func=tool_requery,
#              description="Chỉ dùng để viết lại câu hỏi. Nếu đã có dữ liệu cần thiết, đừng gọi tool này."),
#         retrieval_tool,
#         Tool(name="AnswerWithGemini", func=tool_answer,
#              description="Sinh câu trả lời cuối cùng từ prompt và dữ liệu")
#     ]

#     agent = initialize_agent(
#         tools=tools,
#         llm=llm,
#         agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
#         verbose=True,
#         handle_parsing_errors=True 
#     )

#     response = agent.run(user_question)
#     return response
