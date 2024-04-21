from openai import OpenAI
import time
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
        messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
        response = messages.to_dict()["data"][0]["content"][0]['text']['value']
        self.history.append((message_content, response))
        return response


bot = Bot()


response = bot.send_message("how can i place an order")
print(response)
