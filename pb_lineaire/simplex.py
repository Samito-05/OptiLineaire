from fractions import Fraction


def fmt(f):
    f = Fraction(f)
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


MAX_ITER = 500


class DetailBudget:
    """
    Limite le volume de détails enregistrés pour l'affichage, compté en
    cellules de tableau. Tant que le budget le permet : tableaux + étapes de
    pivot ("full") ; ensuite tableaux seuls ("tableau") ; enfin plus rien
    ("none"). Le calcul lui-même n'est jamais affecté.
    Un même budget est partagé par toutes les relaxations LP d'une résolution
    entière (coupes de Gomory, Branch-and-Bound).
    """

    def __init__(self, full_cells=60_000, tableau_cells=120_000):
        self.full_cells = full_cells
        self.tableau_cells = tableau_cells
        self.used = 0
        self.omitted_steps = 0       # itérations sans détail de pivotage
        self.omitted_tableaux = 0    # itérations non enregistrées

    def level(self):
        if self.used < self.full_cells:
            return "full"
        if self.used < self.tableau_cells:
            return "tableau"
        return "none"


# ---------------------------------------------------------------------------
# Point d'entrée public — méthode du simplexe (origine admissible)
# ---------------------------------------------------------------------------

def run_simplex(c_input, A_input, b_input, budget=None):
    """
    Résout  max Z = c^T x   s.c.   Ax <= b,  x >= 0
    Suppose que l'origine est admissible (b_i >= 0 pour tout i).
    """
    m = len(A_input)
    n = len(c_input)

    c = [Fraction(x) for x in c_input]
    A = [[Fraction(x) for x in row] for row in A_input]
    b = [Fraction(x) for x in b_input]

    # --- Condition nécessaire et suffisante : b >= 0 ---
    for i, bi in enumerate(b):
        if bi < 0:
            return {
                "status": "non_admissible",
                "message": (
                    f"L'origine n'est pas admissible : b{i+1} = {bi} < 0. "
                    "Utilisez la méthode des deux phases."
                ),
            }

    orig_vars = [f"x{i+1}" for i in range(n)]
    # Utiliser 'y' pour les variables d'écart au lieu de 's'
    slack_vars = [f"y{i+1}" for i in range(m)]
    var_names = orig_vars + slack_vars
    num_vars = n + m                          # colonnes hors RHS

    # Tableau initial  [LF | contraintes]
    lf_row = c + [Fraction(0)] * m + [Fraction(0)]
    tableau = [lf_row]
    for i in range(m):
        row = A[i][:] + [Fraction(0)] * m + [b[i]]
        row[n + i] = Fraction(1)              # variable d'écart y_{i+1}
        tableau.append(row)

    basis = [n + i for i in range(m)]        # base initiale : variables d'écart (y)

    iterations = []
    result = _simplex_core(tableau, basis, var_names, m, num_vars, iterations, budget=budget)

    if result["status"] == "unbounded":
        return {
            "status": "unbounded",
            "message": "Le problème est non borné : aucune variable sortante possible.",
            "iterations": iterations,
        }

    if result["status"] == "max_iter":
        return {
            "status": "max_iter",
            "message": f"Nombre maximal d'itérations ({MAX_ITER}) atteint.",
            "iterations": iterations,
        }

    z_star = -tableau[0][-1]
    solution = {name: "0" for name in orig_vars}
    for i, var_idx in enumerate(basis):
        if var_idx < n:
            solution[var_names[var_idx]] = fmt(tableau[i + 1][-1])

    return {
        "status": "optimal",
        "optimal_value": fmt(z_star),
        "solution": solution,
        "iterations": iterations,
        "n": n,
        "m": m,
        "var_names": orig_vars,
        # État final brut (Fractions) — utilisé par les méthodes entières
        # (coupes de Gomory, Branch-and-Bound) pour lire le tableau optimal.
        "final": {
            "tableau": tableau,
            "basis": basis,
            "var_names": var_names,
            "num_vars": num_vars,
            "n": n,
            "m": m,
            "z": z_star,
        },
    }


# ---------------------------------------------------------------------------
# Moteur du simplexe — réutilisable par la méthode des deux phases
# ---------------------------------------------------------------------------

def _simplex_core(tableau, basis, var_names, m, num_vars, iterations, start_iter=0, budget=None):
    """
    Exécute les itérations du simplexe sur le tableau fourni.
    - Modifie `tableau` et `basis` en place.
    - Ajoute les snapshots dans `iterations` (dans la limite de `budget`).
    - Retourne {"status": "optimal" | "unbounded" | "max_iter"}.

    Règle de pivot : coefficient LF le plus positif (cours). Après un pivot
    dégénéré (ratio minimum nul), on applique la règle de Bland (plus petit
    indice) jusqu'au prochain pivot non dégénéré : le cyclage est impossible.
    """
    bland = False
    for it_num in range(MAX_ITER):
        lf = tableau[0]
        number = start_iter + it_num

        # Variable entrante : coefficient LF le plus positif
        # (règle de Bland : premier coefficient LF positif)
        entering_col = -1
        max_coef = Fraction(0)
        for j in range(num_vars):
            if lf[j] > max_coef:
                max_coef = lf[j]
                entering_col = j
                if bland:
                    break

        if entering_col == -1:
            _emit(tableau, basis, var_names, m, num_vars, iterations, budget,
                  number, "optimal")
            return {"status": "optimal"}

        # Variable sortante : test du ratio minimum
        valid = [
            (tableau[i][-1] / tableau[i][entering_col], i)
            for i in range(1, m + 1)
            if tableau[i][entering_col] > 0
        ]

        if not valid:
            _emit(tableau, basis, var_names, m, num_vars, iterations, budget,
                  number, "unbounded", entering_col)
            return {"status": "unbounded"}

        min_ratio = min(r for r, _ in valid)
        ties = [i for r, i in valid if r == min_ratio]
        # À égalité : première ligne (règle de Bland : plus petit indice de variable)
        leaving_row = min(ties, key=lambda i: basis[i - 1]) if bland else ties[0]
        pivot_val = tableau[leaving_row][entering_col]

        _emit(tableau, basis, var_names, m, num_vars, iterations, budget,
              number, "pivot", entering_col, leaving_row, pivot_val, bland=bland)

        _pivot(tableau, leaving_row, entering_col)
        basis[leaving_row - 1] = entering_col
        bland = min_ratio == 0

    return {"status": "max_iter"}


def _pivot(tableau, pivot_row, pivot_col):
    """Opération de pivot en place sur l'élément (pivot_row, pivot_col)."""
    pivot_val = tableau[pivot_row][pivot_col]
    tableau[pivot_row] = [x / pivot_val for x in tableau[pivot_row]]
    for i in range(len(tableau)):
        if i != pivot_row:
            factor = tableau[i][pivot_col]
            if factor != 0:
                tableau[i] = [
                    tableau[i][j] - factor * tableau[pivot_row][j]
                    for j in range(len(tableau[i]))
                ]


def _emit(tableau, basis, var_names, m, num_vars, iterations, budget, number, status,
          entering_col=-1, leaving_row=-1, pivot_val=None, ratios=True, **extra):
    """
    Enregistre le snapshot d'une itération dans `iterations`, avec le détail
    du pivotage si `pivot_val` est fourni — dans la limite de `budget`.
    """
    level = budget.level() if budget else "full"
    if level == "none":
        budget.omitted_tableaux += 1
        return

    ratio_col = None
    if ratios:
        ratio_col = [None]
        for i in range(1, m + 1):
            if entering_col >= 0 and tableau[i][entering_col] > 0:
                ratio_col.append(fmt(tableau[i][-1] / tableau[i][entering_col]))
            else:
                ratio_col.append("—")

    snap = _snapshot(tableau, basis, var_names, m, num_vars,
                     entering_col, leaving_row, ratio_col, pivot_val)
    snap["number"] = number
    snap["status"] = status
    snap.update(extra)
    cells = (m + 1) * (num_vars + 1)

    if pivot_val is not None:
        if level == "full":
            snap["pivot_steps"] = _compute_pivot_steps(
                tableau, basis, var_names, m, num_vars, entering_col, leaving_row, pivot_val
            )
            cells += 2 * (num_vars + 1) * len(snap["pivot_steps"])
        else:
            budget.omitted_steps += 1

    iterations.append(snap)
    if budget:
        budget.used += cells


# ---------------------------------------------------------------------------
# Helpers — snapshot et détail du pivotage
# ---------------------------------------------------------------------------

def _snapshot(tableau, basis, var_names, m, num_vars, entering_col, leaving_row, ratios, pivot_val=None):
    """Construit la représentation d'un tableau pour le template."""
    rows_data = []

    for row_idx in range(m + 1):
        label = "LF" if row_idx == 0 else var_names[basis[row_idx - 1]]

        cells = []
        for col_idx in range(num_vars):
            val = fmt(tableau[row_idx][col_idx])
            if row_idx == leaving_row and col_idx == entering_col:
                ctype = "pivot"
            elif col_idx == entering_col:
                ctype = "entering"
            elif row_idx == leaving_row and leaving_row > 0:
                ctype = "leaving"
            else:
                ctype = "normal"
            cells.append({"value": val, "type": ctype})

        rhs_type = "leaving" if (row_idx == leaving_row and leaving_row > 0) else "normal"

        rows_data.append({
            "label": label,
            "is_lf": row_idx == 0,
            "is_leaving": row_idx == leaving_row and leaving_row > 0,
            "cells": cells,
            "rhs": {"value": fmt(tableau[row_idx][-1]), "type": rhs_type},
            "ratio": ratios[row_idx] if ratios else None,
        })

    return {
        "rows": rows_data,
        "col_headers": var_names[:num_vars],
        "entering": var_names[entering_col] if entering_col >= 0 else None,
        "leaving": var_names[basis[leaving_row - 1]] if leaving_row > 0 else None,
        "pivot_value": fmt(pivot_val) if pivot_val is not None else None,
    }


def _compute_pivot_steps(tableau, basis, var_names, m, num_vars, entering_col, leaving_row, pivot_val):
    """
    Calcule les opérations de pivotage ligne par ligne :
      1. Normalisation de la ligne pivot (kind="normalize")
      2. Éliminations dans les autres lignes (kind="eliminate")
    """
    pivot_label = var_names[basis[leaving_row - 1]]
    p_str = fmt(pivot_val)
    steps = []

    # --- Étape 1 : normalisation ---
    new_pivot_row = [x / pivot_val for x in tableau[leaving_row]]

    if pivot_val == Fraction(1):
        formula = f"L({pivot_label}) ← L({pivot_label})  (pivot = 1, inchangée)"
        operation = f"La ligne {pivot_label} est déjà normalisée (pivot = 1)"
    else:
        formula = f"L({pivot_label}) ← L({pivot_label}) ÷ {p_str}"
        operation = f"Diviser la ligne {pivot_label} par le pivot {p_str}"

    steps.append({
        "kind": "normalize",
        "formula": formula,
        "operation": operation,
        "row_label": pivot_label,
        "new_row": [fmt(v) for v in new_pivot_row],
    })

    # --- Étapes 2.. : éliminations ---
    for i in range(m + 1):
        if i == leaving_row:
            continue
        factor = tableau[i][entering_col]
        if factor == 0:
            continue

        row_label = "LF" if i == 0 else var_names[basis[i - 1]]
        f_str = fmt(abs(factor))
        sign = "−" if factor > 0 else "+"

        if abs(factor) == Fraction(1):
            formula = f"L({row_label}) ← L({row_label}) {sign} L({pivot_label})ₙₒᵤᵥ"
            if factor > 0:
                operation = f"Soustraire la ligne {pivot_label} de la ligne {row_label}"
            else:
                operation = f"Ajouter la ligne {pivot_label} à la ligne {row_label}"
        else:
            formula = f"L({row_label}) ← L({row_label}) {sign} {f_str} × L({pivot_label})ₙₒᵤᵥ"
            if factor > 0:
                operation = f"Soustraire {f_str} × ligne {pivot_label} de la ligne {row_label}"
            else:
                operation = f"Ajouter {f_str} × ligne {pivot_label} à la ligne {row_label}"

        new_row = [
            tableau[i][j] - factor * new_pivot_row[j]
            for j in range(num_vars + 1)
        ]
        steps.append({
            "kind": "eliminate",
            "formula": formula,
            "operation": operation,
            "row_label": row_label,
            "new_row": [fmt(v) for v in new_row],
        })

    return steps
