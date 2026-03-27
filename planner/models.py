from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

User = get_user_model()


class Recipe(models.Model):
    class Category(models.TextChoices):
        SNACK = "snack", "Snack"
        ENTREE = "entree", "Entree"
        DESSERT = "dessert", "Dessert"

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recipes")
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.ENTREE)
    image = models.ImageField(upload_to="recipes/", blank=True, null=True)
    external_image_url = models.URLField(blank=True)
    source_url = models.URLField(blank=True)
    calories = models.PositiveIntegerField(default=0)
    carbs_grams = models.DecimalField(max_digits=6, decimal_places=1, default=Decimal("0.0"))
    fat_grams = models.DecimalField(max_digits=6, decimal_places=1, default=Decimal("0.0"))
    protein_grams = models.DecimalField(max_digits=6, decimal_places=1, default=Decimal("0.0"))
    is_starter = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("recipe-detail", args=[self.pk])

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return self.external_image_url

    @property
    def category_theme(self):
        return {
            self.Category.SNACK: "snack",
            self.Category.ENTREE: "entree",
            self.Category.DESSERT: "dessert",
        }.get(self.category, "entree")


class Ingredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="ingredients")
    text = models.CharField(max_length=255)
    normalized_name = models.CharField(max_length=150, blank=True)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    unit = models.CharField(max_length=40, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.text


class RecipeStep(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="steps")
    instruction = models.TextField()
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.recipe.title} step {self.sort_order}"


class MealEntry(models.Model):
    class Slot(models.TextChoices):
        BREAKFAST = "breakfast", "Breakfast"
        LUNCH = "lunch", "Lunch"
        DINNER = "dinner", "Dinner"
        SNACK = "snack", "Snack"
        OTHER = "other", "Other"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="meal_entries")
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="meal_entries")
    date = models.DateField()
    slot = models.CharField(max_length=20, choices=Slot.choices)
    custom_slot_name = models.CharField(max_length=40, blank=True)
    quantity = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=Decimal("1.0"),
        validators=[MinValueValidator(Decimal("0.5"))],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "slot", "recipe__title"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "date", "slot", "recipe", "custom_slot_name"],
                name="unique_recipe_per_slot_day",
            )
        ]

    def __str__(self):
        return f"{self.user} {self.recipe} {self.date} {self.slot}"

    @property
    def slot_label(self):
        if self.slot == self.Slot.OTHER and self.custom_slot_name:
            return self.custom_slot_name
        return self.get_slot_display()

    @property
    def total_calories(self):
        return int(self.recipe.calories * float(self.quantity))
