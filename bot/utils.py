import time
import logging as logger
from typing import Optional, Union
import psycopg2
import os
from querys import *

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

def load_categories(connection: psycopg2.extensions.connection) -> Optional[dict]:
    categories = {}
    categories_result = execute_fetch_query(get_categories(), connection)
    if len(categories_result) == 0:
        logger.error("No categories found")
        return None
    for res in categories_result:
        categories[res["category"]] = ENABLED
    return categories
