# Third-party imports
# import openai
from fastapi import FastAPI, Form, Depends, Request
from decouple import config
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# Internal imports
from models import Conversation, SessionLocal
from utils import send_message, logger
from bot.bot import Bot

# Sheets imports
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pandas as pd
import os

app = FastAPI()


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@app.get("/")
async def index():
    return {"msg": "working"}


@app.post("/message")
async def reply(request: Request, Body: str = Form(), db: Session = Depends(get_db)):

    # Extract the phone number from the incoming webhook request
    form_data = await request.form()
    whatsapp_number = form_data['From'].split("whatsapp:")[-1]

    thread_id = fetch_thread(whatsapp_number)

    # Call the OpenAI API to generate text with ChatGPT
    new_bot = Bot(thread_old=thread_id,
                  whatsapp_number=whatsapp_number)

    messages = [{"role": "user", "content": Body}]
    messages.append(
        {"role": "system", "content": "You're an investor, a serial founder and you've sold many startups. You understand nothing but business."})

    # The generated text
    chatgpt_response = new_bot.send_message(Body)

    # Store the conversation in the database
    try:
        conversation = Conversation(
            sender=whatsapp_number,
            message=Body,
            response=chatgpt_response
        )
        db.add(conversation)
        db.commit()
        logger.info(f"Conversation #{conversation.id} stored in database")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error storing conversation in database: {e}")

    print(f"Sending the ChatGPT response to this number: {whatsapp_number}")
    send_message(whatsapp_number, chatgpt_response)
    return ""


def fetch_thread(whatsapp_num):
    # schema : [order_id, customer_id, customer_name, order date, order items, status, rider, Rider contact number, Delivery address, Amount, Rating]

    SERVICE_ACCOUNT_PATH = "SpreadsheetAPI/onlybusinessdummy-8706fb48751e.json"
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, SERVICE_ACCOUNT_PATH)

    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
    RANGE_NAME = 'Sheet2'

    # Authenticate and build the service
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    service = build('sheets', 'v4', credentials=credentials)

    # Call the Sheets API to append the data
    sheet = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME, majorDimension='ROWS').execute()

    sheet_values = sheet['values']
    column_names = sheet_values[0]
    data_rows = sheet_values[1:]

    df = pd.DataFrame(data_rows, columns=column_names)
    query_results = df[df['Phone Number'] == whatsapp_num]
    print("CHECK\n", df['Phone Number'], "\n", whatsapp_num)
    if len(query_results) > 0:
        print("LAME", query_results['Thread ID'].values[0])
        return query_results['Thread ID'].values[0]
    else:
        return None
