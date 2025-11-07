from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from chatbot.models import Conversation
from mongoengine.queryset.visitor import Q
from mongoengine import connect
import os
import uuid
from .models import Conversation, Message 
from django.conf import settings
from core.output_generator import respond_user
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from core.output_generator import render_markdown
# Kết nối MongoDB, giả sử database tên là 'chatbot_db'
connect(
    db='HnaFinGENI',
    host='localhost',       # hoặc địa chỉ MongoDB server
    port=27017              # port mặc định
)

from django.shortcuts import render
from django.http import Http404
from .models import Conversation, UploadedFile  # MongoEngine Document

# Tạm mặc định user là "user_ducanh"
USER_ID = "user_ducanh"
# SAVE_FILE_PATH = None
from .  import globals

def chat_home(request, conversation_id=None):
    # --- Lấy danh sách các cuộc trò chuyện của user ---
    conversations = Conversation.objects(user_id=USER_ID)

    # --- Lấy danh sách file đã upload ---
    uploaded_reports = UploadedFile.objects(user_id=USER_ID).order_by("-upload_date")

    # --- Nếu có conversation_id, lấy ra conversation tương ứng ---
    selected_conv = None
    messages = []
    if conversation_id:
        selected_conv = Conversation.objects(conversation_id=conversation_id).first()
        if not selected_conv:
            raise Http404("Conversation not found")
        messages = selected_conv.messages

    # --- Render markdown cho các message ---
    for mes in messages:
        mes.content = render_markdown(mes.content)

    # --- Gửi dữ liệu sang template ---
    context = {
        "conversations": conversations,
        "selected_conv": selected_conv,
        "messages": messages,
        "conversation_id": conversation_id,
        "uploaded_reports": uploaded_reports,  # ✅ thêm dòng này
    }

    return render(request, "chatbot/home.html", context)

def add_new_file(file_path, file_name, user_id="user_ducanh"):
    existing = UploadedFile.objects(file_path=file_path).first()
    if existing:
        print(f"⚠️ File '{file_name}' đã tồn tại trong DB, bỏ qua thêm mới.")
        return existing

    # Nếu chưa có thì tạo mới
    new_file = UploadedFile(
        user_id=user_id,
        file_name=file_name,
        file_path=file_path,
        upload_date=datetime.utcnow()
    )
    new_file.save()
    print(f"✅ File '{file_name}' đã được thêm vào DB (id={new_file.id})")

    return new_file

def new_chat(request):
    # Tạo conversation_id mới
    conversation_id = f"conv_{uuid.uuid4().hex[:6]}"  # ví dụ conv_a1b2c3
    user_id = "user_ducanh"

    # Tạo messages mặc định
    msg_user = Message(
        role="user",
        content="xin chào",
        timestamp=datetime.utcnow()
    )
    msg_bot = Message(
        role="assistant",
        content="Chào bạn tôi là trợ lý tài chính, hãy tải tài liệu lên để bắt đầu nhé",
        timestamp=datetime.utcnow()
    )

    # Lưu vào DB
    conv = Conversation(
        conversation_id=conversation_id,
        user_id=user_id,
        messages=[msg_user, msg_bot],
        file_id=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    conv.save()

    # Điều hướng tới trang chat mới
    return redirect("chat_home", conversation_id=conversation_id)

def chat_upload(request, chat_id):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)
        # optional: lưu liên kết file với chat_id trong DB
        return redirect('chat_home')  # redirect về trang chat chính
    return redirect('chat_home')


def add_new_message_to_conversation(role, content, conversation_id):
    print("đang ghi mess mới")
    msg = Message(
                role=f"{role}",
                content=f"{content}",
                timestamp=datetime.utcnow()
        )
    conv = Conversation.objects(conversation_id=conversation_id).first()
    conv.messages.append(msg)
    conv.updated_at = datetime.utcnow()
    conv.save()
    
    
@csrf_exempt
def chat_send(request, conversation_id):
    if request.method == "POST":
        message = request.POST.get("message", "").strip()
        file = request.FILES.get("file")
        is_summary = request.POST.get("isSummary", "false").lower() == "true"
        print("📄 isSummary:", is_summary)

        # ✅ thêm biến nhận từ formData
        selected_report_id = request.POST.get("selected_report_id")
        selected_report_name = request.POST.get("selected_report_name")

        print("✅ conversation_id:", conversation_id)
        print("📄 selected_report_id:", selected_report_id)
        print("📄 selected_report_name:", selected_report_name)

        if not message and is_summary == "False" :
            return JsonResponse({"response": "Bạn chưa đưa ra câu hỏi nào."})
        
        
        file_path = None

        # --- Trường hợp người dùng upload file ---
        if file:
            upload_dir = os.path.join(settings.BASE_DIR, "files_database")
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, file.name)
            # file_path = f"/media/{file.name}"
            file_name = os.path.splitext(file.name)[0]
            
            add_new_file(file_path=file_path, file_name=file_name)
            
            if not os.path.exists(file_path):
                with open(file_path, "wb+") as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                print(f"✅ File đã lưu: {file_path}")
                
            else:
                print(f"⚠️ File đã tồn tại: {file_path}")

            globals.SAVE_FILE_PATH = file_path

        # --- Trường hợp người dùng chọn file bằng radio ---
        elif selected_report_id:
            try:
                uploaded_file = UploadedFile.objects.get(id=selected_report_id)
                file_path = uploaded_file.file_path
                print(f"✅ Đang sử dụng file từ DB: {file_path}")
                globals.SAVE_FILE_PATH = file_path
            except UploadedFile.DoesNotExist:
                return JsonResponse({"response": "Không tìm thấy file đã chọn trong cơ sở dữ liệu."})

        # --- Nếu không có cả file upload lẫn file đã chọn ---
        if globals.SAVE_FILE_PATH is None:
            return JsonResponse({"response": "Bạn chưa chọn hoặc tải lên tài liệu nào."})

        print("📁 File path được sử dụng:", globals.SAVE_FILE_PATH)

        # --- Gọi hàm xử lý chatbot ---
        if is_summary is False:
            # try:
                bot_respond, suggestions = respond_user(
                    user_question=message,
                    temp_path=globals.SAVE_FILE_PATH,
                    isSummary = is_summary
                )
                html_respond = render_markdown(bot_respond)

                # --- Lưu hội thoại ---
                add_new_message_to_conversation("user", message, conversation_id=conversation_id)
                add_new_message_to_conversation("assistant", bot_respond, conversation_id=conversation_id)
                return JsonResponse({
                "response": html_respond,
                "suggestions": suggestions or []
                 })
            # except Exception as e:     
            #     return JsonResponse({
            #         "response": "❌ Lỗi trong quá trình xử lý chatbot:",
            #         "suggestions":  []
            #     })
        else:
            pdf_path = respond_user(
                user_question=message,
                temp_path=globals.SAVE_FILE_PATH,
                isSummary = is_summary
            )
            if pdf_path:
                file_name = os.path.basename(pdf_path)
                file_url = f"/media/summaries/{file_name}"  # hoặc tùy cấu hình STATIC/MEDIA_URL
                bot_response = f"✅ Đã phân tích xong: <a href='{file_url}' target='_blank'>Tải bản tóm tắt PDF</a>"
            else:
                bot_response = "❌ Lỗi khi tạo bản tóm tắt PDF."

            return JsonResponse({
                "response": bot_response,
                "suggestions": []
            })

    return JsonResponse({"error": "❌ Chỉ hỗ trợ POST request"}, status=400)


@csrf_exempt
def delete_chat(request, conversation_id):
    if request.method == "POST":
        conv = Conversation.objects(conversation_id=conversation_id).first()
        conv.delete()
        return JsonResponse({
            "response": f"Conversation {conversation_id} đã được xóa thành công"
        })