def get_max_recipe_id() -> str:
    return "SELECT MAX(RecipeID) FROM Recipes"

def get_recipe_by_id(recipe_id: int) -> str:
    return f"SELECT * FROM Recipes WHERE RecipeID = {recipe_id}"