import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# Variables indicées reconnues (δ = artificielle unique en deux phases)
_VAR_PATTERN = re.compile(r"^(δ|[xysaA])(\d+)$")
_TEXT_VAR = re.compile(r"\b(δ|[xysaA])(\d+)\b")
# δ seule (sans indice) : variable artificielle unique
_BARE_DELTA = re.compile(r"δ(?!\d)")

# Lettres nécessitant une commande LaTeX dédiée
_LATEX_LETTER = {"δ": r"\delta"}


def _sym(letter):
    return _LATEX_LETTER.get(letter, letter)


def _subscript(letter, index):
    # Retourne une notation LaTeX pour MathJax, ex: $x_{1}$ ou $\delta_{1}$
    return f"${_sym(letter)}_{{{index}}}$"


@register.filter
def math_var(value):
    """
    Convertit un nom de variable en notation LaTeX pour MathJax.
    "x1" → $x_{1}$   "y2" → $y_{2}$   "δ" → $\\delta$   "LF" → "LF"
    """
    text = str(value)
    m = _VAR_PATTERN.fullmatch(text)
    if m:
        return mark_safe(_subscript(m.group(1), m.group(2)))
    if text == "δ":
        return mark_safe(f"${_sym('δ')}$")
    # Pour d'autres labels (ex: LF) on renvoie tel quel
    return text


@register.filter
def math_text(value):
    """
    Dans un texte, remplace toutes les variables (x1, y2, δ, δ…)
    par leur rendu LaTeX prêt pour MathJax.
    "L(δ) ← L(δ) ÷ 6" → "L($\\delta$) ← …"
    """
    text = str(value)
    # Variables indicées (x1, y2, δ1 …)
    text = _TEXT_VAR.sub(lambda m: _subscript(m.group(1), m.group(2)), text)
    # δ seule (non suivie d'un indice)
    text = _BARE_DELTA.sub(lambda _: f"${_sym('δ')}$", text)
    return mark_safe(text)


@register.filter
def math_index(value, letter="x"):
    """
    Convertit un entier en variable indicée HTML.
    3|math_index:"x"  →  <i>x</i><sub>3</sub>
    """
    return mark_safe(_subscript(letter, value))
