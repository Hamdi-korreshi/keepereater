from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Ingredient, MealEntry, Recipe
from .utils import normalize_ingredient


class AccountBootstrapTests(TestCase):
    def test_new_users_receive_four_starter_recipes(self):
        user = User.objects.create_user(
            username="starterfan",
            email="starter@example.com",
            password="StarterPass!123",
        )
        self.assertEqual(user.recipes.count(), 4)


class AccessTests(TestCase):
    def test_private_pages_require_login(self):
        response = self.client.get(reverse("calendar"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_logged_in_user_can_reach_core_pages(self):
        user = User.objects.create_user(
            username="planneruser",
            email="planner@example.com",
            password="PlannerPass!123",
        )
        self.client.login(username="planneruser", password="PlannerPass!123")
        self.assertEqual(self.client.get(reverse("calendar")).status_code, 200)
        self.assertEqual(self.client.get(reverse("cookbook")).status_code, 200)
        self.assertEqual(self.client.get(reverse("grocery-list")).status_code, 200)
        self.assertEqual(user.recipes.count(), 4)

    def test_calendar_week_view_renders(self):
        User.objects.create_user(
            username="weekuser",
            email="week@example.com",
            password="WeekPass!123",
        )
        self.client.login(username="weekuser", password="WeekPass!123")
        response = self.client.get(reverse("calendar"), {"view": "week", "date": "2026-03-27"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Week")


class IngredientParsingTests(TestCase):
    def test_normalize_handles_mixed_fraction_measurements(self):
        normalized = normalize_ingredient("1 1/2 cups all-purpose flour")
        self.assertEqual(str(normalized["quantity"]), "1.5")
        self.assertEqual(normalized["unit"], "cup")
        self.assertEqual(normalized["normalized_name"], "all-purpose flour")

    def test_grocery_list_merges_same_ingredient_across_meals(self):
        user = User.objects.create_user(
            username="mergeuser",
            email="merge@example.com",
            password="MergePass!123",
        )
        recipe = Recipe.objects.create(
            owner=user,
            title="Test Pancakes",
            description="test",
            category="snack",
            calories=100,
            carbs_grams="1",
            fat_grams="1",
            protein_grams="1",
        )
        flour = normalize_ingredient("1 1/2 cups all-purpose flour")
        Ingredient.objects.create(
            recipe=recipe,
            text=flour["text"],
            normalized_name=flour["normalized_name"],
            quantity=flour["quantity"],
            unit=flour["unit"],
        )
        MealEntry.objects.create(user=user, recipe=recipe, date="2026-03-27", slot="breakfast", quantity="1.0")
        MealEntry.objects.create(user=user, recipe=recipe, date="2026-03-28", slot="snack", quantity="1.0")

        self.client.login(username="mergeuser", password="MergePass!123")
        response = self.client.get(
            reverse("grocery-list"),
            {"start_date": "2026-03-27", "end_date": "2026-03-28"},
        )

        self.assertContains(response, "3 cup all-purpose flour")
