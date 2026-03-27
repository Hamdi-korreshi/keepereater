import calendar
import re
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal, InvalidOperation

UNIT_ALIASES = {
    "cup": "cup",
    "cups": "cup",
    "tbsp": "tbsp",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "tsp": "tsp",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "lb": "lb",
    "lbs": "lb",
    "pound": "lb",
    "pounds": "lb",
    "half": "",
    "halves": "",
    "oz": "oz",
    "ounce": "oz",
    "ounces": "oz",
    "clove": "clove",
    "cloves": "clove",
    "pinch": "pinch",
    "pinches": "pinch",
}


def parse_amount(token):
    token = token.strip()
    if not token:
        return None
    if "/" in token and " " not in token:
        num, denom = token.split("/", 1)
        try:
            return Decimal(num) / Decimal(denom)
        except (InvalidOperation, ZeroDivisionError):
            return None
    try:
        return Decimal(token)
    except InvalidOperation:
        return None


def parse_leading_amount(parts):
    if not parts:
        return None, 0

    first = parse_amount(parts[0])
    if first is None:
        return None, 0

    if len(parts) > 1:
        second = parse_amount(parts[1])
        if second is not None and "/" in parts[1]:
            return first + second, 2
    return first, 1


def normalize_ingredient(text):
    text = " ".join(text.strip().split())
    quantity = None
    unit = ""
    normalized_name = text.lower()
    parts = text.split()
    if parts:
        quantity, consumed = parse_leading_amount(parts)
        if quantity is not None:
            parts = parts[consumed:]
        if parts and parts[0].lower() in UNIT_ALIASES:
            unit = UNIT_ALIASES[parts[0].lower()]
            parts = parts[1:]
        normalized_name = " ".join(parts).strip(", ").lower() or text.lower()
    return {
        "text": text,
        "quantity": quantity,
        "unit": unit,
        "normalized_name": re.sub(r"\s+", " ", normalized_name),
    }


def month_bounds(selected_date):
    first_day = selected_date.replace(day=1)
    _, last_day_number = calendar.monthrange(first_day.year, first_day.month)
    last_day = first_day.replace(day=last_day_number)
    start_display = first_day - timedelta(days=first_day.weekday())
    end_display = last_day + timedelta(days=(6 - last_day.weekday()))
    return first_day, last_day, start_display, end_display


def week_bounds(selected_date):
    start = selected_date - timedelta(days=selected_date.weekday())
    end = start + timedelta(days=6)
    return start, end


def build_shopping_list(entries):
    combined = defaultdict(lambda: {"quantity": Decimal("0"), "unit": "", "name": ""})
    manual_items = []
    for entry in entries.select_related("recipe").prefetch_related("recipe__ingredients"):
        for ingredient in entry.recipe.ingredients.all():
            normalized = normalize_ingredient(ingredient.text)
            scaled_quantity = normalized["quantity"] * entry.quantity if normalized["quantity"] is not None else None
            if scaled_quantity is not None and normalized["normalized_name"]:
                key = (normalized["normalized_name"], normalized["unit"])
                combined[key]["quantity"] += scaled_quantity
                combined[key]["unit"] = normalized["unit"]
                combined[key]["name"] = normalized["normalized_name"]
            else:
                manual_items.append(f"{ingredient.text} ({entry.recipe.title} x{entry.quantity})")
    combined_items = [
        {
            "display": " ".join(
                part for part in [format_decimal(item["quantity"]), item["unit"], item["name"]] if part
            ),
            "name": item["name"],
        }
        for item in combined.values()
    ]
    combined_items.sort(key=lambda item: item["name"])
    manual_items.sort()
    return combined_items, manual_items


def format_decimal(value):
    if value == value.to_integral():
        return str(int(value))
    return format(value.normalize(), "f")


def calorie_totals(entries):
    total = Decimal("0")
    for entry in entries.select_related("recipe"):
        total += Decimal(entry.recipe.calories) * entry.quantity
    return int(total)
