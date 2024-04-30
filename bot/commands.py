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
import io

from telegram import Update, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, ConversationHandler

DISABLED = "DISABLED"
ENABLED = "ENABLED"
CATEGORIES = "CATEGORIES"
CUISINES = "CUISINES"
DATES = "DATES"
HEARTS = "HEARTS"
MIN = "MIN"
MAX = "MAX"
GET_CHART= range(1)
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

def send_menu_charts(update: Update, context: CallbackContext):
    reply_keyboard = [["1","2","3"]]
    context.bot.send_message(
    update.message.from_user.id,
    "🍰 Hey there! Are you curious about which recipes requires the least time and have received the most 'hearts'? Or perhaps you want to know which recipes are the user favorites? Here are some options you can explore through visual charts:\n\n"
    "*📊 Option 1:* Press or send *'1'* to discover recipes with the shortest cooking time and highest ratings!\n"
    "*📊 Option 2:* Press or send *'2'* ❤️ to explore the user-favorite recipes!\n"
    "*📊 Option 3:* Press or send *'3'* to delve into some fascinating charts and graphs!\n"
    "*📊Option 4:* Send '0' to CANCEL\n\n"
    "_Get ready to embark on a delightful journey through our dessert wonderland! 🍨🍩 Let's uncover some sweet surprises together! 😋✨_",
    parse_mode=ParseMode.MARKDOWN ,
    reply_markup = ReplyKeyboardMarkup(
        reply_keyboard, one_time_keyboard = True, input_field_placeholder ="Here"
        )
    )
    return GET_CHART

def get_chart(update: Update, context: CallbackContext):
    context.user_data["respuesta"] = update.message.text
    connection = get_connection()

    if context.user_data["respuesta"] == '1':
        send_hearts_by_category(update, context, connection)
    elif context.user_data["respuesta"] == '2':
        send_count_by_holiday(update, context, connection)
    elif context.user_data["respuesta"] == '3':
        pass
    else:
        update.message.reply_text("Oops! I didn't quite catch that. Please select an option from the menu.")

    update.message.reply_text(
        "*Hey there, foodie friend!* \n\n"
        "Just a quick heads-up that you can use the */set_filter* command to get a random ☘️ recipe from our massive database!  It's like having a culinary genie in your pocket! ✨\n\n"
        "And if you're craving more chart goodness, just send */get_menu_charts* again and I'll serve you up those options in no time! \n Happy culinary adventures! 🤖",
        parse_mode=ParseMode.MARKDOWN
        )
    return ConversationHandler.END

def send_count_by_holiday(update: Update, context: CallbackContext, connection: psycopg2.extensions.connection):
    """
    This handler send a predesigned graphic
    """
    try:
        count_by_holiday_result = execute_fetch_query(get_holidays_count(), connection)

        if count_by_holiday_result is None:
            update.message.reply_text("Something went wrong... Try again later.")
            return

        df =pd.DataFrame(count_by_holiday_result, columns=['summer_count', 'easter_count', 'christmas_count', "valentines_count"])
        counts = df.iloc[0].tolist()

        fig, ax = plt.subplots(figsize=(10, 6))
        plt.subplots_adjust(left=0.15, right=0.9, bottom=0.2, top=0.85)
        ax.bar(df.columns, counts, color = "#FF339F")
        ax.set_xlabel("HOLIDAYS")
        ax.set_ylabel("TOTAL RECIPES")
        ax.set_title("RECIPES BY HOLIDAYS")

        with io.BytesIO() as buffer:
            fig.savefig(buffer, format="png")
            buffer.seek(0)
            context.bot.send_message(
            update.message.from_user.id,
            "🪄 Here's the chart you've been waiting for! 🪄"
            )
            update.message.reply_photo(buffer.read())

    except Exception as e:
        context.bot.send_message(
            update.message.from_user.id,
            "An error occurred generating the chart. Please try again later."
        )
