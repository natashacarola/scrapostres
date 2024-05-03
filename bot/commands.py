from datetime import datetime
import re
from dotenv import load_dotenv
import psycopg2
from utils import *
from querys import *

from telegram import Update, ParseMode, ReplyKeyboardMarkup
from telegram.ext import  CallbackContext, ConversationHandler
import os

load_dotenv()

DISABLED = os.environ["DISABLED"]
ENABLED = os.environ["ENABLED"]
CATEGORIES = os.environ["CATEGORIES"]
CUISINES = os.environ["CUISINES"]
DATES = os.environ["DATES"]
HEARTS = os.environ["HEARTS"]
TIME = os.environ["TIME"]
VALENTINES = os.environ["VALENTINES"]
CHRISTMAS = os.environ["CHRISTMAS"]
EASTER = os.environ["EASTER"]
SUMMER = os.environ["SUMMER"]
HOLIDAYS = os.environ["HOLIDAYS"]
MIN = os.environ["MIN"]
MAX = os.environ["MAX"]
GET_CHART= range(1)

def send_random_recipe(update: Update, context: CallbackContext, connection: psycopg2.extensions.connection, filters: dict) -> None:
    """
    This handler sends a random recipe from the database
    """
    categories = [category for category, status in filters[CATEGORIES].items() if status == ENABLED]
    cuisines = [cuisine for cuisine, status in filters[CUISINES].items() if status == ENABLED]
    min_date_updated = filters[DATES][MIN]
    max_date_updated = filters[DATES][MAX]
    min_time = filters[TIME][MIN]
    max_time = filters[TIME][MAX]
    hearts = filters[HEARTS].pop()
    filters[HEARTS].add(hearts)

    query = get_random_recipe(categories, cuisines, min_date_updated, max_date_updated, hearts, min_time, max_time)
    recipe = execute_fetch_query(query, connection)
    if not recipe:
        context.bot.send_message(
            update.message.from_user.id,
            "I couldn't find any recipe with the given filters. Please try again with different filters."
        )
        return
    recipe = recipe[0]
    recipe_html = create_recipe_html(recipe)
    context.bot.send_message(
        update.message.from_user.id,
        recipe_html,
        parse_mode=ParseMode.HTML
    )

def send_top_recipe(update: Update, context: CallbackContext, connection: psycopg2.extensions.connection, filters: dict) -> None:
    """
    This handler sends a recipe from the database sorted by a parameter
    """
    sort_columns = {DATES: "UpdatedDate", HEARTS: "Hearts", TIME: "TotalTime"}
    if not context.args or context.args[0].upper() not in sort_columns.keys():
        context.bot.send_message(
            update.message.from_user.id,
            "Please provide a valid sorting parameter: 'dates', 'hearts' or 'time'. You can also add an extra parameter 'min' or 'max' if you want the top max or top min.\n Example: /top_recipe dates min"
        )
        return
    order_by = sort_columns[context.args[0].upper()]
    if len(context.args) > 1:
        if context.args[1].upper() == "MIN":
            order_by += " ASC"
        elif context.args[1].upper() == "MAX":
            order_by += " DESC"
        else:
            context.bot.send_message(
                update.message.from_user.id,
                "Please provide a valid extra parameter: 'min' or 'max'"
            )
            return
    else:
        order_by += " DESC"

    categories = [category for category, status in filters[CATEGORIES].items() if status == ENABLED]
    cuisines = [cuisine for cuisine, status in filters[CUISINES].items() if status == ENABLED]
    min_date_updated = filters[DATES][MIN]
    max_date_updated = filters[DATES][MAX]
    min_time = filters[TIME][MIN]
    max_time = filters[TIME][MAX]
    hearts = filters[HEARTS].pop()
    filters[HEARTS].add(hearts)

    query = get_top_recipe(categories, cuisines, min_date_updated, max_date_updated, hearts, min_time, max_time, order_by)
    recipe = execute_fetch_query(query, connection)
    if not recipe:
        context.bot.send_message(
            update.message.from_user.id,
            "I couldn't find any recipe with the given filters. Please try again with different filters."
        )
        return
    recipe = recipe[0]
    recipe_html = create_recipe_html(recipe)
    context.bot.send_message(
        update.message.from_user.id,
        recipe_html,
        parse_mode=ParseMode.HTML
    )

def send_random_holiday_recipe(update: Update, context: CallbackContext, connection: psycopg2.extensions.connection, filters: dict) -> None:
    """
    This handler sends a random recipe from the database that matches the holidays
    """
    categories = [category for category, status in filters[CATEGORIES].items() if status == ENABLED]
    cuisines = [cuisine for cuisine, status in filters[CUISINES].items() if status == ENABLED]
    min_date_updated = filters[DATES][MIN]
    max_date_updated = filters[DATES][MAX]
    min_time = filters[TIME][MIN]
    max_time = filters[TIME][MAX]
    hearts = filters[HEARTS].pop()
    filters[HEARTS].add(hearts)
    valentines = filters[HOLIDAYS][VALENTINES]
    christmas = filters[HOLIDAYS][CHRISTMAS]
    easter = filters[HOLIDAYS][EASTER]
    summer = filters[HOLIDAYS][SUMMER]

    query = get_random_holiday_recipe(categories, cuisines, min_date_updated, max_date_updated, hearts, min_time, max_time, valentines, christmas, easter, summer)
    recipe = execute_fetch_query(query, connection)
    if not recipe:
        context.bot.send_message(
            update.message.from_user.id,
            "I couldn't find any recipe with the given filters. Please try again with different filters."
        )
        return
    recipe = recipe[0]
    recipe_html = create_recipe_html(recipe)
    context.bot.send_message(
        update.message.from_user.id,
        recipe_html,
        parse_mode=ParseMode.HTML
    )

def send_top_holiday_recipe(update: Update, context: CallbackContext, connection: psycopg2.extensions.connection, filters: dict) -> None:
    """
    This handler sends a recipe from the database that matches the holidays and is sorted by a parameter
    """
    sort_columns = {DATES: "UpdatedDate", HEARTS: "Hearts", TIME: "TotalTime"}
    if not context.args or context.args[0].upper() not in sort_columns.keys():
        context.bot.send_message(
            update.message.from_user.id,
            "Please provide a valid sorting parameter: 'dates', 'hearts' or 'time'. You can also add an extra parameter 'min' or 'max' if you want the top max or top min.\n Example: /top_holiday_recipe dates min"
        )
        return
    order_by = sort_columns[context.args[0].upper()]
    if len(context.args) > 1:
        if context.args[1].upper() == "MIN":
            order_by += " ASC"
        elif context.args[1].upper() == "MAX":
            order_by += " DESC"
        else:
            context.bot.send_message(
                update.message.from_user.id,
                "Please provide a valid extra parameter: 'min' or 'max'"
            )
            return
    else:
        order_by += " DESC"

    categories = [category for category, status in filters[CATEGORIES].items() if status == ENABLED]
    cuisines = [cuisine for cuisine, status in filters[CUISINES].items() if status == ENABLED]
    min_date_updated = filters[DATES][MIN]
    max_date_updated = filters[DATES][MAX]
    min_time = filters[TIME][MIN]
    max_time = filters[TIME][MAX]
    hearts = filters[HEARTS].pop()
    filters[HEARTS].add(hearts)
    valentines = filters[HOLIDAYS][VALENTINES]
    christmas = filters[HOLIDAYS][CHRISTMAS]
    easter = filters[HOLIDAYS][EASTER]
    summer = filters[HOLIDAYS][SUMMER]

    query = get_top_holiday_recipe(categories, cuisines, min_date_updated, max_date_updated, hearts, min_time, max_time, valentines, christmas, easter, summer, order_by)
    recipe = execute_fetch_query(query, connection)
    if not recipe:
        context.bot.send_message(
            update.message.from_user.id,
            "I couldn't find any recipe with the given filters. Please try again with different filters."
        )
        return
    recipe = recipe[0]
    recipe_html = create_recipe_html(recipe)
    context.bot.send_message(
        update.message.from_user.id,
        recipe_html,
        parse_mode=ParseMode.HTML
    )

def send_filter(update: Update, context: CallbackContext, filter: dict, name: str) -> None:
    """
    This handler sends the list of some filter of the recipes and whether they are enabled or disabled
    """
    message = f"<b>{name.capitalize()}</b>\n"

    keys = {}
    for k in filter.keys():
        if k is not None:
            keys[k.title()] = k

    for k in sorted(keys.keys()):
        category = keys[k]
        if filter[category] == ENABLED:
            message += f"🟢 {k}\n"
        else:
            message += f"🔴 {k}\n"

    context.bot.send_message(
        update.message.from_user.id,
        message,
        parse_mode=ParseMode.HTML
    )

def set_filter(update: Update, context: CallbackContext, filter: dict, name: str) -> None:
    """
    This handler sets the status of a list of some filter of the recipes
    """

    if len(context.args) == 0 or not context.args[0].upper() in [ENABLED, DISABLED]:
        context.bot.send_message(
            update.message.from_user.id,
            f"Please indicate whether you want to enable or disable.\n The status must be either 'ENABLED' or 'DISABLED'.\n The command must be like this: \n/set_{name.lower()} ENABLED/DISABLED selection1 selection2 ...\n/set_{name.lower()} ENABLED/DISABLED (to modify all {name.lower()})\nThe case is unsensitive and you don't need to put the complete name of each selection, just a part of it. If the name has more than one word, you can use an underscore instead of a space."
        )
        return
    status = context.args[0].upper()
    list_to_set = context.args[1:] if len(context.args) > 1 else filter.keys()
    list_to_set = [f for f in list_to_set if f is not None]

    context.bot.send_message(
        update.message.from_user.id,
        "Updating..."
    )

    failed_ones = []
    success_ones = []
    for f in list_to_set:
        f.replace("_", " ")
        if f in filter:
            filter[f] = status
            success_ones.append(f)
        else:
            success = False
            for k in filter.keys():
                # delete spaces and symbols from the names using regex to have only the letters
                k_simplified = re.sub(r'[^a-zA-Z]', '', k).lower()
                f_simplified = re.sub(r'[^a-zA-Z]', '', f).lower()
                if f_simplified in k_simplified:
                    filter[k] = status
                    success_ones.append(k)
                    success = True
            if not success:
                failed_ones.append(f)
                    
    if failed_ones:
        context.bot.send_message(
            update.message.from_user.id,
            f"Failed to set the following: {', '.join(failed_ones)}\nPlease make sure you typed each name correctly.\nThe case is unsensitive and you don't need to put the complete name of each selection, just a part of it. If the name has more than one word, you can use an underscore instead of a space."
        )
    if success_ones:
        context.bot.send_message(
            update.message.from_user.id,
            f"{name.title()} updated successfully"
        )

def send_dates(update: Update, context: CallbackContext, filter: dict) -> None:
    """
    This handler sends the oldest and newest updated dates of the recipes
    """
    message = "<b>Updated Dates Allowed</b>\n"
    message += f"Oldest: {filter[MIN].strftime('%Y-%m-%d')}\n"
    message += f"Newest: {filter[MAX].strftime('%Y-%m-%d')}\n"

    context.bot.send_message(
        update.message.from_user.id,
        message,
        parse_mode=ParseMode.HTML
    )

def set_dates(update: Update, context: CallbackContext, connection: psycopg2.extensions.connection, filters: dict) -> None:
    """
    This handler sets the oldest and newest updated dates of the recipes
    """
    if len(context.args) == 1 or len(context.args) > 2:
        context.bot.send_message(
            update.message.from_user.id,
            "Please provide only two dates: the oldest and the newest. You can also not provide any dates to reset them to the default values."
        )
        return

    if len(context.args) == 0:
        oldest_updated_date = execute_fetch_query(get_oldest_updated_date(), connection)[0]["min"]
        newest_updated_date = execute_fetch_query(get_newest_updated_date(), connection)[0]["max"]
        filters[DATES] = {MIN: oldest_updated_date, MAX: newest_updated_date}
        context.bot.send_message(
            update.message.from_user.id,
            "Dates reset to the default values"
        )
        return

    try:
        oldest_updated_date = datetime(*[int(i) for i in context.args[0].split("-")])
        newest_updated_date = datetime(*[int(i) for i in context.args[1].split("-")])
    except ValueError:
        context.bot.send_message(
            update.message.from_user.id,
            "Please provide the dates in the format 'YYYY-MM-DD'"
        )
        return

    filters[DATES][MIN] = oldest_updated_date
    filters[DATES][MAX] = newest_updated_date
    context.bot.send_message(
        update.message.from_user.id,
        "Dates updated successfully"
    )

def send_hearts(update: Update, context: CallbackContext, hearts: set) -> None:
    """
    This handler sends the number of hearts the user has
    """
    n_hearts = hearts.pop()
    hearts.add(n_hearts)
    context.bot.send_message(
        update.message.from_user.id,
        f"The minimum number of hearts is {n_hearts}"
    )

def set_hearts(update: Update, context: CallbackContext, filter: set) -> None:
    """
    This handler sets the minimum number of hearts the user wants
    """
    if len(context.args) != 1:
        context.bot.send_message(
            update.message.from_user.id,
            "Please provide one number"
        )
        return

    try:
        hearts = int(context.args[0])
    except ValueError:
        context.bot.send_message(
            update.message.from_user.id,
            "Please provide a valid number"
        )
        return

    filter.pop()
    filter.add(hearts)
    context.bot.send_message(
        update.message.from_user.id,
        "Hearts updated successfully"
    )

def send_time(update: Update, context: CallbackContext, time: dict) -> None:
    """
    This handler sends the minimum and maximum time the user has
    """
    max_t = time[MAX] if time[MAX] != -1 else "∞"
    message = "<b>Time Allowed (minutes)</b>\n"
    message += f"Minimum: {time[MIN]}\n"
    message += f"Maximum: {max_t}\n"

    context.bot.send_message(
        update.message.from_user.id,
        message,
        parse_mode=ParseMode.HTML
    )

def set_time(update: Update, context: CallbackContext, filter: dict) -> None:
    """
    This handler sets the minimum and maximum time the user wants
    """
    if len(context.args) != 2:
        context.bot.send_message(
            update.message.from_user.id,
            "Please provide only two numbers (in minutes)"
        )
        return

    try:
        min_time = int(context.args[0])
        max_time = int(context.args[1])
    except ValueError:
        context.bot.send_message(
            update.message.from_user.id,
            "Please provide valid numbers"
        )
        return

    filter[MIN] = min_time
    filter[MAX] = max_time
    context.bot.send_message(
        update.message.from_user.id,
        "Time updated successfully"
    )

def send_holidays(update: Update, context: CallbackContext, filter: dict) -> None:
    """
    This handler sends the holidays the user has
    """
    holidays = ""
    if filter[VALENTINES]:
        holidays += "💌 Valentine's Day\n"
    if filter[CHRISTMAS]:
        holidays += "🎄 Christmas\n"
    if filter[EASTER]:
        holidays += "🐰 Easter\n"
    if filter[SUMMER]:
        holidays += "🏖️ Summer\n"

    if len(holidays) == 0:
        context.bot.send_message(
            update.message.from_user.id,
            "All holidays disabled"
        )
        return

    context.bot.send_message(
        update.message.from_user.id,
        f"The holidays allowed are:\n{holidays}"
    )

def set_holidays(update: Update, context: CallbackContext, filter: dict) -> None:
    """
    This handler sets the holidays the user wants
    """
    allowed = [h.upper() for h in context.args]
    confirmed = []
    for h in [VALENTINES, CHRISTMAS, EASTER, SUMMER]:
        if h in allowed:
            filter[h] = True
            confirmed.append(h)
        else:
            filter[h] = False
    if len(confirmed) == 0:
        context.bot.send_message(
            update.message.from_user.id,
            "All holidays disabled"
        )
    else:
        context.bot.send_message(
            update.message.from_user.id,
            f"The following holidays are enabled: {', '.join(confirmed)}"
        )

def clean_filters(update: Update, context: CallbackContext, connection: psycopg2.extensions.connection, filters: dict) -> None:
    """
    This handler cleans the filters
    """
    for (filter_name, column) in [(CATEGORIES, "Category"), (CUISINES, "Cuisine")]:
        filters[filter_name] = load_filter(connection, column)
        if not filters[filter_name]:
            return

    oldest_updated_date = execute_fetch_query(get_oldest_updated_date(), connection)[0]["min"]
    newest_updated_date = execute_fetch_query(get_newest_updated_date(), connection)[0]["max"]
    oldest_updated_date = datetime(oldest_updated_date.year, oldest_updated_date.month, oldest_updated_date.day)
    newest_updated_date = datetime(newest_updated_date.year, newest_updated_date.month, newest_updated_date.day)
    filters[DATES][MIN] = oldest_updated_date
    filters[DATES][MAX] = newest_updated_date
    filters[TIME][MIN] = 0
    filters[TIME][MAX] = -1
    filters[HEARTS].clear()
    filters[HEARTS].add(0)
    filters[HOLIDAYS][VALENTINES] = True
    filters[HOLIDAYS][CHRISTMAS] = True
    filters[HOLIDAYS][EASTER] = True
    filters[HOLIDAYS][SUMMER] = True
    context.bot.send_message(
        update.message.from_user.id,
        "Filters cleaned successfully"
    )

def send_menu_charts(update: Update, context: CallbackContext):
    reply_keyboard = [["1","2"],["3","4"],["5"]]
    context.bot.send_message(
    update.message.from_user.id,
    "🍰 Hey there! Dive into our visual charts and unlock delicious secrets with a tap! ✨\n\n"
    "*📊 Option 1:* Press or send *'1'* to see which categories have the most hearts! They must be the crowd-pleasers!\n"
    "*📊 Option 2:* Press or send *'2'* ❤️ to discover how many special occasion recipes we have! We're talking party time!\n"
    "*📊 Option 3:* Press or send *'3'* to see how many recipes we've collected from Sweetest Menu over the years! We bet it's a treasure trove!\n"
    "*📊 Option 4:* Press or send '4' to see how many recipes we've collected from RecipeTin Eats over the years! Let's see what culinary gems they hold!\n"
    "*📊 Option 5:* Press or send '5' to discover the TOP 5 longest cooking times by category (only for the brave!). Are you ready to face the heat?\n\n"
    "_Get ready to embark on a delightful journey through our dessert wonderland! 🍨🍩 Let's uncover some sweet surprises together! 😋✨_",
    parse_mode=ParseMode.MARKDOWN ,
    reply_markup = ReplyKeyboardMarkup(
        reply_keyboard, one_time_keyboard = True, input_field_placeholder ="Here"
        )
    )
    return GET_CHART

def get_chart(update: Update, context: CallbackContext):
    context.user_data["respuesta"] = update.message.text
    connection = get_connection()

    if context.user_data["respuesta"] == '1':
        send_hearts_by_category(update, context, connection)
    elif context.user_data["respuesta"] == '2':
        send_count_by_holiday(update, context, connection)
    elif context.user_data["respuesta"] == '3':
        send_recipes_by_posteddate(update, context, connection, "sweetestmenu")
    elif context.user_data["respuesta"] == '4':
        send_recipes_by_posteddate(update, context, connection, "recipetineats")
    elif context.user_data["respuesta"] == '5':
        send_max_time_by_category(update,context,connection)
    else:
        update.message.reply_text("Oops! I didn't quite catch that. Please select an option from the menu.")

    update.message.reply_text(
        "*Hey there, foodie friend!* \n\n"
        "Just a quick heads-up that you can use the */random_recipe* command to get a random ☘️ recipe from our massive database!  It's like having a culinary genie in your pocket! ✨\n\n"
        "And if you're craving more chart goodness, just send */send_menu_charts* again and I'll serve you up those options in no time! \n Happy culinary adventures! 🤖",
        parse_mode=ParseMode.MARKDOWN
        )
    return ConversationHandler.END

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome! I'm Postrecito, your friendly guide to the world of all things sweet and delectable. \n\n"
                                "I'm here to help you discover the perfect recipe to satisfy your every craving, from quick and easy treats to elaborate showstoppers. ✨ \n\n"
                                "🚀 Here are a few quick commands to get you started 🚀\n\n"
                                "/random_recipe - Let fate decide your next culinary adventure with a random recipe suggestion! \n"
                                "/top_recipe - Explore the best recipes based on your preferences. \n\n"
                                "/set_categories - Narrow down your options by selecting your preferred dessert category.\n"
                                "/set_cuisines - Explore the flavors of the world by choosing your desired cuisine.\n"
                                "/set_dates - Indulge in seasonal delights by filtering recipes based on specific dates\n"
                                "/set_hearts - Satisfy your cravings for crowd-pleasers by setting a minimum hearts threshold.\n"
                                "/set_time - Choose the perfect recipe for your schedule by setting a maximum cooking time.\n"
                                "/set_holidays - Celebrate special occasions with recipes tailored to your favorite holidays.\n"
                                "/clean_filters - Reset the filters. \n"
                                "/random_holiday_recipe - Let Postrecito surprise you with a delectable recipe from your chosen holiday.\n"
                                "/top_holiday_recipe - Discover the top holiday recipe based on your preferences.\n"
                                "/send_menu_charts - Delve into a world of charts and graphs showcasing our vast recipe collection.\n\n"
                                "Remember, I'm always here to help you find the perfect recipe for your sweet tooth. _Happy baking and indulging!_✨"
                            )

