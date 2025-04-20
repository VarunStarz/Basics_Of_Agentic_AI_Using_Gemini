import os
from dotenv import load_dotenv
import requests

load_dotenv()
google_api_key = os.getenv('GOOGLE_API_KEY')

from google import generativeai
from google.generativeai.types import FunctionDeclaration, Tool

generativeai.configure(api_key=google_api_key)

from pydantic import BaseModel, Field
import json

def getWeather(args):
    for key,value in args.items():
        print(f"key: {key}", f"value: {value}")

    latitude = args['latitude']
    longitude = args['longitude']

    response = requests.get(
        f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"
    )
    #print(f"response.content: {response.content}")
    data = response.json()
    #print(f'response --> ', data['current'])
    return data['current']

def call_function(name, args):
    if name == "getWeather":
        return getWeather(args)

weatherTool = FunctionDeclaration(
    name="getWeather",
    description="Get the current temperature for the given coordinates which are lattitude and longitude",
    parameters={
        "type": "object",
        "properties": {
            "latitude": {"type": "number"},
            "longitude": {"type": "number"},
        },
        "required": ["latitude", "longitude"]
    }
)

#tool = Tool(function_declarations=[weatherTool])

#model = generativeai.GenerativeModel(model_name="gemini-2.0-flash", tools=tool, system_instruction="You are a helpful weather assistant")

#chat = model.start_chat()
#chatResponse = chat.send_message("What's the weather like in Paris today?")
#print(f"chatResponse: {chatResponse}")

#if chatResponse.candidates[0].content.parts and hasattr(chatResponse.candidates[0].content.parts[0], 'function_call'):
#    function_call = chatResponse.candidates[0].content.parts[0].function_call
#    print(f"Function called: {function_call.name}")
#    print(f"Arguments: {function_call.args}")

#else:
#    print(f"chatResponse.text: {chatResponse}")

#---------------------------------------------------------------------------------

#functions = [getWeather]

#config = {
#    'tools': functions,
#    'automatic_function_calling': {'disable': True}
#}

toolConfig = {
        'function_calling_config': {
            'mode': 'any'
        }
    }

tool = Tool(function_declarations=[weatherTool])

model = generativeai.GenerativeModel(model_name="gemini-2.0-flash", tools=tool, tool_config=toolConfig,
                                     system_instruction="You are a helpful weather assistant. If you receive data other than weather data, do not return the weather data.")

chatAnswerModel = generativeai.GenerativeModel(model_name="gemini-2.0-flash")

chat = model.start_chat()
chatAnswer = chatAnswerModel.start_chat()

questionPrompt = "What's your name?"

chatResponse = chat.send_message(questionPrompt)
print(f"chatResponse: {chatResponse.candidates[0].content.parts[0].function_call}")
print(f"arguments: {chatResponse.candidates[0].content.parts[0].function_call.args}")

latitude = chatResponse.candidates[0].content.parts[0].function_call.args['latitude']
longitude = chatResponse.candidates[0].content.parts[0].function_call.args['longitude']

print(f"Latitude: {latitude}, Longitude: {longitude}")

if chatResponse.candidates[0].content.parts and hasattr(chatResponse.candidates[0].content.parts[0], 'function_call'):
    function_call = chatResponse.candidates[0].content.parts[0].function_call
    print(f"Function called: {function_call.name}")
    print(f"Arguments: {function_call.args}")

    result = call_function(function_call.name, function_call.args)
    print(f'questionPromt ---> ', questionPrompt)
    print(f'result --> ', result)

    answerPrompt = f"You are an agent who's input is a questionPrompt and the result to the question. Use both to give an answer in natural human language. questionPrompt: {questionPrompt}, result: {result}. If you receive data other than mentioned tools, do not give the received information."

    chatAnswerResponse = chatAnswer.send_message(answerPrompt)
    print(f'chatAnswer ---> ', chatAnswerResponse.text)

else:
    print(f"chatResponse.text: {chatResponse}")


class WeatherResponse(BaseModel):
    temperature: float = Field(
        description='The current temperature in celsius for the given location.'
    ) 
    response: str = Field(
        description="A natural language response to the user's question."
    )


