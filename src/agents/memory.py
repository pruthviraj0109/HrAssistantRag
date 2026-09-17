from langchain_core.chat_history import InMemoryChatMessageHistory


class ConversationMemory:
    def __init__(self):
        self.history = InMemoryChatMessageHistory()

    def add_user_message(self, message: str):
        self.history.add_user_message(message)

    def add_ai_message(self, message: str):
        self.history.add_ai_message(message)

    def get_messages(self):
        return self.history.messages

    def clear(self):
        self.history.clear()
