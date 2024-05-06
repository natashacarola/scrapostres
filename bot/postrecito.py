from datetime import datetime
from functools import partial
import logging as logger
import os
from dotenv import load_dotenv
from utils import *
from querys import *
import sys


from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

from commands import *

load_dotenv()

DISABLED = os.environ["DISABLED"]
ENABLED = os.environ["ENABLED"]
CATEGORIES = os.environ["CATEGORIES"]
CUISINES = os.environ["CUISINES"]
DATES = os.environ["DATES"]
HEARTS = os.environ["HEARTS"]
TIME = os.environ["TIME"]
VALENTINES = os.environ["VALENTINES"]
CHRISTMAS = os.environ["CHRISTMAS"]
EASTER = os.environ["EASTER"]
SUMMER = os.environ["SUMMER"]
HOLIDAYS = os.environ["HOLIDAYS"]
MIN = os.environ["MIN"]
MAX = os.environ["MAX"]
GET_CHART = range(1)

def wrong_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Wrong command, please try again")

def not_a_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("That's not a command, I'm a bot, I only understand commands\nTry with /random_recipe 😉")

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
    filters[TIME] = {MIN: 0, MAX: -1}
    filters[HEARTS] = set()
    filters[HEARTS].add(0)
    filters[HOLIDAYS] = {VALENTINES: True, CHRISTMAS: True, EASTER: True, SUMMER: True}

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
    dispatcher.add_handler(CommandHandler(TIME, partial(send_time, time=filters[TIME])))
    dispatcher.add_handler(CommandHandler("set_time", partial(set_time, filter=filters[TIME]), pass_args=True))
    dispatcher.add_handler(CommandHandler(HOLIDAYS, partial(send_holidays, filter=filters[HOLIDAYS])))
    dispatcher.add_handler(CommandHandler("set_holidays", partial(set_holidays, filter=filters[HOLIDAYS]), pass_args=True))
    dispatcher.add_handler(CommandHandler("random_holiday_recipe", partial(send_random_holiday_recipe, connection=connection, filters=filters)))
    dispatcher.add_handler(CommandHandler("top_holiday_recipe", partial(send_top_holiday_recipe, connection=connection, filters=filters), pass_args=True))
    dispatcher.add_handler(CommandHandler("top_recipe", partial(send_top_recipe, connection=connection, filters=filters), pass_args=True))
    dispatcher.add_handler(CommandHandler("start", start))
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("send_menu_charts",send_menu_charts )],
        states = {
            GET_CHART: [MessageHandler(Filters.text, get_chart)]
        },
        fallbacks = []
    )
    dispatcher.add_handler(conversation_handler)
    dispatcher.add_handler(MessageHandler(Filters.command, wrong_command))
    dispatcher.add_handler(MessageHandler(~Filters.command, not_a_command))
    # Echo any message that is not a command
    # dispatcher.add_handler(MessageHandler(~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()
