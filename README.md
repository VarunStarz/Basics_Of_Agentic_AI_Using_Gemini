# Basics Of Agentic AI Using Gemini
This repository contains basics of Agentic AI implementation such as getting a structured output from a LLM, function calling using tools and prompt chaining using Gemini api.

# Structed Output
The GenerativeModel of Gemini has a method called generate_content() which has two important parameters: response_mime_type and response_schema. These are the equivalent of OpenAI's response_format method parameter. This can be used if you want the LLM to give it's response in a particular format (ex. JSON) instead of natural language.

# Function Calling Using Tools
Function calling lets you connect models to external tools and APIs. Instead of generating text responses, the model understands when to call specific functions and provides the necessary parameters to execute real-world actions. This allows the model to act as a bridge between natural language and real-world actions and data. Function calling has 3 primary use cases:

Augment Knowledge: Access information from external sources like databases, APIs, and knowledge bases.
Extend Capabilities: Use external tools to perform computations and extend the limitations of the model, such as using a calculator or creating charts.
Take Actions: Interact with external systems using APIs, such as scheduling appointments, creating invoices, sending emails, or controlling smart home devices

The GenerativeModel of Gemini has two parameters called tools and tool_config. The tool_config defines the function calling configuration while the tool is a FunctionDeclaration object which defines the purpose of the particular tool.

# Prompt Chaining
Prompt chaining is a technique used when working with generative AI models in which the output from one prompt is used as input for the next. The AI Agent chains its output with all the available methods in order to give a final output.
