from collections import defaultdict
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AccountForm, GroceryRangeForm, MealEntryForm, RecipeForm, SignUpForm
from .models import MealEntry, Recipe
from .utils import build_shopping_list, calorie_totals, month_bounds, week_bounds


def home(request):
    return render(request, "planner/home.html", {"smiling_people_image": None})


def signup(request):
    if request.user.is_authenticated:
        return redirect("calendar")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your account is ready, including the 4 starter recipes in your cookbook.")
        return redirect("calendar")
    return render(request, "registration/signup.html", {"form": form})


class KeepereatersLoginView(LoginView):
    template_name = "registration/login.html"


@login_required
def cookbook(request):
    query = request.GET.get("q", "").strip()
    recipes = request.user.recipes.all()
    if query:
        recipes = recipes.filter(Q(title__icontains=query) | Q(description__icontains=query))
    return render(
        request,
        "planner/cookbook.html",
        {"recipes": recipes.prefetch_related("ingredients"), "query": query},
    )


@login_required
def recipe_detail(request, pk):
    recipe = get_object_or_404(
        Recipe.objects.prefetch_related("ingredients", "steps"),
        pk=pk,
        owner=request.user,
    )
    return render(request, "planner/recipe_detail.html", {"recipe": recipe})


@login_required
def recipe_create(request):
    form = RecipeForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        recipe = form.save(commit=False)
        recipe.owner = request.user
        recipe.save()
        form.instance = recipe
        form.save()
        messages.success(request, "Recipe added to your cookbook.")
        return redirect(recipe.get_absolute_url())
    return render(request, "planner/recipe_form.html", {"form": form, "title": "Add Recipe"})


@login_required
def recipe_edit(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, owner=request.user)
    form = RecipeForm(request.POST or None, request.FILES or None, instance=recipe)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Recipe updated.")
        return redirect(recipe.get_absolute_url())
    return render(request, "planner/recipe_form.html", {"form": form, "title": "Edit Recipe", "recipe": recipe})


@login_required
def recipe_delete(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, owner=request.user)
    if request.method == "POST":
        recipe.delete()
        messages.success(request, "Recipe removed from your cookbook.")
        return redirect("cookbook")
    return render(request, "planner/confirm_delete.html", {"object": recipe, "kind": "recipe"})


@login_required
def calendar_view(request):
    view_mode = request.GET.get("view", "month")
    date_param = request.GET.get("date")
    month_param = request.GET.get("month")
    today = date.today()
    if date_param:
        focus_date = datetime.strptime(date_param, "%Y-%m-%d").date()
    elif month_param:
        focus_date = datetime.strptime(month_param, "%Y-%m").date().replace(day=1)
    else:
        focus_date = today

    if view_mode == "week":
        period_start, period_end = week_bounds(focus_date)
        display_start, display_end = period_start, period_end
        title = f"{period_start.strftime('%b %d')} - {period_end.strftime('%b %d, %Y')}"
        prev_value = (period_start - timedelta(days=7)).isoformat()
        next_value = (period_start + timedelta(days=7)).isoformat()
        selected_date = focus_date
    else:
        selected_date = focus_date.replace(day=1)
        period_start, period_end, display_start, display_end = month_bounds(selected_date)
        title = selected_date.strftime("%B %Y")
        prev_value = (period_start - timedelta(days=1)).strftime("%Y-%m")
        next_value = (period_end + timedelta(days=1)).strftime("%Y-%m")

    entries = (
        request.user.meal_entries.filter(date__range=(display_start, display_end))
        .select_related("recipe")
        .order_by("date", "slot", "recipe__title")
    )
    entries_by_day = defaultdict(list)
    for entry in entries:
        entries_by_day[entry.date].append(entry)

    days = []
    current = display_start
    while current <= display_end:
        days.append(
            {
                "date": current,
                "in_month": view_mode == "week" or current.month == selected_date.month,
                "entries": entries_by_day[current],
            }
        )
        current += timedelta(days=1)

    month_entries = request.user.meal_entries.filter(
        date__range=month_bounds(date.today().replace(day=1))[:2]
    ).select_related("recipe")
    week_start, week_end = week_bounds(date.today())
    week_entries = request.user.meal_entries.filter(date__range=(week_start, week_end)).select_related("recipe")
    calendar_rows = [days[index:index + 7] for index in range(0, len(days), 7)]
    context = {
        "selected_date": selected_date,
        "today": today,
        "calendar_rows": calendar_rows,
        "view_mode": view_mode,
        "calendar_title": title,
        "month_calories": calorie_totals(month_entries),
        "week_calories": calorie_totals(week_entries),
        "prev_value": prev_value,
        "next_value": next_value,
    }
    return render(request, "planner/calendar.html", context)


@login_required
def meal_entry_create(request):
    initial = {"date": request.GET.get("date") or date.today().isoformat(), "slot": request.GET.get("slot") or MealEntry.Slot.DINNER}
    recipe_id = request.GET.get("recipe")
    if recipe_id:
        initial["recipe"] = recipe_id
    form = MealEntryForm(request.user, request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            form.save()
        except IntegrityError:
            form.add_error(None, "That recipe is already scheduled in the same slot for that day. Update the quantity instead.")
        else:
            messages.success(request, "Meal added to the calendar.")
            return redirect("calendar")
    return render(request, "planner/meal_entry_form.html", {"form": form, "title": "Schedule Meal"})


@login_required
def meal_entry_edit(request, pk):
    entry = get_object_or_404(MealEntry, pk=pk, user=request.user)
    form = MealEntryForm(request.user, request.POST or None, instance=entry)
    if request.method == "POST" and form.is_valid():
        try:
            form.save()
        except IntegrityError:
            form.add_error(None, "That recipe is already scheduled in the same slot for that day. Update the quantity instead.")
        else:
            messages.success(request, "Meal updated.")
            return redirect("calendar")
    return render(request, "planner/meal_entry_form.html", {"form": form, "title": "Edit Scheduled Meal", "entry": entry})


@login_required
def meal_entry_delete(request, pk):
    entry = get_object_or_404(MealEntry.objects.select_related("recipe"), pk=pk, user=request.user)
    if request.method == "POST":
        entry.delete()
        messages.success(request, "Meal removed from the calendar.")
        return redirect("calendar")
    return render(request, "planner/confirm_delete.html", {"object": entry, "kind": "meal"})


@login_required
def grocery_list(request):
    today = date.today()
    week_start, week_end = week_bounds(today)
    form = GroceryRangeForm(request.GET or None, initial={"start_date": week_start, "end_date": week_end})
    combined_items = []
    manual_items = []
    selected_entries = request.user.meal_entries.none()
    if form.is_valid():
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]
        selected_entries = request.user.meal_entries.filter(date__range=(start_date, end_date))
        combined_items, manual_items = build_shopping_list(selected_entries)
    return render(
        request,
        "planner/grocery_list.html",
        {
            "form": form,
            "combined_items": combined_items,
            "manual_items": manual_items,
            "selected_entries": selected_entries.select_related("recipe").order_by("date", "slot"),
        },
    )


@login_required
def account_settings(request):
    account_form = AccountForm(request.POST or None, instance=request.user, prefix="account")
    password_form = PasswordChangeForm(request.user, request.POST or None, prefix="password")

    if request.method == "POST":
        if "save_account" in request.POST and account_form.is_valid():
            account_form.save()
            messages.success(request, "Email updated.")
            return redirect("account-settings")
        if "save_password" in request.POST and password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password updated.")
            return redirect("account-settings")

    return render(
        request,
        "planner/account_settings.html",
        {"account_form": account_form, "password_form": password_form},
    )
