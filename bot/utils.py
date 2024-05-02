import time
import logging as logger
from typing import Optional, Union
import psycopg2
import os
from querys import *
import matplotlib.pyplot as plt
import pandas as pd
import io

from telegram import Update
from telegram.ext import CallbackContext


DISABLED = "DISABLED"
ENABLED = "ENABLED"

def get_connection() -> Union[psycopg2.extensions.connection, None]:
    try:
        connection = psycopg2.connect(
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            host=os.environ["POSTGRES_HOST"],
            port=os.environ["POSTGRES_PORT"],
            database=os.environ["POSTGRES_DB"],
        )

        connection.autocommit = True
        return connection
    except psycopg2.OperationalError as e:
        return None

def execute_fetch_query(query: str, connection: psycopg2.extensions.connection) -> Optional[list]:
    try:
        with connection.cursor() as cursor:

            # info_string = ""

            time_now = time.time()
            cursor.execute(query)
            exc_duration = round(round(time.time() - time_now, 4) * 1000, 1)
            # info_string += f"Query: {_beautify_query(query)} \n\t\tExecution time: {exc_duration} ms"

            if cursor.description is not None:
                column_names = [column[0] for column in cursor.description]
                data = [dict(zip(column_names, row)) for row in cursor.fetchall()]
            else:
                data = None

            # info_string += f"\n\tRows: {len(data)}"
            # info_string += f"\n\tFirst row: {data[:1]}\n"
            # logger.info(info_string)
        return data
    except psycopg2.Error as e:
        logger.error(f"Error executing query: {e}")
        return None

def create_recipe_html(recipe: dict) -> str:
    recipe_html = f"<b>🍽️ {recipe['name']}</b> 🍽️\n"
    recipe_html += f"<i>Category:</i> {recipe['category']}\n"
    if recipe['cuisine']:
        recipe_html += f"<i>Cuisine:</i> {recipe['cuisine']}\n"
    if recipe['preptime']:
        recipe_html += f"<i>Prep Time:</i> {recipe['preptime']} minutes\n"
    if recipe['totaltime']:
        recipe_html += f"<i>Total Time:</i> {recipe['totaltime']} minutes\n"
    if recipe['hearts']:
        recipe_html += f"<i>Hearts:</i> {recipe['hearts']} ❤️\n"
    recipe_html += f"<i>Find it here 👉🏻 </i> {recipe['recipeurl']}\n"
    return recipe_html

def load_filter(connection: psycopg2.extensions.connection, filter_name: str) -> Optional[dict]:
    filter = {}
    filter_result = execute_fetch_query(get_filter(filter_name), connection)
    if filter_result is None or len(filter_result) == 0:
        logger.error(f"No {filter_name} found")
        return None
    for res in filter_result:
        filter[res[filter_name.lower()]] = ENABLED
    return filter


def send_count_by_holiday(update: Update, context: CallbackContext, connection: psycopg2.extensions.connection) -> None:
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

    except Exception:
        context.bot.send_message(
            update.message.from_user.id,
            "An error occurred generating the chart. Please try again later."
        )

def send_recipes_by_posteddate(update: Update, context: CallbackContext, connection: psycopg2.extensions.connection, page: str) -> None:
    """
    This handler send a predesigned graphic
    """

    try:
        recipes_by_date = execute_fetch_query(get_recipes_by_posted_date(page), connection)

        if recipes_by_date is None:
            update.message.reply_text("Something went wrong... Try again later.")
            return

        df =pd.DataFrame(recipes_by_date, columns = ["year","count_recipes"])

        fig, ax =plt.subplots()
        ax.plot(df["year"], df["count_recipes"], color = "skyblue")
        ax.set_xlabel("YEAR")
        ax.set_ylabel("RECIPES")
        ax.set_title("Recipes uploaded through years")

        with io.BytesIO() as buffer:
            fig.savefig(buffer, format="png")
            buffer.seek(0)
            context.bot.send_message(
            update.message.from_user.id,
            "Got it! here's your chart! ✨✨"
            )
            update.message.reply_photo(buffer.read())

    except Exception as e:
        context.bot.send_message(
        update.message.from_user.id,
        "An error occurred generating the chart. Please try again later."
        )
        print(f"Error {e}")

def send_max_time_by_category(update: Update, context: CallbackContext, connection: psycopg2.extensions.connection) -> None:
    """
    This handler send a predesigned graphic
    """
    try:
        max_time_by_category = execute_fetch_query(get_max_time_by_category(), connection)

        if max_time_by_category is None:
            update.message.reply_text("Something went wrong... Try again later.")
            return

        df =pd.DataFrame(max_time_by_category, columns = ["category","max_total_time"])

        fig, ax =plt.subplots(figsize=(16, 6))
        plt.subplots_adjust(left=0.15, right=0.9, bottom=0.2, top=0.85)
        ax.barh(df["category"], df["max_total_time"], color = "green")
        ax.set_xlabel("TIME (MIN)")
        ax.set_ylabel("CATEGORY")
        ax.set_title("COOKING MAX TIME BY CATEGORY")

        with io.BytesIO() as buffer:
            fig.savefig(buffer, format="png")
            buffer.seek(0)
            context.bot.send_message(
            update.message.from_user.id,
            "Chart ready! ✅"
            )
            update.message.reply_photo(buffer.read())

    except Exception:
        context.bot.send_message(
            update.message.from_user.id,
            "An error occurred generating the chart. Please try again later."
        )

def send_hearts_by_category(update: Update, context: CallbackContext, connection: psycopg2.extensions.connection) -> None:
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
            "Check out this chart! 😄"
            )
            update.message.reply_photo(buffer.read())

    except Exception:
        context.bot.send_message(
            update.message.from_user.id,
            "An error occurred generating the chart. Please try again later."
        )
