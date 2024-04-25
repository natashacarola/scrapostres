from functools import partial
import logging as logger
import os
from dotenv import load_dotenv
import psycopg2
from utils import *
from querys import *
import random
import sys

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

    # Echo any message that is not a command
    # dispatcher.add_handler(MessageHandler(~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()