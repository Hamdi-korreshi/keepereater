from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Ingredient, Recipe, RecipeStep
from .starter_data import STARTER_RECIPES
from .utils import normalize_ingredient

User = get_user_model()


@receiver(post_save, sender=User)
def seed_starter_recipes(sender, instance, created, **kwargs):
    if not created:
        return

    for recipe_data in STARTER_RECIPES:
        recipe = Recipe.objects.create(
            owner=instance,
            title=recipe_data["title"],
            description=recipe_data["description"],
            category=recipe_data["category"],
            source_url=recipe_data["source_url"],
            calories=recipe_data["calories"],
            carbs_grams=Decimal(recipe_data["carbs_grams"]),
            fat_grams=Decimal(recipe_data["fat_grams"]),
            protein_grams=Decimal(recipe_data["protein_grams"]),
            is_starter=True,
        )
        for index, ingredient_text in enumerate(recipe_data["ingredients"], start=1):
            normalized = normalize_ingredient(ingredient_text)
            Ingredient.objects.create(
                recipe=recipe,
                text=normalized["text"],
                normalized_name=normalized["normalized_name"],
                quantity=normalized["quantity"],
                unit=normalized["unit"],
                sort_order=index,
            )
        for index, step in enumerate(recipe_data["steps"], start=1):
            RecipeStep.objects.create(recipe=recipe, instruction=step, sort_order=index)
