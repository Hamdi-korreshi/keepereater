# Keepereaters

Meal planning app built with Django, TailwindCSS, and DaisyUI.

## Run locally

1. `python3 -m venv .venv`
2. `.venv/bin/pip install django pillow 'psycopg[binary]'`
3. `npm install`
4. `npm run build:css`
5. `.venv/bin/python manage.py migrate`
6. `.venv/bin/python manage.py createsuperuser`
7. `.venv/bin/python manage.py runserver`

## Database

- If `POSTGRES_DB` is set, the app uses PostgreSQL.
- Otherwise it falls back to SQLite for local development.

## Starter recipes

New accounts automatically receive 4 starter recipes based on:

- [Easy Chicken Stir Fry](https://www.momontimeout.com/easy-chicken-stir-fry-recipe/)
- [Chicken Parmesan](https://www.allrecipes.com/recipe/223042/chicken-parmesan/)
- [Protein Pancakes](https://www.laurafuentes.com/protein-pancakes/)
- [Ground Beef Tacos](https://feelgoodfoodie.net/recipe/ground-beef-tacos-napa-cabbage-guacamole/)
