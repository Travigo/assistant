# import vertexai.generative_models
import requests
import sys
from vertexai.preview.generative_models import GenerativeModel, Tool, FunctionDeclaration, AutomaticFunctionCallingResponder, Part


def search_stops(name : str, transporttype : str):
    """Search for public transport stops (bus stop/train station/tram stop/metro station) that match a give query string for the name of the stop

    Args:
        name: The name or location of the stop (bus stop/train station/tram stop/metro station) 
        transporttype: The mode of transport the stop serves, such as bus, train, rail, tram, metro, underground
    """
    print("stop_search", name, transporttype)
    resp = requests.get(url='https://api.travigo.app/core/stops/search', params={'name':name, 'transporttype':transporttype})
    return resp.json()

def get_stop(primaryidentifier : str):
    """Get information related to the stop such as services running at it, platforms, entrances

    Args:
        primaryidentifier: The unique PrimaryIdentifier representing the transport stop
    
    """

    print("stop", primaryidentifier)

    resp = requests.get(url=f"https://api.travigo.app/core/stops/{primaryidentifier}")
    return resp.json()

def stop_departures(primaryidentifier : str):
    """Return the departing journeys with their destination and departure time that are leaving from a stop based on the unique PrimaryIdentifier for the transport stop bus stop/train station/tram stop/metro station)
    
    Args:
        primaryidentifier: The unique PrimaryIdentifier representing the transport stop
    """
    print("departures", primaryidentifier)
    
    resp = requests.get(url=f"https://api.travigo.app/core/stops/{primaryidentifier}/departures")
    return {"departures": resp.json()}

# for stop in search_stops("Baldock rail", "Rail"):
#     print(stop['PrimaryName'])

# sys.exit(1)

# Infer function schema
get_stop_func = FunctionDeclaration.from_func(get_stop)
search_stops_func = FunctionDeclaration.from_func(search_stops)
stop_departures_func = FunctionDeclaration.from_func(stop_departures)
# Tool is a collection of related functions
travigo_tool = Tool(
    function_declarations=[get_stop_func, search_stops_func, stop_departures_func],
)

# Use tools in chat:
model = GenerativeModel(
    "gemini-1.5-flash-preview-0514",
    # You can specify tools when creating a model to avoid having to send them with every request.
    tools=[travigo_tool],
    system_instruction=Part.from_text("You are an AI assistant who helps users with queries about public transport")
)

# Activate automatic function calling:
afc_responder = AutomaticFunctionCallingResponder(
    # Optional:
    max_automatic_function_calls=5,
)
chat = model.start_chat(responder=afc_responder)

def message(chat, text):
    print(f"User: {text}")
    response = chat.send_message(text)
    
    for part in response.candidates[0].content.parts:
        print(f"AI: {part.text}")

message(chat, "Is there a rail station in Baldock and what is its name and identifier?")
# message(chat, "What services run at this station")
message(chat, "When is the next train to Cambridge from this station?")
message(chat, "I can't make that, when is the next one around 10pm?")