from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import MealEntry, Recipe
from .utils import normalize_ingredient


class SignUpForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_form_classes(self.fields)


class AccountForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_form_classes(self.fields)


class RecipeForm(forms.ModelForm):
    ingredients_text = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 8}),
        help_text="Enter one ingredient per line, for example: 2 cups rice",
    )
    steps_text = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 8}),
        help_text="Enter one step per line in the order you want them shown.",
    )

    class Meta:
        model = Recipe
        fields = (
            "title",
            "description",
            "category",
            "image",
            "calories",
            "carbs_grams",
            "fat_grams",
            "protein_grams",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_form_classes(self.fields)
        if self.instance.pk:
            self.fields["ingredients_text"].initial = "\n".join(
                ingredient.text for ingredient in self.instance.ingredients.all()
            )
            self.fields["steps_text"].initial = "\n".join(
                step.instruction for step in self.instance.steps.all()
            )

    def save(self, commit=True):
        recipe = super().save(commit=commit)
        if commit:
            recipe.ingredients.all().delete()
            recipe.steps.all().delete()
            ingredients = [
                normalize_ingredient(line)
                for line in self.cleaned_data["ingredients_text"].splitlines()
                if line.strip()
            ]
            for index, ingredient in enumerate(ingredients, start=1):
                recipe.ingredients.create(
                    text=ingredient["text"],
                    normalized_name=ingredient["normalized_name"],
                    quantity=ingredient["quantity"],
                    unit=ingredient["unit"],
                    sort_order=index,
                )
            for index, step in enumerate(
                [line.strip() for line in self.cleaned_data["steps_text"].splitlines() if line.strip()],
                start=1,
            ):
                recipe.steps.create(instruction=step, sort_order=index)
        return recipe


class MealEntryForm(forms.ModelForm):
    class Meta:
        model = MealEntry
        fields = ("recipe", "date", "slot", "custom_slot_name", "quantity")
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        apply_form_classes(self.fields)
        self.fields["recipe"].queryset = user.recipes.all()
        self.fields["quantity"].widget.attrs["step"] = "0.5"

    def clean(self):
        cleaned_data = super().clean()
        slot = cleaned_data.get("slot")
        custom_slot_name = (cleaned_data.get("custom_slot_name") or "").strip()
        if slot == MealEntry.Slot.OTHER and not custom_slot_name:
            self.add_error("custom_slot_name", "Add a label for the custom slot.")
        if slot and cleaned_data.get("date") and cleaned_data.get("recipe"):
            compare_slot_name = custom_slot_name if slot == MealEntry.Slot.OTHER else ""
            existing = MealEntry.objects.filter(
                user=self.user,
                date=cleaned_data["date"],
                slot=slot,
                recipe=cleaned_data["recipe"],
                custom_slot_name=compare_slot_name,
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError(
                    "That recipe is already scheduled in the same slot for that day. Update the quantity instead."
                )
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user
        instance.custom_slot_name = (instance.custom_slot_name or "").strip() if instance.slot == MealEntry.Slot.OTHER else ""
        if commit:
            instance.save()
        return instance


class GroceryRangeForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("The end date must be on or after the start date.")
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_form_classes(self.fields)


def apply_form_classes(fields):
    for field in fields.values():
        widget = field.widget
        if isinstance(widget, forms.Textarea):
            css_class = "textarea textarea-bordered min-h-32"
        elif isinstance(widget, forms.Select):
            css_class = "select select-bordered"
        elif isinstance(widget, forms.ClearableFileInput):
            css_class = "file-input file-input-bordered"
        else:
            css_class = "input input-bordered"
        existing = widget.attrs.get("class", "")
        widget.attrs["class"] = f"{existing} {css_class}".strip()
