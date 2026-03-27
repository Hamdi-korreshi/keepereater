from django.urls import path

from .views import (
    KeepereatersLoginView,
    account_settings,
    calendar_view,
    cookbook,
    grocery_list,
    home,
    meal_entry_create,
    meal_entry_delete,
    meal_entry_edit,
    recipe_create,
    recipe_delete,
    recipe_detail,
    recipe_edit,
    signup,
)

urlpatterns = [
    path("", home, name="home"),
    path("signup/", signup, name="signup"),
    path("login/", KeepereatersLoginView.as_view(), name="login"),
    path("cookbook/", cookbook, name="cookbook"),
    path("recipes/add/", recipe_create, name="recipe-create"),
    path("recipes/<int:pk>/", recipe_detail, name="recipe-detail"),
    path("recipes/<int:pk>/edit/", recipe_edit, name="recipe-edit"),
    path("recipes/<int:pk>/delete/", recipe_delete, name="recipe-delete"),
    path("calendar/", calendar_view, name="calendar"),
    path("calendar/add/", meal_entry_create, name="meal-entry-create"),
    path("calendar/<int:pk>/edit/", meal_entry_edit, name="meal-entry-edit"),
    path("calendar/<int:pk>/delete/", meal_entry_delete, name="meal-entry-delete"),
    path("grocery-list/", grocery_list, name="grocery-list"),
    path("account/", account_settings, name="account-settings"),
]
