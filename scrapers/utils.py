import time
import logging as logger
from typing import Optional, Union
import requests as rq
from lxml import html
import psycopg2
import os
from typing import Callable, Any
import re
from datetime import date

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

def _beautify_query(query: str) -> str:
    query = ' '.join(query.split())
    query = query.replace("  ", " ")
    return query

def execute_insert_query(query: str, connection: psycopg2.extensions.connection, values=None) -> None:
    try:
        with connection.cursor() as cursor:
            time_now = time.time()
            if values:
                cursor.execute(query, values)
            else:
                cursor.execute(query)
        exc_duration = round(round(time.time() - time_now, 4) * 1000, 1)
        # logger.info(f"Query: {_beautify_query(query)} \n\tExecution time: {exc_duration} ms\n")
    except psycopg2.Error as e:
        logger.error(f"Error executing query: {e}")

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

def _request_page(page: str) -> Optional[rq.Response]:
    our_headers = {
    'user-agent':
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'
    }
    respuesta = rq.get(page,headers = our_headers)
    if respuesta.status_code == 200:
        return respuesta
    else:
        logger.error(f"Can't do a request to: {page} || STATUS CODE: {respuesta.status_code}")
        return None

def parse_html(page: str) -> Optional[html.HtmlElement]:
    result = _request_page(page)
    if result is None:
        return None
    return html.fromstring(result.content)

def has_next_page(page_html: html.HtmlElement) -> Optional[str]:
    link = page_html.xpath("//li[contains(@class,'pagination-next')]/a/@href")
    if link:
        return link[0]
    else:
        return None

def tryExcept(page: html.HtmlElement, data: str, index: int, boolean: bool):
    try:
        if(boolean):
            return  page.xpath(data)[index]
        else:
            return page.xpath(data)
    except IndexError as e:
        return None

def scrap_category(category_html: html.HtmlElement, connector: psycopg2.extensions.connection, scraper_func: Callable[[str, psycopg2.extensions.connection, Any], None], json_page=None) -> None:
    recipes = category_html.xpath("//div[contains(@class,'content')]//a[contains(@class,'title')]/@href")
    for recipe in recipes:
        scraper_func(recipe, connector, json_page)

    category_next_page = has_next_page(category_html)
    if (category_next_page is not None):
        next_page_html = parse_html(category_next_page)
        if next_page_html is not None:
            scrap_category(next_page_html, connector, scraper_func, json_page)

def parse_date(date_obtained):
    # dates examples 3/03/19 o 31 Jan '23
    months = {
        "Jan" : 1,
        "Feb" : 2,
        "Mar" : 3,
        "Apr" : 4,
        "May" : 5,
        "Jun" : 6,
        "Jul" : 7,
        "Aug" : 8,
        "Sep" : 9,
        "Oct" : 10,
        "Nov" : 11,
        "Dec" : 12
    }
    regex_date = r"(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) '(\d{2})"
    match = re.match(regex_date,date_obtained)
    if (match):
        d, m, y = match.groups()
        day = int(d)
        month = months[m]
        year = int(y) + 2000
        new_date = date(year,month,day)
        return new_date
    else:
        date_parts = date_obtained.strip().split("/")
        month, day, year = map(int, date_parts)
        year += 2000
        new_date = date(year,month,day)
        return new_date
