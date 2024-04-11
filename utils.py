import time
import logging as logger
import mysql

#traer las cosas de la tabla
def execute_fetch_query(query, connection):
    cursor = connection.cursor()

    info_string = "\t"

    time_now = time.time()
    cursor.execute(query)
    exc_duration = round(round(time.time() - time_now, 4) * 1000, 1)
    info_string += f"Query: {_beautify_query(query)} \n\t\tExecution time: {exc_duration} ms"

    column_names = [column[0] for column in cursor.description]
    data = [dict(zip(column_names, row)) for row in cursor.fetchall()]

    info_string += f"\n\t\tRows: {len(data)}"
    info_string += f"\n\t\tFirst row: {data[:1]}"
    logger.info(info_string)
    cursor.close()
    connection.close()
    return data

#insertar cosas en la tabla
def execute_insert_query(query, connection, values=None):

    # connection = MySQLConnectionPool.get_instance().get_connection()

    cursor = connection.cursor()

    time_now = time.time()
    if values:
        cursor.execute(query, values)
    else:
        cursor.execute(query)
    connection.commit()
    exc_duration = round(round(time.time() - time_now, 4) * 1000, 1)
    logger.info(f"\tQuery: {_beautify_query(query)} \n\t\tExecution time: {exc_duration} ms")

    cursor.close()
    connection.close()

def _beautify_query(query):
    query = ' '.join(query.split())
    query = query.replace("  ", " ")
    return query
