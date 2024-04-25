def get_max_recipe_id() -> str:
    return "SELECT MAX(RecipeID) FROM Recipes"

def get_random_recipe(categories: list) -> str:
    categories = ", ".join([f"'{category}'" for category in categories])
    return f"SELECT * FROM Recipes WHERE Category IN ({categories}) ORDER BY RANDOM() LIMIT 1"

def get_recipe_by_id(recipe_id: int) -> str:
    return f"SELECT * FROM Recipes WHERE RecipeID = {recipe_id}"

def get_categories() -> str:
    return "SELECT DISTINCT Category FROM Recipes"