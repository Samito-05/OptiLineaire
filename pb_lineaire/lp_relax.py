"""
Résolution automatique d'une relaxation linéaire continue.

Sélectionne la méthode comme dans le cours :
  • tous les b_i ≥ 0  →  Simplexe direct (origine admissible)
  • un b_i < 0        →  méthode des deux phases (artificielle unique δ)

Utilisé par les méthodes entières (coupes de Gomory, Branch-and-Bound)
qui doivent résoudre une relaxation LP à chaque étape / nœud.
"""

from fractions import Fraction
from .simplex import run_simplex
from .simplex_two_phase import run_two_phase


def solve_lp_auto(c, A, b, budget=None):
    """
    Résout  max c^T x   s.c.  A x ≤ b,  x ≥ 0  en choisissant la méthode.
    Retourne le résultat du solveur, enrichi de la clé "method" et, si un
    `budget` de détails est fourni, du nombre d'itérations dont l'affichage
    a été réduit ("omitted_steps") ou supprimé ("omitted_tableaux").
    """
    steps_before = budget.omitted_steps if budget else 0
    tableaux_before = budget.omitted_tableaux if budget else 0

    if all(Fraction(bi) >= 0 for bi in b):
        result = run_simplex(c, A, b, budget=budget)
        result["method"] = "simplex"
    else:
        result = run_two_phase(c, A, b, budget=budget)
        result["method"] = "two_phase"

    if budget:
        result["omitted_steps"] = budget.omitted_steps - steps_before
        result["omitted_tableaux"] = budget.omitted_tableaux - tableaux_before
    return result


def extract_x(final, n):
    """Extrait le vecteur x (Fractions) du tableau optimal."""
    x = [Fraction(0)] * n
    for i, var_idx in enumerate(final["basis"]):
        if var_idx < n:
            x[var_idx] = final["tableau"][i + 1][-1]
    return x
