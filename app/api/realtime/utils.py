from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_notification_to_all(message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "notifications",
        {
            "type": "send_notification",
            "content": {
                "message": message
            }
        }
    )

def send_notification_to_user(user_id, message, extra_data=None):
    # Handle the case when user_id is None (anonymous user)
    if user_id is None:
        user_id = 'anonymous'
        
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}_notifications",
        {
            "type": "send_notification",
            "content": {
                "message": message,
                **(extra_data or {})
            }
        }
    ) 