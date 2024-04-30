from datetime import datetime

def get_max_recipe_id() -> str:
    return "SELECT MAX(RecipeID) FROM Recipes"

def get_random_recipe(categories: list, cuisines: list, min_date_updated: datetime, max_date_updated: datetime, hearts: int) -> str:
    categories = ", ".join([f"'{category}'" for category in categories])
    cuisines = ", ".join([f"'{cuisine}'" for cuisine in cuisines])
    query = f"SELECT * FROM Recipes \
        WHERE Category IN ({categories}) \
        AND Cuisine IN ({cuisines}) \
        AND UpdatedDate >= '{min_date_updated}' \
        AND UpdatedDate <= '{max_date_updated}'"
    if hearts > 0:
        query += f" AND Hearts >= {hearts}"
    query += " ORDER BY RANDOM() LIMIT 1"
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
    return "SELECT SUM(CASE WHEN summer = true THEN 1 ELSE 0 END) AS summer_count, SUM(CASE WHEN easter = true THEN 1 ELSE 0 END) AS easter_count, SUM(CASE WHEN christmas = true THEN 1 ELSE 0 END) AS christmas_count, SUM(CASE WHEN valentines = true THEN 1 ELSE 0 END) AS valentines_count FROM holidays;"
