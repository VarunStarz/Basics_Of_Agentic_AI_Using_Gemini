from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
import os
import logging
from dotenv import load_dotenv
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

log = logging.getLogger(__name__)

load_dotenv()
google_api_key = os.getenv('GOOGLE_API_KEY')

from google import generativeai

generativeai.configure(api_key=google_api_key)
model = generativeai.GenerativeModel(model_name="gemini-2.0-flash")

class EventExtraction(BaseModel):
    """First LLM call: Extract basic event information"""

    description: str = Field(description='Raw description of the event')
    isCalenderEvent: bool = Field(description='Whether this text describes a calendar event')
    confidenceScore: float = Field(description='Confidence score between 0 and 1')

class EventDetails(BaseModel):
    """Second LLM call: Parse specific event details"""

    name: str = Field(description='Name of the event')
    date: str = Field(description='Date and time of the event. Use ISO 8601 to format this value.')
    durationInMinutes: int = Field(description='Expected duration in minutes')
    participants: list[str] = Field(description='List of participants')

class EventConfirmation(BaseModel):
     """Third LLM call: Generate confirmation message"""

     confirmationMessage: str = Field(description='Natural language confirmation message')
     calendarLink: str = Field(description='Generated calendar link if applicable')

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

def extractEventInformation(userInput: str) -> EventExtraction:
    """First LLM call to determine if input is a calendar event"""

    log.info('Entering into extractEventInformation')
    log.info(f'userInput --> {userInput}')

    today = datetime.now()
    dateContext = f"Today is {today.strftime('%A, %B %d, %Y')}"
    log.info(f'dateContext --> {dateContext}')

    eventExtractionSchema = removeTitles(EventExtraction.model_json_schema())
    log.info(f'eventExtractionSchema --> {eventExtractionSchema}')

    prompt = f"Analyze if the user's input describes a calendar event. User Input: {userInput}"
    response = model.generate_content(contents=prompt, generation_config={"response_mime_type": "application/json","response_schema": eventExtractionSchema})
    
    log.info(f'extractEventInformation response --> {response.text}')

    try:
        responseDict = json.loads(response.text)
        eventExtractionResponse = EventExtraction(**responseDict)
    except:
        log.error("Error parsing LLM response: %s", str(e))
        eventExtractionResponse = EventExtraction(description=userInput, isCalenderEvent=False, confidenceScore=0.0)

    log.info('Returning from extractEventInformation')

    return eventExtractionResponse

def parseEventDetails(description: str) -> EventDetails:
    """Second LLM call to extract specific event details"""
    
    log.info('Entering into parseEventDetails')

    today = datetime.now()
    dateContext = f"Today is {today.strftime('%A, %B %d, %Y')}"
    log.info(f'dateContext --> {dateContext}')

    eventDetailsSchema = removeTitles(EventDetails.model_json_schema())
    log.info(f'eventDetailsSchema --> {eventDetailsSchema}')

    prompt = f"{dateContext} Description: {description}. Extract detailed event information from the description provided. When dates reference 'next Tuesday' or similar relative dates, use this current date as reference."
    response = model.generate_content(contents=prompt, generation_config={"response_mime_type": "application/json","response_schema": eventDetailsSchema})
    
    log.info(f'parseEventDetails response --> {response.text}')

    try:
        responseDict = json.loads(response.text)
        parseEventDetailsResponse = EventDetails(**responseDict)
    except:
        log.error("Error parsing LLM response: %s", str(e))
        parseEventDetailsResponse = EventDetails(name="", date="", durationInMinutes=0.0, participants=[])

    log.info('Returning from parseEventDetails')

    return parseEventDetailsResponse

def generateEventConfirmation(eventDetails: EventDetails) -> EventConfirmation:
    """Third LLM call to generate a confirmation message"""

    log.info('Entering into generateEventConfirmation')
    log.info(f"eventDetails --> {eventDetails}")

    eventConfirmationSchema = removeTitles(EventConfirmation.model_json_schema())
    log.info(f'eventConfirmationSchema --> {eventConfirmationSchema}')

    prompt = f"Event Details: {str(eventDetails.model_dump())}. Generate a natural confirmation message for the event. Sign of with your name; John"
    response = model.generate_content(contents=prompt, generation_config={"response_mime_type": "application/json","response_schema": eventConfirmationSchema})
    
    log.info(f'generateEventConfirmation response --> {response.text}')

    try:
        responseDict = json.loads(response.text)
        generateEventConfirmationResponse = EventConfirmation(**responseDict)
    except:
        log.error("Error parsing LLM response: %s", str(e))
        generateEventConfirmationResponse = EventConfirmation(confirmationMessage="", calendarLink="")
    
    log.info('Returning from generateEventConfirmation')

    return generateEventConfirmationResponse

def processCalendarRequest(userInput: str) -> Optional[EventConfirmation]:
    """Main function implementing the prompt chain with gate check"""

    log.info('Entering into processCalendarRequest')

    extractedEventInformation = extractEventInformation(userInput=userInput)

    if (extractedEventInformation.isCalenderEvent == False or extractedEventInformation.confidenceScore < 0.7):
        log.warning(f"Gate check failed - is_calendar_event: {extractedEventInformation.isCalenderEvent}, confidence: {extractedEventInformation.confidenceScore:.2f}")
        return None
    log.info("Gate check passed, proceeding with event processing")

    eventDetails = parseEventDetails(description=extractedEventInformation.description)
    generatedConfirmation = generateEventConfirmation(eventDetails=eventDetails)

    log.info('Returning from processCalendarRequest')

    return generatedConfirmation


#extractEventInformation("Let's schedule a 1h team meeting next Tuesday at 2pm with Alice and Bob to discuss the project roadmap.")
#extractEventInformation("Hello.")

#CALENDAR LINK APPLICABLE
userInput = "Let's schedule a 1h team meeting last christmas at 2pm with Alice and Bob to discuss the project roadmap."

#CALENDAR LINK NOT APPLICABLE
# userInput = "We are planning to schedule a one-hour team meeting next Tuesday at 2:00 PM. The meeting will include Alice and Bob as participants, and the primary agenda will be to discuss the project roadmap. During this meeting, we will go over the current progress, identify any potential roadblocks, and align on the next steps for the project. The discussion will focus on key milestones, resource allocation, and deadlines to ensure that the project stays on track. This meeting is important for collaboration and decision-making, so it is recommended that all attendees come prepared with relevant updates and questions. The meeting can take place either virtually via a video conferencing platform or in person, depending on team preferences. Let me know if this time works for everyone or if any adjustments are needed."

result = processCalendarRequest(userInput=userInput)

if result:
    log.info(f"Confirmation Message --> {result.confirmationMessage}")
    if result.calendarLink:
        log.info(f"Calendar Link --> {result.calendarLink}")
else:
    log.info("This doesn't appear to be a calendar event request.")

