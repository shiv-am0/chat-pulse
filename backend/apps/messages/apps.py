from django.apps import AppConfig


class MessagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.messages'
    label = 'chat_messages'   # ← Add this line
    # This is the unique internal identifier Django uses
    # It doesn't affect your URLs, models, or imports
    # It only resolves the naming collision with django.contrib.messages