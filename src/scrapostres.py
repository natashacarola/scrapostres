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

def filt_data_json(page_json):
    data_filt = []
    for page in page_json['pages']:
        try:
            ingredientes = page['recipe']['ingredientListHtml']
        except KeyError as e:
            ingredientes = None
        data_filt.append({'Url': page['url'],'Ingredients':ingredientes, 'Hearts': page['totalFavorites']})

    return data_filt

def request_api(api_url, params):
    respuesta = rq.get(api_url,params=params)
    if respuesta.status_code == 200 :
        return respuesta.json()
    else:
        logger.error(f"Can't do a request to: {api_url} || STATUS CODE: {respuesta.status_code}")
        return

def scrap_recipe(recipe, connection, json_page):
    recipe_html = parse_html(recipe)
    data_filt = filt_data_json(json_page)
    # know if a recipe with the same url is already in the database
    select_query = f"""
        SELECT UpdatedDate FROM Recipes WHERE RecipeURL = '{recipe}'
        """
    last_date = execute_fetch_query(select_query, connection)
    updated_date = tryExcept(recipe_html,"//time[contains(@class,'entry-modified')]/text()",0,True)
    if last_date and last_date[0] == updated_date:
        logger.info(f"Recipe {recipe} already in the database")
        return

    hearts = 0
    ingredients = []
    #instructions_text = ''

    title = tryExcept(recipe_html, "//header[contains(@class,'recipes')]//h2[contains(@class,'title')]/text()", 0, True)
    #instructions = tryExcept(recipe_html,"//div[contains(@class,'instructions')]//text()",0,False)
    posted_date = tryExcept(recipe_html,"//time[contains(@class,'entry-time')]/text()",0,True)
    category = tryExcept(recipe_html,"//span[contains(@class,'tasty-recipes-category')]/text()",0,True)
    total_time = tryExcept(recipe_html,"//span[contains(@class,'tasty-recipes-total')]/text()",0,True)
    prep_time = tryExcept(recipe_html,"//span[contains(@class,'tasty-recipes-prep')]/text()",0,True)
    cuisine  = tryExcept(recipe_html,"//span[contains(@class,'tasty-recipes-cuisine')]/text()",0,True)

    data_filt = filt_data_json(json_page)
    #try:
    #        instructions_text = ''.join(instructions).strip().split('Instructions')[1]
    #except IndexError as e:
    #        return

    for data in data_filt:
        if data['Url'] == recipe:
            ingredients = data['Ingredients']
            hearts = data['Hearts']

    # la url es recipe



    insert_query = """
        INSERT INTO Recipes (Name, Category, Ingredients, RecipeURL, PostedDate, UpdatedDate, Hearts, PrepTime, TotalTime, Cuisine)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    values = (title, category, ingredients, recipe, posted_date, updated_date, hearts, prep_time, total_time, cuisine)
    execute_insert_query(insert_query, connection, values)
    logger.info(f"Recipe '{title}' inserted in the database")

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

    home_page = 'https://www.sweetestmenu.com/'
    home_html = parse_html(home_page)

    url_api = 'https://c06f.app.slickstream.com/p/embed-site-info-v2'
    params_api = {
        "site": "9GRJKUB3"
    }
    json_page = request_api(url_api, params_api)
    categories = home_html.xpath("//a[contains(@href,'recipes')]/following-sibling::ul//a/@href")

    for category in categories:
        category_html = parse_html(category)
        scrap_category(category_html, connection, scrap_recipe, json_page)

    connection.close()


main()

