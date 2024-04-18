import time
import logging as logger
from typing import Optional
import requests as rq
from lxml import html

def _beautify_query(query):
    query = ' '.join(query.split())
    query = query.replace("  ", " ")
    return query

def execute_insert_query(query, connection, values=None):
    with connection.cursor() as cursor:    
        time_now = time.time()  
        if values:
            cursor.execute(query, values)
        else:
            cursor.execute(query)
    connection.commit()
    exc_duration = round(round(time.time() - time_now, 4) * 1000, 1)
    # logger.info(f"Query: {_beautify_query(query)} \n\tExecution time: {exc_duration} ms\n")

def execute_fetch_query(query, connection):
    cursor = connection.cursor()

    # info_string = ""
    
    time_now = time.time()
    cursor.execute(query)
    exc_duration = round(round(time.time() - time_now, 4) * 1000, 1)
    # info_string += f"Query: {_beautify_query(query)} \n\t\tExecution time: {exc_duration} ms"

    column_names = [column[0] for column in cursor.description]
    data = [dict(zip(column_names, row)) for row in cursor.fetchall()]

    # info_string += f"\n\tRows: {len(data)}"
    # info_string += f"\n\tFirst row: {data[:1]}\n"
    # logger.info(info_string)
    cursor.close()
    return data

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
    
def tryExcept(page,data,index,boolean):
    try:
        if(boolean):
            return  page.xpath(data)[index]
        else:
            return page.xpath(data)
    except IndexError as e:
        return None

def scrap_category(category_html, connector, scraper_func, json_page=None):
    recipes = category_html.xpath("//div[contains(@class,'content')]//a[contains(@class,'title')]/@href")
    for recipe in recipes:
        scraper_func(recipe, connector, json_page)

    category_next_page = has_next_page(category_html)
    if (category_next_page is not None):
        next_page_html = parse_html(category_next_page)
        scrap_category(next_page_html, connector, json_page)
    else:
        return