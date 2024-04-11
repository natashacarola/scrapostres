import os
from dotenv import load_dotenv
import requests as rq
#from bs4 import BeautifulSoup
from lxml import html
import logging as logger
import sys
#import mysql.connector
from datetime import datetime
import psycopg2
from psycopg2 import Error
from utils import execute_insert_query


def request_page(page):
    our_headers = {
    'user-agent':
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'
    }
    return rq.get(page,headers = our_headers)

def parse_html(page):
    result = request_page(page)
    return html.fromstring(result.content)

def scrap_category(category_html, connector):
    recipes = category_html.xpath("//div[contains(@class,'content')]//a[contains(@class,'title')]/@href")
    for recipe in recipes:
        scrap_recipe(recipe, connector)

    category_next_page = has_next_page(category_html)
    if (category_next_page is not None):
        next_page_html = parse_html(category_next_page)
        scrap_category(next_page_html, connector)
    else:
        return


def scrap_recipe(recipe, connection):
    recipe_html = parse_html(recipe)
    try:
        title = recipe_html.xpath("//header[contains(@class,'recipes')]//h2[contains(@class,'title')]/text()")[0]
        # ingredients = recipe_html.xpath("//div[contains(@class,'ingredients')]//ul")[0]
        ingredients = ', '.join([i.text for i in recipe_html.xpath("//div[contains(@class,'ingredients')]//ul/li") if i.text is not None])
    except IndexError as e:
        title = None
        ingredients = None
    instructions = recipe_html.xpath("//div[contains(@class,'instructions')]//text()")
    category = recipe_html.xpath("//div[contains(@class,'details')]/span[contains(@class,'category')]")
    total_time = recipe_html.xpath("//span[contains(@class,'total')]/text()")
    total_time_text = "".join(total_time).strip()
    prep_time = recipe_html.xpath("//span[contains(@class,'prep')]/text()")
    # la url es recipe
    posted_date = recipe_html.xpath("//time[contains(@class,'entry-time')]/text()")
    posted_date_text = "".join(posted_date).strip()
    updated_date = recipe_html.xpath("//time[contains(@class,'entry-modified')]/text()")
    updated_date_text = "".join(updated_date).strip()
    cuisine = recipe_html.xpath("//span[contains(@class,'tasty-recipes-cuisine')]/text()")
    #cuisine_text = cuisine[0].strip()
    hearts = 0

    # TODO: Fix this
    # category = ', '.join([i.text for i in recipe_html.xpath("//div[contains(@class,'details')]/span[contains(@class,'category')]") if i.text is not None])
    # instructions = ' '.join([i.strip() for i in recipe_html.xpath("//div[contains(@class,'instructions')]//text()") if i.strip() != ''])
    # cuisine = ', '.join([i for i in recipe_html.xpath("//span[contains(@class,'tasty-recipes-cuisine')]/text()") if i.text is not None])
    # prep_time = ', '.join([i.text for i in recipe_html.xpath("//span[contains(@class,'prep')]/text()") if i.text is not None])

    # insert_query = """
    #     INSERT INTO Recipes (RecipeID, Name, Category, Ingredients, RecipeURL, PostedDate, UpdatedDate, Hearts, PrepTime, TotalTime, Cuisine)
    #     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    #     """
    
    # execute_insert_query(insert_query, connection, (None, title, category, ingredients, recipe, posted_date_text, updated_date_text, hearts, prep_time, total_time_text, cuisine))

def has_next_page(page_html):
    link = page_html.xpath("//li[contains(@class,'pagination-next')]/a/@href")
    if link:
        return link[0]
    else:
        return None

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

    categories = home_html.xpath("//a[contains(@href,'recipes')]/following-sibling::ul//a/@href")

    for category in categories:
        category_html = parse_html(category)
        scrap_category(category_html, connection)
    
    connection.close()


main()

