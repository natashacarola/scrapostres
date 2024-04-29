from datetime import datetime
from functools import partial
import logging as logger
import os
from dotenv import load_dotenv
import psycopg2
from utils import *
from querys import *
import random
import sys
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
import io

from telegram import Update, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

from commands import *

DISABLED = "DISABLED"
ENABLED = "ENABLED"
CATEGORIES = "CATEGORIES"
CUISINES = "CUISINES"
DATES = "DATES"
HEARTS = "HEARTS"
MIN = "MIN"
MAX = "MAX"

def main() -> None:
    load_dotenv()
    logger.basicConfig(stream=sys.stdout, level=logger.INFO)
    connection = get_connection()
    updater = Updater(token=os.environ["BOT_TOKEN"])

    filters = {}
    for (filter_name, column) in [(CATEGORIES, "Category"), (CUISINES, "Cuisine")]:
        filters[filter_name] = load_filter(connection, column)
        if not filters[filter_name]:
            return
    
    oldest_updated_date = execute_fetch_query(get_oldest_updated_date(), connection)[0]["min"]
    newest_updated_date = execute_fetch_query(get_newest_updated_date(), connection)[0]["max"]
    oldest_updated_date = datetime(oldest_updated_date.year, oldest_updated_date.month, oldest_updated_date.day)
    newest_updated_date = datetime(newest_updated_date.year, newest_updated_date.month, newest_updated_date.day)
    filters[DATES] = {MIN: oldest_updated_date, MAX: newest_updated_date}
    filters[HEARTS] = set()
    filters[HEARTS].add(0)

    # Get the dispatcher to register handlers
    # Then, we register each handler and the conditions the update must meet to trigger it
    dispatcher = updater.dispatcher

    # Register commands
    dispatcher.add_handler(CommandHandler("random_recipe", partial(send_random_recipe, connection=connection, filters=filters)))
    dispatcher.add_handler(CommandHandler(CATEGORIES, partial(send_filter, filter=filters[CATEGORIES], name=CATEGORIES)))
    dispatcher.add_handler(CommandHandler(CUISINES, partial(send_filter, filter=filters[CUISINES], name=CUISINES)))
    dispatcher.add_handler(CommandHandler("set_categories", partial(set_filter, filter=filters[CATEGORIES], name=CATEGORIES), pass_args=True))
    dispatcher.add_handler(CommandHandler("set_cuisines", partial(set_filter, filter=filters[CUISINES], name=CUISINES), pass_args=True))
    dispatcher.add_handler(CommandHandler(DATES, partial(send_dates, filter=filters[DATES])))
    dispatcher.add_handler(CommandHandler("set_dates", partial(set_dates, filters=filters, connection=connection), pass_args=True))
    dispatcher.add_handler(CommandHandler(HEARTS, partial(send_hearts, hearts=filters[HEARTS])))
    dispatcher.add_handler(CommandHandler("set_hearts", partial(set_hearts, filter=filters[HEARTS]), pass_args=True))
    dispatcher.add_handler(CommandHandler("clean_filters", partial(clean_filters, filters=filters, connection=connection)))
    dispatcher.add_handler(CommandHandler("send_chart", partial(send_hearts_by_category, connection = connection)))
    
    # Echo any message that is not a command
    # dispatcher.add_handler(MessageHandler(~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()
