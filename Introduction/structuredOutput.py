import os
from dotenv import load_dotenv

load_dotenv()
google_api_key = os.getenv('GOOGLE_API_KEY')

#import google.generativeai as genai

# Set API key
#genai.configure(api_key=google_api_key)
# Initialize Gemini model
#client = genai.GenerativeModel("gemini-2.0-flash-thinking-exp")

# List available models
#models = genai.list_models()

# Print available models
#for model in models:
#    print(model.name)

from google import generativeai

generativeai.configure(api_key=google_api_key)

from pydantic import BaseModel
import json

def extractStructureFromSchema(schema):
    structure = {}

    for key,value in schema.get('properties', {}).items():
        if value['type'] == 'array':
            structure[key] = ['value']
        else:
            structure[key] = 'value'

    return structure

def removeTitles(schema):
    if isinstance(schema, dict):
        return {
            key: removeTitles(value) for key, value in schema.items() if key != "title"
        }
    elif isinstance(schema, list):
        return [removeTitles(item) for item in schema]
    return schema

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

calendarEventSchema = CalendarEvent.model_json_schema()
print('calendarEventSchema --> ', calendarEventSchema)

calendarEventCleanedSchema = removeTitles(calendarEventSchema)
print('calendarEventCleanedSchema --> ', calendarEventCleanedSchema)

#calendarEventExtractedSchema = extractStructureFromSchema(calendarEventSchema)
#print('calendarEventExtractedSchema --> ', calendarEventExtractedSchema)

#calendarEventExtractedSchema = {
#    "type": "object",
#    "properties": {
#        "name": {"type": "string"},
#        "date": {"type": "string"},
#        "participants": {"type": "array", "items": {"type": "string"}}
#    },
#    "required": ["name", "date", "participants"]
#}


prompt = """
Extract event details from the given text and format them in JSON.
The format should be in JSON format:
{
  name: value,
  participants: value in list,
  date: value
}

Text: "Alice and Bob are going to a science fair on Friday."
"""

newPrompt = 'Extract event details from the given text. Text: "Alice and Bob are going to a science fair on Friday.'

model = generativeai.GenerativeModel(model_name="gemini-2.0-flash")
#response = model.generate_content(contents=prompt, generation_config={"response_mime_type": "application/json"})
response = model.generate_content(contents=newPrompt, generation_config={"response_mime_type": "application/json","response_schema": calendarEventCleanedSchema})

print('response --> ', response.text)

# Parse response into Pydantic model
#try:
#    event_data = json.loads(response.candidates[0].content.parts[0].text)
#    event = CalendarEvent(**event_data)
#    print(event.name)
#    print(event.date)
#    print(event.participants)  # Validated event object
#except Exception as e:
#    print("Error parsing response:", e)
