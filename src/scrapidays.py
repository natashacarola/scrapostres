import os
from dotenv import load_dotenv
import requests as rq
from lxml import html
import logging as logger
import sys
import psycopg2
from psycopg2 import Error
from typing import Optional
from utils import *

def scrap_holiday(holiday_name: str, holiday_html: html.HtmlElement, connector: psycopg2.extensions.connection) -> None:
    recipes = holiday_html.xpath("//div[contains(@class,'content')]//a[contains(@class,'title')]/@href")

    for recipe in recipes:
        select_query = f"""
            SELECT RecipeID FROM Recipes WHERE RecipeURL = '{recipe}'
            """
        recipe_id_result = execute_fetch_query(select_query, connector)
        
        if not recipe_id_result:
            logger.warn(f"Recipe {recipe} not found in the Recipes database, skipping")
            continue
        recipe_id = int(recipe_id_result[0]['recipeid'])
 
        # check if the recipe is already in the holiday
        select_query = f"""
            SELECT * FROM Holidays WHERE RecipeID = '{recipe_id}'
            """
        recipe_holiday_in_db = execute_fetch_query(select_query, connector)
        if not recipe_holiday_in_db:
            insert_query = """
                INSERT INTO Holidays (RecipeID, Valentines, Christmas, Easter, Summer)
                VALUES (%s, %s, %s, %s, %s)
                """
            values = (recipe_id, False, False, False, False)
            execute_insert_query(insert_query, connector, values)
            logger.info(f"Recipe {recipe} added to the Holidays table")

        # update the holiday
        update_query = f"""
            UPDATE Holidays
            SET {holiday_name} = True
            WHERE RecipeID = '{recipe_id}'
            """
        execute_insert_query(update_query, connector)
        logger.info(f"Recipe {recipe} updated in the Holidays table for {holiday_name}")

    holiday_next_page = has_next_page(holiday_html)
    if holiday_next_page is not None:
        next_page_html = parse_html(holiday_next_page)
        if next_page_html is not None:
            scrap_holiday(holiday_name, next_page_html, connector)

def main():
    load_dotenv()
    logger.basicConfig(stream=sys.stdout, level=logger.INFO)

    try:
        connection = psycopg2.connect(
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            host=os.environ["POSTGRES_HOST"],
            port=os.environ["POSTGRES_PORT"],
            database=os.environ["POSTGRES_DB"],
        )

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
        return

    recipes_page = 'https://www.sweetestmenu.com/recipes/'
    recipes_html = parse_html(recipes_page)
    if recipes_html is None:
        return
    holidays = recipes_html.xpath("//li[@id='menu-item-24786']//following-sibling::ul//a/@href")
    holidays_names = recipes_html.xpath("//li[@id='menu-item-24786']//following-sibling::ul//a//text()")

    for i in range(len(holidays)):
        url = holidays[i]
        holiday = holidays_names[i]
        holiday_html = parse_html(url)
        if holiday_html is None:
            logger.error(f"Can't parse the holiday {holiday}")
            continue
        scrap_holiday(holiday, holiday_html, connection)

    connection.close()


main()

