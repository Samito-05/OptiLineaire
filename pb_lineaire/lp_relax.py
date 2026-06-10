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


def solve_lp_auto(c, A, b):
    """
    Résout  max c^T x   s.c.  A x ≤ b,  x ≥ 0  en choisissant la méthode.
    Retourne le résultat du solveur, enrichi de la clé "method".
    """
    if all(Fraction(bi) >= 0 for bi in b):
        result = run_simplex(c, A, b)
        result["method"] = "simplex"
    else:
        result = run_two_phase(c, A, b)
        result["method"] = "two_phase"
    return result


def extract_x(final, n):
    """Extrait le vecteur x (Fractions) du tableau optimal."""
    x = [Fraction(0)] * n
    for i, var_idx in enumerate(final["basis"]):
        if var_idx < n:
            x[var_idx] = final["tableau"][i + 1][-1]
    return x
