import re

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def math_var(value):
    """Affiche x1/y2 en style mathématique LaTeX: \\(x_1\\), \\(y_2\\)."""
    text = str(value)
    match = re.fullmatch(r"([xy])(\d+)", text)
    if not match:
        return text

    name, index = match.groups()
    return mark_safe(f"\\({name}_{{{index}}}\\)")


@register.filter
def math_text(value):
    """Convertit dans un texte toutes les occurrences x1/y2 en \\(x_1\\)/\\(y_2\\)."""
    text = str(value)
    converted = re.sub(r"\b([xy])(\d+)\b", r"\\(\1_{{\2}}\\)", text)
    return mark_safe(converted)


@register.filter
def math_index(value, letter="x"):
    """Convertit un index en notation LaTeX : 1 -> \\(x_1\\), 2 -> \\(y_2\\), etc."""
    return mark_safe(f"\\({letter}_{{{value}}}\\)")


