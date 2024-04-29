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

from telegram import Update, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

DISABLED = "DISABLED"
ENABLED = "ENABLED"
CATEGORIES = "CATEGORIES"
CUISINES = "CUISINES"
DATES = "DATES"
HEARTS = "HEARTS"
MIN = "MIN"
MAX = "MAX"

def send_random_recipe(update: Update, context: CallbackContext, connection: psycopg2.extensions.connection, filters: dict) -> None:
    """
    This handler sends a random recipe from the database
    """
    categories = [category for category, status in filters[CATEGORIES].items() if status == ENABLED]
    cuisines = [cuisine for cuisine, status in filters[CUISINES].items() if status == ENABLED]
    min_date_updated = filters[DATES][MIN]
    max_date_updated = filters[DATES][MAX]
    hearts = filters[HEARTS].pop()
    filters[HEARTS].add(hearts)

    query = get_random_recipe(categories, cuisines, min_date_updated, max_date_updated, hearts)
    recipe = execute_fetch_query(query, connection)
    if not recipe:
        context.bot.send_message(
            update.message.from_user.id,
            "I couldn't find any recipe with the given filters. Please try again with different filters."
        )
        return
    recipe = recipe[0]
    recipe_html = create_recipe_html(recipe)
    context.bot.send_message(
        update.message.from_user.id,
        recipe_html,
        parse_mode=ParseMode.HTML
    )

def send_filter(update: Update, context: CallbackContext, filter: dict, name: str) -> None:
    """
    This handler sends the list of some filter of the recipes and whether they are enabled or disabled
    """
    message = f"<b>{name.capitalize()}</b>\n"

    keys = {}
    for k in filter.keys():
        if k is not None:
            keys[k.title()] = k

    for k in sorted(keys.keys()):
        category = keys[k]
        if filter[category] == ENABLED:
            message += f"🟢 {k}\n"
        else:
            message += f"🔴 {k}\n"

    context.bot.send_message(
        update.message.from_user.id,
        message,
        parse_mode=ParseMode.HTML
    )

def set_filter(update: Update, context: CallbackContext, filter: dict, name: str) -> None:
    """
    This handler sets the status of a list of some filter of the recipes
    """
    
    if len(context.args) == 0 or not context.args[0].upper() in [ENABLED, DISABLED]:
        context.bot.send_message(
            update.message.from_user.id,
            "Please indicate whether you want to enable or disable.\n The status must be either 'ENABLED' or 'DISABLED'"
        )
        return
    status = context.args[0].upper()
    list_to_set = context.args[1:] if len(context.args) > 1 else filter.keys()
    list_to_set = [f for f in list_to_set if f is not None]

    failed_ones = []
    for f in list_to_set:
        f.replace("_", " ")
        if f in filter:
            filter[f] = status
        else:
            failed_ones.append(f)

    if failed_ones:
        context.bot.send_message(
            update.message.from_user.id,
            f"Failed to set the following: {', '.join(failed_ones)}\nPlease make sure you typed each name correctly."
        )
    else:
        context.bot.send_message(
            update.message.from_user.id,
            f"All {name.lower()} updated successfully"
        )

def send_dates(update: Update, context: CallbackContext, filter: dict) -> None:
    """
    This handler sends the oldest and newest updated dates of the recipes
    """
    message = "<b>Updated Dates Allowed</b>\n"
    message += f"Oldest: {filter[MIN].strftime('%Y-%m-%d')}\n"
    message += f"Newest: {filter[MAX].strftime('%Y-%m-%d')}\n"

    context.bot.send_message(
        update.message.from_user.id,
        message,
        parse_mode=ParseMode.HTML
    )

def set_dates(update: Update, context: CallbackContext, connection: psycopg2.extensions.connection, filters: dict) -> None:
    """
    This handler sets the oldest and newest updated dates of the recipes
    """
    if len(context.args) == 1 or len(context.args) > 2:
        context.bot.send_message(
            update.message.from_user.id,
            "Please provide only two dates: the oldest and the newest. You can also not provide any dates to reset them to the default values."
        )
        return
    
    if len(context.args) == 0:
        oldest_updated_date = execute_fetch_query(get_oldest_updated_date(), connection)[0]["min"]
        newest_updated_date = execute_fetch_query(get_newest_updated_date(), connection)[0]["max"]
        filters[DATES] = {MIN: oldest_updated_date, MAX: newest_updated_date}
        context.bot.send_message(
            update.message.from_user.id,
            "Dates reset to the default values"
        )
        return
    
    try:
        oldest_updated_date = datetime(*[int(i) for i in context.args[0].split("-")])
        newest_updated_date = datetime(*[int(i) for i in context.args[1].split("-")])
    except ValueError:
        context.bot.send_message(
            update.message.from_user.id,
            "Please provide the dates in the format 'YYYY-MM-DD'"
        )
        return
    
    filters[DATES][MIN] = oldest_updated_date
    filters[DATES][MAX] = newest_updated_date
    context.bot.send_message(
        update.message.from_user.id,
        "Dates updated successfully"
    )

def send_hearts(update: Update, context: CallbackContext, hearts: set) -> None:
    """
    This handler sends the number of hearts the user has
    """
    n_hearts = hearts.pop()
    hearts.add(n_hearts)
    context.bot.send_message(
        update.message.from_user.id,
        f"The minimum number of hearts is {n_hearts}"
    )

def set_hearts(update: Update, context: CallbackContext, filter: set) -> None:
    """
    This handler sets the minimum number of hearts the user wants
    """
    if len(context.args) != 1:
        context.bot.send_message(
            update.message.from_user.id,
            "Please provide only one number"
        )
        return
    
    try:
        hearts = int(context.args[0])
    except ValueError:
        context.bot.send_message(
            update.message.from_user.id,
            "Please provide a valid number"
        )
        return
    
    filter.pop()
    filter.add(hearts)
    context.bot.send_message(
        update.message.from_user.id,
        "Hearts updated successfully"
    )

def clean_filters(update: Update, context: CallbackContext, connection: psycopg2.extensions.connection, filters: dict) -> None:
    """
    This handler cleans the filters
    """
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
    context.bot.send_message(
        update.message.from_user.id,
        "Filters cleaned successfully"
    )