import time
import logging as logger


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
    logger.info(f"Query: {_beautify_query(query)} \n\tExecution time: {exc_duration} ms\n")

def execute_fetch_query(query, connection):
    cursor = connection.cursor()

    info_string = ""
    
    time_now = time.time()
    cursor.execute(query)
    exc_duration = round(round(time.time() - time_now, 4) * 1000, 1)
    info_string += f"Query: {_beautify_query(query)} \n\t\tExecution time: {exc_duration} ms"

    column_names = [column[0] for column in cursor.description]
    data = [dict(zip(column_names, row)) for row in cursor.fetchall()]

    info_string += f"\n\tRows: {len(data)}"
    info_string += f"\n\tFirst row: {data[:1]}\n"
    logger.info(info_string)
    cursor.close()
    return data