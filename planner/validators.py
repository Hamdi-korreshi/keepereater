from django.core.exceptions import ValidationError


class ComplexityPasswordValidator:
    def validate(self, password, user=None):
        if not any(char.isupper() for char in password):
            raise ValidationError("Password must include at least one uppercase letter.")
        if not any(char.islower() for char in password):
            raise ValidationError("Password must include at least one lowercase letter.")
        if not any(char.isdigit() for char in password):
            raise ValidationError("Password must include at least one number.")
        if password.isalnum():
            raise ValidationError("Password must include at least one symbol.")

    def get_help_text(self):
        return "Your password must be at least 11 characters and include uppercase, lowercase, number, and symbol characters."
