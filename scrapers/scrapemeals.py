import os
from dotenv import load_dotenv
import requests as rq
from lxml import html
import logging as logger
import sys
from datetime import datetime
import psycopg2
from psycopg2 import Error
from utils import *

def scrap_recipe(recipe: str, connection: psycopg2.extensions.connection, json_page=None) -> None:
    recipe_html = parse_html(recipe)
    if not recipe_html:
        logger.error(f"Can't parse the recipe {recipe}")
        return
    # know if a recipe with the same url is already in the database
    select_query = f"""
        SELECT UpdatedDate FROM Recipes WHERE RecipeURL = '{recipe}'
        """
    last_date = execute_fetch_query(select_query, connection)
    updated_date = tryExcept(recipe_html,"//time[contains(@class,'entry-modified')]/text()",0,True)
    updated_date = parse_date(updated_date)
    if last_date:
        last_date_str = last_date[0]['updateddate'].strftime('%Y-%m-%d')
        updated_date_str = updated_date.strftime('%Y-%m-%d')
        if last_date_str == updated_date_str:
            logger.info(f"Recipe {recipe} already in the database")
            return

    #ingredients = ', '.join([i.text for i in recipe_html.xpath("//div[contains(@class,'ingredients')]//ul/li") if i.text is not None])
    ingredients = tryExcept(recipe_html,"//div[contains(@class, 'ingredients')]",0,True)
    if ingredients is not None:
        ingredients = ingredients.text_content().replace("Ingredients","").replace("▢","")
    else:
        return

    hearts = 0

    title = tryExcept(recipe_html, "//h1[@class='entry-title']//text()", 0, True)
    if not title:
        logger.warning(f"Title not found for recipe {recipe}, skipping it")
        return
    # instructions = tryExcept(recipe_html,"//div[contains(@class,'instructions')]//text()",0,False)
    posted_date = tryExcept(recipe_html,"//time[contains(@class,'entry-time')]/text()",0,True)
    posted_date = parse_date(posted_date)
    # instructions_text = ''.join(instructions).strip()
    category = tryExcept(recipe_html,"//div[@class='breadcrumb']//span[2]//text()",0,True)
    prep_time = tryExcept(recipe_html,"//span[contains(@class, 'recipe-prep_time-minutes')]//text()",0,True)
    if prep_time is not None:
        prep_time = int(prep_time) #+ " minutes"
    else:
        logger.warning(f"Prep time not found for recipe {recipe}, skipping it")
        return
    total_time = tryExcept(recipe_html,"//span[contains(@class, 'recipe-cook_time-minutes')]//text()",0,True)
    if not total_time:
        total_time = tryExcept(recipe_html,"//span[contains(@class, 'recipe-cook_time-hours')]//text()",0,True)
        if total_time:
            total_time = prep_time + int(total_time) * 60
        else:
            total_time = prep_time
    else:
        total_time = prep_time + int(total_time)
    cuisine  = tryExcept(recipe_html,"//span[contains(@class, 'wprm-recipe-cuisine wprm-block-text-normal')]//text()",0,True)

    instructions = None #TODO
    image_url = tryExcept(recipe_html, "//img[contains(@src,'.jpg')]/@src", 0, True)



    insert_query = """
        INSERT INTO Recipes (Name, Category, Ingredients, RecipeURL, Instructions, ImageURL, PostedDate, UpdatedDate, Hearts, PrepTime, TotalTime, Cuisine)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    values = (title, category, ingredients, recipe, instructions, image_url, posted_date, updated_date, hearts, prep_time, total_time, cuisine)

    execute_insert_query(insert_query, connection, values)

    logger.info(f"Recipe '{title}' inserted into the database")

def main():
    load_dotenv()
    logger.basicConfig(stream=sys.stdout, level=logger.INFO)

    connection = get_connection()
    if not connection:
        logger.error(f"Error while connecting to PostgreSQL")
        return

    home_page = 'https://www.recipetineats.com/'
    home_html = parse_html(home_page)
    if not home_html:
        logger.error(f"Can't parse the home page {home_page}")
        return

    categories = home_html.xpath("//a[contains(@href,'category')]//@href")

    for category in categories:
        category_html = parse_html(category)
        if not category_html:
            logger.error(f"Can't parse the category {category}")
            continue
        scrap_category(category_html, connection, scrap_recipe)

    connection.close()


if __name__ == '__main__':
   main()
