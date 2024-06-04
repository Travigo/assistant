import logging
import json
import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from twilio.rest import Client

from vertex import Assistant

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

@app.get("/assistant/twilio/")
async def get():
    return HTMLResponse("No content here")

@app.post("/assistant/twilio/webhook")
async def get(request: Request):
    client = Client(os.environ['TRAVIGO_TWILIO_ACCOUNT_SID'], os.environ['TRAVIGO_TWILIO_AUTH_TOKEN'])

    # print(request.form, )
    form_data = await request.form()

    event_type = form_data['EventType']
    
    if event_type == "onMessageAdded":
        received_message = OnMessageReceived(**form_data)
        print(received_message)

        logging.info("Message received")

        assistant = Assistant()
        assistant.create_chat()

        response = assistant.message(received_message.Body)

        for part in response.candidates[0].content.parts:
            send_message = client.conversations \
                    .v1 \
                    .services(os.environ['TRAVIGO_TWILIO_SERVICE_SID']) \
                    .conversations(received_message.ConversationSid) \
                    .messages \
                    .create(author='system', body=part.text)
            
            print(send_message)

        history = []

        for historyItem in assistant.chat.history[-5:]:
          history.append(historyItem.to_dict())

        print(json.dumps(history))

        return HTMLResponse("OK")
    
    return HTMLResponse("Unknown mode")
