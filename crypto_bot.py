from openai import AzureOpenAI
import os 
import requests
import json


client = AzureOpenAI(
	api_key = os.getenv("AZURE_KEY"),
	azure_endpoint = os.getenv("AZURE_ENDPOINT"),
	api_version ="2023-10-01-preview"

)

messages = [
	{"role": "system", "content": "Response to everything as a short poem"},
	{"role": "user","content": "Find me current price of ethereum in Euro"}

]


def crypto_price(crypto_name, fiat_currency):
	url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency={fiat_currency}"
	print(url)
	response = requests.get(url)
	data = response.json()
	current_price = [coin['current_price'] for coin in data if coin['id'] == crypto_name][0]
	return f"The current price of {crypto_name} is {current_price}{fiat_currency}"

functions = [
	{
		"type": "function",
		"function": {
			"name": "get_crypto_price",
			"description": "Get prices of crypto currency in a specified global currency", 
			"parameters": {
				"type": "object",
				"properties": {
					"crypto_name":{
					"type":"string",
					"description":"The name of the crypto currency that i want to look up"
				},
				"fiat_currency": {
					"type": "string",
					"description": "The fiat currency for defining the price of crypto currency. use the offical abbreviation"
				}
			},
			"required": ["crypto_name", "fiat_currency"]

		}
	}
	}

]



response = client.chat.completions.create(
	model = "GPT-4",
	messages = messages,
	tools = functions,
	tool_choice = "auto"
)

response_message = response.choices[0].message

gpt_tools = response.choices[0].message.tool_calls

if gpt_tools:

	available_functions = {
		"get_crypto_price": crypto_price
	}

	messages.append(response_message)
	for gpt_tool in gpt_tools:
		function_name = gpt_tool.function.name
		function_to_call = available_functions[function_name]
		function_parameters = json.loads(gpt_tool.function.arguments)
		function_response = function_to_call(function_parameters.get('crypto_name'), function_parameters.get('fiat_currency'))
		messages.append(
			{
				"tool_call_id": gpt_tool.id,
				"role": "tool",
				"name": function_name,
				"content": function_response
			}
		)
		second_response = client.chat.completions.create(
			model = "GPT-4",
			messages=messages
		)
		print(second_response.choices[0].message.content)





else:
	print(response.choices[0].message.content)
