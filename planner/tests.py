from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


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
