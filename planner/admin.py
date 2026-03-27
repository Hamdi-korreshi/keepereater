from django.contrib import admin

from .models import Ingredient, MealEntry, Recipe, RecipeStep


class IngredientInline(admin.TabularInline):
    model = Ingredient
    extra = 0


class RecipeStepInline(admin.TabularInline):
    model = RecipeStep
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "category", "calories", "is_starter")
    list_filter = ("category", "is_starter")
    search_fields = ("title", "description")
    inlines = [IngredientInline, RecipeStepInline]


@admin.register(MealEntry)
class MealEntryAdmin(admin.ModelAdmin):
    list_display = ("date", "slot", "recipe", "user", "quantity")
    list_filter = ("slot", "date")
    search_fields = ("recipe__title", "user__username")
