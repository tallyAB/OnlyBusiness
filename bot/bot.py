from openai import OpenAI
import time
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# import API_RowAppend file


class Bot:
    def __init__(self, api_key = "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", assistant_id = "asst_8FWoRndfw1BUlalAHW0Xib45"):
        self.client = OpenAI(api_key=api_key)
        self.assistant_id = assistant_id
        self.thread = self.client.beta.threads.create()
        self.assistant = self.client.beta.assistants.retrieve(assistant_id = self.assistant_id)
        self.thread = self.client.beta.threads.create()
        self.history = [] # contains tuple of (query response) in ascending order (latest response at end of list)
    def print_history(self):
        for msg , rsp in self.history:
            print(f"User: {msg}\nBot: {rsp}\n")

    def wait_on_run(self,run, thread):
        
        while run.status == "queued" or run.status == "in_progress":
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id,
            )
            time.sleep(0.5)
        
        return run
    
    def insert_data_to_spreadsheet(self,values = None):
    # schema : [order_id, customer_id, customer_name, order date, order items, status, rider, Rider contact number, Delivery address, Amount, Rating]

    # values should be passed in the following format:

        #values = [["23", "69", "Zain Ali Khokhar", "01-03-2024", "HP Envy Screen Protector, HP Envy Hinge", "Delivered", "Sponge-Bob", "03248433434", "Out of Lahore", "$6666.44", "9", "Added through API"]]


        SERVICE_ACCOUNT_FILE = r'C:\Users\Ahad Imran\Desktop\GenAI\Project\onlybusinessdummy-8706fb48751e.json' 
        SPREADSHEET_ID = '1E_TLxnvSQgz2E7Y-5kFLJZtf8OogxPklmCQ819ip-vA'
        RANGE_NAME = 'Sheet1'

        
        # Authenticate and build the service
        credentials = Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        service = build('sheets', 'v4', credentials=credentials)

        # Call the Sheets API to append the data
        request = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={'values': values}
        )
        response = request.execute()

        return "Successfully added row."

    def call_required_function(self, tools_called):

        for tool in tools_called:
            
            if (tool.function.name == 'insert_data_to_spreadsheet'):
                values_param = json.loads(tool.function.arguments)['values']
                response = self.insert_data_to_spreadsheet(values_param)

        return response
    

    def send_message(self, message_content):
        """
        Sends a message to the bot and waits for the response.
        
        Args:
        message_content (str): The content of the message the user sends to the bot.
        
        Returns:
        str: The bot's response.
        """

        message = self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content= message_content,
        )
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
            )
        run = self.wait_on_run(run, self.thread)
        
        print(run.status)
        if (run.status == 'requires_action'):
            check = self.call_required_function(run.required_action.submit_tool_outputs.tool_calls)
            print(check)

        
        messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
       
        response = messages.to_dict()["data"][0]["content"][0]['text']['value']
        self.history.append((message_content, response))
        return response

