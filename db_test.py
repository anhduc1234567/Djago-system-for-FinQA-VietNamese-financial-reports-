from mongoengine import connect, disconnect
# from mongoengine.connection import MongoEngineConnectionError
from chatbot.models import Conversation

try:
    # Kết nối MongoDB
    connect(
        db='HnaFinGENI',            # tên database
        host='localhost',           # hoặc 'mongodb://localhost:27017/hnafingeni'
        port=27017,
        username='',                # nếu có username
        password='',                # nếu có password
    )
    print("✅ Kết nối MongoDB thành công!")

    # Test query
    conversations = Conversation.objects(user_id='user_ducanh')
    print(f"Số conversation tìm thấy: {len(conversations)}")
    for c in conversations:
        print(c.conversation_id, len(c.messages), "messages")

except Exception as e:
    print("❌ Có lỗi khác:", e)

finally:
    disconnect()
