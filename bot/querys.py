from datetime import datetime

def get_max_recipe_id() -> str:
    return "SELECT MAX(RecipeID) FROM Recipes"

def get_random_recipe(categories: list, cuisines: list, min_date_updated: datetime, max_date_updated: datetime, hearts: int, min_time: int, max_time: int) -> str:
    categories = ", ".join([f"'{category}'" for category in categories])
    cuisines = ", ".join([f"'{cuisine}'" for cuisine in cuisines])
    query = f"SELECT * FROM Recipes \
        WHERE Category IN ({categories}) \
        AND Cuisine IN ({cuisines}) \
        AND UpdatedDate >= '{min_date_updated}' \
        AND UpdatedDate <= '{max_date_updated}' \
        AND TotalTime >= {min_time}"
    if hearts > 0:
        query += f" AND Hearts >= {hearts}"
    if max_time > 0:
        query += f" AND TotalTime <= {max_time}"
    query += " ORDER BY RANDOM() LIMIT 1"
    return query

def get_top_recipe(categories: list, cuisines: list, min_date_updated: datetime, max_date_updated: datetime, hearts: int, min_time: int, max_time: int, order_by: str) -> str:
    categories = ", ".join([f"'{category}'" for category in categories])
    cuisines = ", ".join([f"'{cuisine}'" for cuisine in cuisines])
    query = f"SELECT * FROM Recipes \
        WHERE Category IN ({categories}) \
        AND Cuisine IN ({cuisines}) \
        AND UpdatedDate >= '{min_date_updated}' \
        AND UpdatedDate <= '{max_date_updated}' \
        AND TotalTime >= {min_time}"
    if hearts > 0:
        query += f" AND Hearts >= {hearts}"
    if max_time > 0:
        query += f" AND TotalTime <= {max_time}"
    query += f" ORDER BY {order_by} DESC LIMIT 1"
    return query

def get_random_holiday_recipe(categories: list, cuisines: list, min_date_updated: datetime, max_date_updated: datetime, hearts: int, min_time: int, max_time: int, valentines: bool, christmas: bool, easter: bool, summer: bool) -> str:
    categories = ", ".join([f"'{category}'" for category in categories])
    cuisines = ", ".join([f"'{cuisine}'" for cuisine in cuisines])
    query = f"SELECT * FROM Recipes \
        WHERE RecipeID IN ( \
            SELECT RecipeID FROM Holidays \
            WHERE Valentines = {valentines} \
            AND Christmas = {christmas} \
            AND Easter = {easter} \
            AND Summer = {summer} \
        ) \
        AND Category IN ({categories}) \
        AND Cuisine IN ({cuisines}) \
        AND UpdatedDate >= '{min_date_updated}' \
        AND UpdatedDate <= '{max_date_updated}' \
        AND TotalTime >= {min_time} \
        AND Hearts >= {hearts}"
    if max_time > 0:
        query += f" AND TotalTime <= {max_time}"
    query += " ORDER BY RANDOM() LIMIT 1"
    return query

def get_top_holiday_recipe(categories: list, cuisines: list, min_date_updated: datetime, max_date_updated: datetime, hearts: int, min_time: int, max_time: int, valentines: bool, christmas: bool, easter: bool, summer: bool, order_by: str) -> str:
    categories = ", ".join([f"'{category}'" for category in categories])
    cuisines = ", ".join([f"'{cuisine}'" for cuisine in cuisines])
    query = f"SELECT * FROM Recipes \
        WHERE RecipeID IN ( \
            SELECT RecipeID FROM Holidays \
            WHERE Valentines = {valentines} \
            AND Christmas = {christmas} \
            AND Easter = {easter} \
            AND Summer = {summer} \
        ) \
        AND Category IN ({categories}) \
        AND Cuisine IN ({cuisines}) \
        AND UpdatedDate >= '{min_date_updated}' \
        AND UpdatedDate <= '{max_date_updated}' \
        AND TotalTime >= {min_time} \
        AND Hearts >= {hearts}"
    if max_time > 0:
        query += f" AND TotalTime <= {max_time}"
    query += f" ORDER BY {order_by} DESC LIMIT 1"
    return query

def get_recipe_by_id(recipe_id: int) -> str:
    return f"SELECT * FROM Recipes WHERE RecipeID = {recipe_id}"

def get_filter(filter_name: str) -> str:
    return f"SELECT DISTINCT {filter_name} FROM Recipes"

def get_oldest_updated_date() -> str:
    return "SELECT MIN(UpdatedDate) FROM Recipes"

def get_newest_updated_date() -> str:
    return "SELECT MAX(UpdatedDate) FROM Recipes"

def get_categories() -> str:
    return "SELECT DISTINCT Category FROM Recipes"

def get_hearts_by_category() -> str:
    return "SELECT category, SUM(hearts) as total_hearts FROM recipes GROUP BY category HAVING SUM(hearts) > 0"

def get_holidays_count() -> str:
    return "SELECT SUM(CASE WHEN summer = true THEN 1 ELSE 0 END) AS summer_count, SUM(CASE WHEN easter = true THEN 1 ELSE 0 END) AS easter_count, SUM(CASE WHEN christmas = true THEN 1 ELSE 0 END) AS christmas_count, SUM(CASE WHEN valentines = true THEN 1 ELSE 0 END) AS valentines_count FROM holidays"

def get_recipes_by_posted_date(page)-> str:
    return f"SELECT EXTRACT(YEAR FROM posteddate) AS year, COUNT(recipeid) AS count_recipes FROM recipes WHERE recipeurl like '%{page}%' GROUP BY EXTRACT(YEAR FROM posteddate) ORDER BY EXTRACT(YEAR FROM posteddate)"

def get_max_time_by_category() -> str:
  return "SELECT DISTINCT category, MAX(totaltime) as max_total_time FROM recipes WHERE totaltime IS NOT NULL GROUP BY category ORDER BY max_total_time DESC LIMIT 5"
