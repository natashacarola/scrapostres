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

DISABLED = "DISABLED"
ENABLED = "ENABLED"

def send_random_recipe(update: Update, context: CallbackContext, connection: psycopg2.extensions.connection, filters: dict) -> None:
    """
    This handler sends a random recipe from the database
    """
    categories = [category for category, status in filters["CATEGORIES"].items() if status == ENABLED]

    query = get_random_recipe(categories)
    recipe = execute_fetch_query(query, connection)
    if not recipe:
        context.bot.send_message(
            update.message.from_user.id,
            "There was an error fetching the recipe. Please try again later."
        )
        return
    recipe = recipe[0]
    recipe_html = create_recipe_html(recipe)
    context.bot.send_message(
        update.message.from_user.id,
        recipe_html,
        parse_mode=ParseMode.HTML
    )

def send_categories(update: Update, context: CallbackContext, categories: dict) -> None:
    """
    This handler sends the categories of the recipes and wheter they are enabled or disabled
    """
    message = "<b>Categories</b>\n"

    for category in sorted(categories.keys()):
        if categories[category] == ENABLED:
            message += f"🟢 {category}\n"
        else:
            message += f"🔴 {category}\n"

    context.bot.send_message(
        update.message.from_user.id,
        message,
        parse_mode=ParseMode.HTML
    )

def set_categories(update: Update, context: CallbackContext, categories: dict) -> None:
    """
    This handler sets the status of a list of categories
    """

    if len(context.args) == 0 or not context.args[0].upper() in [ENABLED, DISABLED]:
        context.bot.send_message(
            update.message.from_user.id,
            "Please indicate whether you want to enable or disable the categories.\n The status must be either 'ENABLED' or 'DISABLED'"
        )
        return
    status = context.args[0].upper()
    categories_to_set = context.args[1:] if len(context.args) > 1 else categories.keys()

    failed_categories = []
    for category in categories_to_set:
        category.replace("_", " ")
        if category in categories:
            categories[category] = status
        else:
            failed_categories.append(category)

    if failed_categories:
        context.bot.send_message(
            update.message.from_user.id,
            f"Failed to set the following categories: {', '.join(failed_categories)}\nPlease make sure you typed the category name correctly."
        )
    else:
        context.bot.send_message(
            update.message.from_user.id,
            f"All categories updated successfully"
        )

def send_hearts_by_category(update: Update, context: CallbackContext, connection: psycopg2.extensions.connection):
    """
    This handler send a predesigned graphic
    """
    try:
        hearts_by_category_result = execute_fetch_query(get_hearts_by_category(), connection)

        if hearts_by_category_result is None:
            update.message.reply_text("Something went wrong... Try again later.")
            return

        df =pd.DataFrame(hearts_by_category_result, columns = ["category","total_hearts"])
        df_sorted =df.sort_values(by = "total_hearts", ascending=False)
        df_sorted = df_sorted.head()

        fig, ax =plt.subplots(figsize=(8, 6))
        plt.subplots_adjust(left=0.15, right=0.9, bottom=0.2, top=0.85)
        ax.barh(df_sorted["category"], df_sorted["total_hearts"], color = "#FF339F")
        ax.set_xlabel("TOTAL HEARTS")
        ax.set_ylabel("CATEGORY")
        ax.set_title("RECIPES CATEGORIES WITH MORE HEARTS")

        with io.BytesIO() as buffer:
            fig.savefig(buffer, format="png")
            buffer.seek(0)
            context.bot.send_message(
            update.message.from_user.id,
            "This is the top 5 most liked! 😄"
            )
            update.message.reply_photo(buffer.read())

    except Exception as e:
        context.bot.send_message(
            update.message.from_user.id,
            "An error occurred generating the chart. Please try again later."
        )

def main() -> None:
    load_dotenv()
    logger.basicConfig(stream=sys.stdout, level=logger.INFO)
    connection = get_connection()
    updater = Updater(token=os.environ["BOT_TOKEN"])

    categories = load_categories(connection)
    if not categories:
        return

    filters = {"CATEGORIES": categories}

    # Get the dispatcher to register handlers
    # Then, we register each handler and the conditions the update must meet to trigger it
    dispatcher = updater.dispatcher

    # Register commands
    dispatcher.add_handler(CommandHandler("random_recipe", partial(send_random_recipe, connection=connection, filters=filters)))
    dispatcher.add_handler(CommandHandler("categories", partial(send_categories, categories=categories)))
    dispatcher.add_handler(CommandHandler("set_categories", partial(set_categories, categories=categories), pass_args=True))
    dispatcher.add_handler(CommandHandler("send_chart", partial(send_hearts_by_category, connection = connection)))
    # Echo any message that is not a command
    # dispatcher.add_handler(MessageHandler(~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()
