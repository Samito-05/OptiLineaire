from fractions import Fraction


def fmt(f):
    f = Fraction(f)
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


def run_simplex(c_input, A_input, b_input):
    """
    Résout max Z = c^T x  s.c.  Ax <= b, x >= 0
    Retourne un dict avec les itérations et le résultat.
    """
    m = len(A_input)
    n = len(c_input)

    c = [Fraction(x) for x in c_input]
    A = [[Fraction(x) for x in row] for row in A_input]
    b = [Fraction(x) for x in b_input]

    # --- Vérification admissibilité de l'origine ---
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
    slack_vars = [f"s{i+1}" for i in range(m)]
    var_names = orig_vars + slack_vars
    num_vars = n + m

    # --- Construction du tableau initial ---
    # Ligne LF (ligne 0) : [c1,...,cn, 0,...,0 | 0]
    # Lignes 1..m         : [A_i | e_i | b_i]
    tableau = []
    lf_row = c + [Fraction(0)] * m + [Fraction(0)]
    tableau.append(lf_row)
    for i in range(m):
        row = A[i][:] + [Fraction(0)] * m + [b[i]]
        row[n + i] = Fraction(1)
        tableau.append(row)

    # Base initiale : variables d'écart s1..sm
    basis = [n + i for i in range(m)]

    iterations = []

    for it_num in range(100):
        lf = tableau[0]

        # Choix variable entrante : coefficient le plus positif dans LF
        entering_col = -1
        max_coef = Fraction(0)
        for j in range(num_vars):
            if lf[j] > max_coef:
                max_coef = lf[j]
                entering_col = j

        # Calcul des ratios pour l'affichage
        ratios = [None]  # LF n'a pas de ratio
        for i in range(1, m + 1):
            if entering_col >= 0 and tableau[i][entering_col] > 0:
                ratios.append(fmt(tableau[i][-1] / tableau[i][entering_col]))
            else:
                ratios.append("—")

        if entering_col == -1:
            # Solution optimale
            snap = _snapshot(tableau, basis, var_names, m, n, -1, -1, ratios)
            snap["number"] = it_num
            snap["status"] = "optimal"
            iterations.append(snap)
            break

        # Choix variable sortante : test du ratio minimum
        valid = []
        for i in range(1, m + 1):
            if tableau[i][entering_col] > 0:
                valid.append((tableau[i][-1] / tableau[i][entering_col], i))

        if not valid:
            snap = _snapshot(tableau, basis, var_names, m, n, entering_col, -1, ratios)
            snap["number"] = it_num
            snap["status"] = "unbounded"
            iterations.append(snap)
            return {
                "status": "unbounded",
                "message": "Le problème est non borné : aucune variable sortante possible.",
                "iterations": iterations,
            }

        _, leaving_row = min(valid, key=lambda x: x[0])
        pivot_val = tableau[leaving_row][entering_col]

        snap = _snapshot(
            tableau, basis, var_names, m, n,
            entering_col, leaving_row, ratios, pivot_val
        )
        snap["number"] = it_num
        snap["status"] = "pivot"
        iterations.append(snap)

        # --- Opération de pivot ---
        tableau[leaving_row] = [x / pivot_val for x in tableau[leaving_row]]
        for i in range(m + 1):
            if i != leaving_row:
                factor = tableau[i][entering_col]
                if factor != 0:
                    tableau[i] = [
                        tableau[i][j] - factor * tableau[leaving_row][j]
                        for j in range(num_vars + 1)
                    ]

        basis[leaving_row - 1] = entering_col

    # --- Extraction de la solution ---
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
    }


def _snapshot(tableau, basis, var_names, m, n, entering_col, leaving_row, ratios, pivot_val=None):
    """Construit la représentation d'un tableau pour le template."""
    rows_data = []
    num_vars = n + m

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

        rhs_val = fmt(tableau[row_idx][-1])
        rhs_type = "leaving" if (row_idx == leaving_row and leaving_row > 0) else "normal"

        rows_data.append({
            "label": label,
            "is_lf": row_idx == 0,
            "is_leaving": row_idx == leaving_row and leaving_row > 0,
            "cells": cells,
            "rhs": {"value": rhs_val, "type": rhs_type},
            "ratio": ratios[row_idx] if ratios else None,
        })

    return {
        "rows": rows_data,
        "col_headers": var_names,
        "entering": var_names[entering_col] if entering_col >= 0 else None,
        "leaving": var_names[basis[leaving_row - 1]] if leaving_row > 0 else None,
        "pivot_value": fmt(pivot_val) if pivot_val is not None else None,
    }
