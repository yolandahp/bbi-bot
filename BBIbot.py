import os, requests, json, pickle, re
from datetime import datetime
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

secrets = []

def load_secrets(filename):
    global secrets
    with open(filename, "r") as f:
        secrets = json.load(f)

def load_creds(filename):
    with open(filename, 'rb') as token:
        return pickle.load(token)

def build_sheet():
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    spreadsheet_id = secrets["sheet_id"]

    creds = load_creds('token.pickle')
    service = build('sheets', 'v4', credentials=creds)

    sheet = service.spreadsheets()

    return sheet, spreadsheet_id

def weight_record(user, prev_weight, cur_weight):
    weight_change = cur_weight - prev_weight
    if (weight_change < 0):
        emoji = '\U00002B07'
    elif (weight_change > 0):
        emoji = '\U00002B06'
    else:
        emoji = '\U00002194'

    comment = "{}: {}{:.1f}".format(user, emoji, weight_change)
    return comment

def add_to_sheet(user, value):
    sheet, spreadsheet_id = build_sheet()

    month = datetime.now().strftime('%B')
    range_name = "{}!B3:B30".format(month)

    result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                range=range_name).execute()

    values = result.get('values')
    idx = 0
    date_today = datetime.now().strftime('%m/%d/%Y').lstrip("0").replace(" 0", " ")
    for i in range(len(values)):
        if values[i][0] == date_today:
            idx = i
            break
    
    if user == "fatanugraha":
        range_name = "{}!D{}".format(month, 3+idx)
    elif user == "yolandahertita":
        range_name = "{}!C{}".format(month, 3+idx)

    # appending values
    values = [[value]]
    body = {'values': values}

    result = sheet.values().update(spreadsheetId=spreadsheet_id, 
                                range=range_name,
                                valueInputOption='RAW',
                                body=body).execute()

    # get previous weight
    if idx == 0:
        return value
    else:
        if user == "fatanugraha":
            range_name = "{}!D{}".format(month, 3+idx-1)
        elif user == "yolandahertita":
            range_name = "{}!C{}".format(month, 3+idx-1)
        
        result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                    range=range_name).execute()

        return float(result['values'][0][0])

def start(update: Update, context: CallbackContext):
    user = update.message.from_user    
    update.message.reply_text(
        "Hello {}! Please enter your body weight today! (ex: 63.7)".format(user.first_name)
    )

def update_weight(update: Update, context: CallbackContext):
    user = update.message.from_user
    text = update.message.text
    
    try:
        weight = float(text)
        res = add_to_sheet(user.username, weight)
        comment = weight_record(user.username, res, weight)
        update.message.reply_text(
            "Your weight have successfully updated!\n" + comment
        )
    except ValueError:
        update.message.reply_text("Wrong format! please input again (ex: 63.7)")

def main():
    load_secrets("secrets.json")
    updater = Updater(secrets["telegram_token"])
    dispatcher = updater.dispatcher

    # handle command in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, update_weight))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()