import os
from dotenv import load_dotenv
import requests as rq
from lxml import html
import logging as logger
import sys
import psycopg2
from psycopg2 import Error
from utils import *
from typing import Union

def filt_data_json(page_json: dict) -> list:
    data_filt = []
    for page in page_json['pages']:
        try:
            ingredientes = page['recipe']['ingredientListHtml']
        except KeyError as e:
            ingredientes = None
        #data_filt.append({'Url': page['url'],'Ingredients':ingredientes, 'Hearts': page['totalFavorites']})
        try:
            prep_time = page['recipe']['prepMinutes']
        except KeyError as e:
            prep_time = None
        try:
            total_time = page['recipe']['totalMinutes']
        except KeyError as e:
            total_time = None

        data_filt.append({'Url': page['url'],'Ingredients':ingredientes, 'Hearts': page['totalFavorites'], 'prepMinutes': prep_time, 'totalMinutes': total_time })

    return data_filt

def request_api(api_url: str, params: dict) -> Union[dict, None]:
    respuesta = rq.get(api_url,params=params)
    if respuesta.status_code == 200 :
        return respuesta.json()
    else:
        logger.error(f"Can't do a request to: {api_url} || STATUS CODE: {respuesta.status_code}")
        return None

def scrap_recipe(recipe: str, connection: psycopg2.extensions.connection, json_page: dict) -> None:
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

    hearts = 0
    ingredients = None
    total_time = None
    prep_time = None
    #instructions_text = ''

    title = tryExcept(recipe_html, "//header[contains(@class,'recipes')]//h2[contains(@class,'title')]/text()", 0, True)
    if not title:
        logger.warning(f"Title not found for recipe {recipe}, skipping it")
        return
    instructions = tryExcept(recipe_html,"//div[contains(@class,'instructions')]//text()",0,False)
    posted_date = tryExcept(recipe_html,"//time[contains(@class,'entry-time')]/text()",0,True)
    posted_date = parse_date(posted_date)
    category = tryExcept(recipe_html,"//span[contains(@class,'tasty-recipes-category')]/text()",0,True)
    cuisine  = tryExcept(recipe_html,"//span[contains(@class,'tasty-recipes-cuisine')]/text()",0,True)
    image_url = tryExcept(recipe_html, "//img[contains(@src,'.jpg')]/@src", 0, True)
    #total_time = tryExcept(recipe_html,"//span[contains(@class,'tasty-recipes-total')]/text()",0,True)
    #prep_time = tryExcept(recipe_html,"//span[contains(@class,'tasty-recipes-prep')]/text()",0,True)

    try:
        instructions_text = ''.join(instructions).split('Instructions')[1].strip()
    except IndexError as e:
        instructions_text = None

    data_filt = filt_data_json(json_page)

    for data in data_filt:
        if data['Url'] == recipe:
            ingredients = data['Ingredients']
            hearts = data['Hearts']
            prep_time = int(data['prepMinutes']) if data['prepMinutes'] is not None else None
            total_time = int(data['totalMinutes']) if data['totalMinutes'] is not None else None


    insert_query = """
        INSERT INTO Recipes (Name, Category, Ingredients, RecipeURL, Instructions, ImageURL, PostedDate, UpdatedDate, Hearts, PrepTime, TotalTime, Cuisine)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    values = (title, category, ingredients, recipe, instructions_text, image_url, posted_date, updated_date, hearts, prep_time, total_time, cuisine)
    execute_insert_query(insert_query, connection, values)
    logger.info(f"Recipe '{title}' inserted in the database")

def main():
    load_dotenv()
    logger.basicConfig(stream=sys.stdout, level=logger.INFO)

    connection = get_connection()
    if not connection:
        logger.error(f"Error while connecting to PostgreSQL: {e}")
        return

    home_page = 'https://www.sweetestmenu.com/'
    home_html = parse_html(home_page)
    if not home_html:
        logger.error(f"Can't parse the home page {home_page}")
        return

    url_api = 'https://c06f.app.slickstream.com/p/embed-site-info-v2'
    params_api = {
        "site": "9GRJKUB3"
    }
    json_page = request_api(url_api, params_api)
    categories = home_html.xpath("//a[contains(@href,'recipes')]/following-sibling::ul//a/@href")

    for category in categories:
        category_html = parse_html(category)
        if not category_html:
            logger.error(f"Can't parse the category {category}")
            continue
        scrap_category(category_html, connection, scrap_recipe, json_page)

    connection.close()


main()

