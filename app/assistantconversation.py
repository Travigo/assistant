from datetime import datetime
from pydantic import BaseModel

class AssistantConversation(BaseModel):
  ConversationID : str
  Messages : str = ""
  LastModified : datetime
