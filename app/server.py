import logging
import json
import os
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from twilio.rest import Client
from pymongo import MongoClient

from vertex import Assistant
from assistantconversation import AssistantConversation

from vertexai.preview.generative_models import Content, Part

client = MongoClient(os.environ['TRAVIGO_MONGODB_CONNECTION'])
app = FastAPI()

class OnMessageReceived(BaseModel):
  EventType	: str = ""
  ConversationSid : str = ""
  MessageSid : str = ""
  MessagingServiceSid	: str = ""
  Index : int = 0
  DateCreated	: str = ""
  Body : str = ""
  Author	: str = ""
  ParticipantSid	: str = ""
  Attributes	: str = ""
  Media	: str = ""
  ChannelMetadata : str = ""

@app.get("/assistant")
async def get():
  updateConversationHistory("dlkfngjkdnfg", json.dumps({}))
  return HTMLResponse("No content here")

def getConversationHistory(conversationID : str) -> AssistantConversation:
  db = client[os.environ['TRAVIGO_MONGODB_DATABASE']]
  collection = db['assistant_conversations']

  searchQuery = {"ConversationID": conversationID}
  conversation = collection.find_one(searchQuery)
  
  if conversation is None:
      conversation = AssistantConversation(
        ConversationID=conversationID,
        LastModified=datetime.now(),
        Messages="[]"
      )
  else:
      conversation = AssistantConversation(**conversation)

  return conversation

def updateConversationHistory(conversation: AssistantConversation):
  db = client[os.environ['TRAVIGO_MONGODB_DATABASE']]
  collection = db['assistant_conversations']

  searchQuery = {"ConversationID": conversation.ConversationID}

  collection.update_one(searchQuery, {"$set": conversation.model_dump()}, upsert=True)

@app.post("/assistant/twilio/webhook")
async def get(request: Request):
  client = Client(os.environ['TRAVIGO_TWILIO_ACCOUNT_SID'], os.environ['TRAVIGO_TWILIO_AUTH_TOKEN'])

  form_data = await request.form()

  event_type = form_data['EventType']
  
  if event_type == "onMessageAdded":
      received_message = OnMessageReceived(**form_data)
      print(received_message)

      logging.info("Message received")

      # Load previous history
      conversationHistory = getConversationHistory(received_message.ConversationSid)
      previousHistoryDict = json.loads(conversationHistory.Messages)
      previousHistory = []

      for historyItem in previousHistoryDict:
        parts = []
        for partDef in historyItem['parts']:
          if 'text' in partDef:
            part = Part.from_text(partDef['text'])
          elif 'function_call' in partDef or 'function_response' in partDef:
            part = Part.from_dict(partDef)

          parts.append(part)

        content = Content(role=historyItem['role'], parts=parts)
        previousHistory.append(content)

      # Create new chat
      assistant = Assistant()
      assistant.create_chat(history=previousHistory)

      response = assistant.message(received_message.Body)

      for part in response.candidates[0].content.parts:
        send_message = client.conversations \
                .v1 \
                .services(os.environ['TRAVIGO_TWILIO_SERVICE_SID']) \
                .conversations(received_message.ConversationSid) \
                .messages \
                .create(author='system', body=part.text)
        
        print(send_message)

      # Update database history
      history = []

      for historyItem in assistant.chat.history:
        history.append(historyItem.to_dict())

      conversationHistory.Messages = json.dumps(history)

      updateConversationHistory(conversationHistory)

      return HTMLResponse("OK")
  
  return HTMLResponse("Unknown mode")
