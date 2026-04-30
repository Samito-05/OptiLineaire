import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# Préfixes reconnus comme variables mathématiques
_VAR_PATTERN = re.compile(r"^([xysaA])(\d+)$")
_TEXT_VAR = re.compile(r"\b([xysaA])(\d+)\b")


def _subscript(letter, index):
    return f"<i>{letter}</i><sub>{index}</sub>"


@register.filter
def math_var(value):
    """
    Convertit un nom de variable en HTML avec indice.
    "x1" → <i>x</i><sub>1</sub>
    "s2" → <i>s</i><sub>2</sub>
    "a3" → <i>a</i><sub>3</sub>
    "LF" → "LF"  (inchangé)
    """
    text = str(value)
    m = _VAR_PATTERN.fullmatch(text)
    if m:
        return mark_safe(_subscript(m.group(1), m.group(2)))
    return text


@register.filter
def math_text(value):
    """
    Dans un texte, remplace toutes les variables (x1, s2, a3 …)
    par leur rendu HTML avec indice.
    "L(s1) ← L(s1) ÷ 6" → "L(<i>s</i><sub>1</sub>) ← …"
    """
    text = str(value)
    result = _TEXT_VAR.sub(lambda m: _subscript(m.group(1), m.group(2)), text)
    return mark_safe(result)


@register.filter
def math_index(value, letter="x"):
    """
    Convertit un entier en variable indicée HTML.
    3|math_index:"x"  →  <i>x</i><sub>3</sub>
    """
    return mark_safe(_subscript(letter, value))
