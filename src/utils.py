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
    logger.info(f"\tQuery: {_beautify_query(query)} \n\t\tExecution time: {exc_duration} ms")