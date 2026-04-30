import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# Préfixes reconnus comme variables mathématiques
_VAR_PATTERN = re.compile(r"^([xysaA])(\d+)$")
_TEXT_VAR = re.compile(r"\b([xysaA])(\d+)\b")


def _subscript(letter, index):
    # Retourne une notation LaTeX pour MathJax, ex: $x_{1}$
    return f"${letter}_{{{index}}}$"


@register.filter
def math_var(value):
    """
    Convertit un nom de variable en notation LaTeX pour MathJax.
    "x1" → $x_{1}$
    "y2" → $y_{2}$
    "a3" → $a_{3}$
    "LF" → "LF"  (inchangé)
    """
    text = str(value)
    m = _VAR_PATTERN.fullmatch(text)
    if m:
        return mark_safe(_subscript(m.group(1), m.group(2)))
    # Pour d'autres labels (ex: LF) on renvoie tel quel
    return text


@register.filter
def math_text(value):
    """
    Dans un texte, remplace toutes les variables (x1, y2, a3 …)
    par leur rendu LaTeX prêt pour MathJax.
    "L(y1) ← L(y1) ÷ 6" → "L($y_{1}$) ← …"
    """
    text = str(value)
    # Remplace les occurrences de variables par leur forme LaTeX
    result = _TEXT_VAR.sub(lambda m: _subscript(m.group(1), m.group(2)), text)
    return mark_safe(result)


@register.filter
def math_index(value, letter="x"):
    """
    Convertit un entier en variable indicée HTML.
    3|math_index:"x"  →  <i>x</i><sub>3</sub>
    """
    return mark_safe(_subscript(letter, value))
