import logging
from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from pytz import timezone
from .gsheets_main import upload_to_sheets

# from .gsheets_main import upload_to_sheets
import csv

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)


def getISTTime(utc_time):
    format = "%Y-%m-%d %H:%M:%S"
    now_asia = utc_time.astimezone(timezone("Asia/Kolkata"))
    return now_asia.strftime(format)


filename = "data.csv"


def loadData():
    global all_data
    with open(filename, "r") as f:
        reader = csv.reader(f)
        all_data = list(reader)


def syncSheetData():
    import requests

    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSKb_1O_ATu6iAiMRxv9OFlFjClbwSIpzwX95eCCXB3T5Aa54AgGci5_Od6eD0p1xIfpgVAIgHcO4vM/pub?gid=0&single=true&output=csv"
    logging.info("Downloading file from url: " + url + "...")
    response = requests.get(url, allow_redirects=True)
    open(filename, "wb").write(response.content)
    loadData()
    logging.info("Completed")


all_data = []


def findEntryID(entry):
    for i in all_data:
        for j in i:
            if j == entry:
                return i


def findEntryById(entry_id):
    for i in all_data:
        if i[0] == entry_id:
            return i


def getIndex(entries, text):
    for i in range(len(entries)):
        if entries[i] == text:
            return i
    return -1


user_log = []


def entry(bot, update):
    global user_log
    # logging.info(update)  # comment out in production
    if update.message and update.message.text:
        chat_id = update.message.chat_id
        text = update.message.text
        user_log.append(
            [
                getISTTime(update.message.date),
                chat_id,
                update.message.from_user.first_name,
                update.message.from_user.username,
                text,
                update.message.message_id,
            ]
        )
        if len(user_log) > 24:
            upload_to_sheets(user_log)
            user_log = []
        logging.info(text)
        if text == "/update_data":
            syncSheetData()
            bot.sendMessage(
                chat_id=chat_id,
                text="Data updated",
            )
        else:
            arr = findEntryID(text)
            if arr:
                language_index = getIndex(arr, text)
                to_reply = findEntryById(arr[2])
                if to_reply:
                    buttons = arr[3].split(",")
                    button_list = []
                    if buttons[0]:
                        for b in buttons:
                            button_entries = findEntryById(b)
                            if not button_entries[language_index]:
                                for bb in button_entries[4:]:
                                    if bb:
                                        b_text = bb
                                        break
                            else:
                                b_text = button_entries[language_index]
                            button_list.append([b_text])
                    bot.sendMessage(
                        chat_id=chat_id,
                        reply_to_message_id=update.message.message_id,
                        text=to_reply[language_index],
                        reply_markup=ReplyKeyboardMarkup(
                            button_list, resize_keyboard=True
                        ),
                    )
