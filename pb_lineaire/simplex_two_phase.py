"""
Méthode des deux phases du simplexe — variante à variable artificielle unique.

Résout  max Z = c^T x   s.c.   Ax ≤ b,  x ≥ 0
même lorsque certains b_i < 0 (origine non admissible).

Phase 1 (problème auxiliaire) :
  • Une SEULE variable artificielle δ, de coefficient −1 sur chaque ligne
        Ax + I y − δ·e = b
  • Objectif auxiliaire :  max (0·x − δ)   (≡ min δ)
  • δ est hors base au départ ; on la FORCE en base par un pivot sur la ligne
    dont le RHS est le plus négatif → toutes les lignes deviennent admissibles.
  • On applique ensuite le simplexe standard.
        δ = 0 à l'optimum  →  problème admissible, on passe en Phase 2
        δ > 0 à l'optimum  →  problème infaisable

Phase 2 :
  • On supprime la colonne δ.
  • On réexprime l'objectif original max c^T x dans la base courante.
  • On applique le simplexe standard.
"""

from fractions import Fraction
from .simplex import fmt, _simplex_core, _snapshot, _compute_pivot_steps


def run_two_phase(c_input, A_input, b_input):
    m = len(A_input)
    n = len(c_input)

    c = [Fraction(x) for x in c_input]
    A = [[Fraction(x) for x in row] for row in A_input]
    b = [Fraction(x) for x in b_input]

    orig_vars  = [f"x{i+1}" for i in range(n)]
    slack_vars = [f"y{i+1}" for i in range(m)]
    art_var    = "δ"                                  # variable artificielle unique

    all_vars   = orig_vars + slack_vars + [art_var]   # colonnes Phase 1
    num_all    = n + m + 1
    art_col    = n + m                                # indice de la colonne δ

    # -----------------------------------------------------------------------
    # Tableau du problème auxiliaire :  Ax + I y − δ·e = b
    #   • une seule artificielle δ, coefficient −1 sur chaque ligne
    #   • base initiale : variables d'écart y
    # -----------------------------------------------------------------------
    constraint_rows = []
    basis = []
    for i in range(m):
        row = [Fraction(0)] * (num_all + 1)
        for j in range(n):
            row[j] = A[i][j]
        row[n + i]   = Fraction(1)     # écart y_{i+1}
        row[art_col] = Fraction(-1)    # δ : −1 sur toutes les lignes
        row[-1]      = b[i]
        basis.append(n + i)            # y_{i+1} en base
        constraint_rows.append(row)

    # Objectif Phase 1 : max (0·x − δ)
    lf1 = [Fraction(0)] * num_all + [Fraction(0)]
    lf1[art_col] = Fraction(-1)

    tableau_p1 = [lf1[:]] + [r[:] for r in constraint_rows]
    basis_p1   = basis[:]

    phase1_iters = []

    # --- Tableau initial (avant forçage) : δ hors base, RHS éventuellement < 0 ---
    init_snap = _snapshot(tableau_p1, basis_p1, all_vars, m, num_all, -1, -1, None)
    init_snap["number"] = 0
    init_snap["status"] = "init"
    init_snap["caption"] = (
        "Problème auxiliaire : une seule variable artificielle δ (colonne −1 sur "
        "chaque ligne), objectif max(0·x − δ). δ est hors base ; on la force en base "
        "sur la ligne dont le RHS est le plus négatif pour rendre la base admissible."
    )
    phase1_iters.append(init_snap)

    start = 1

    # --- Forçage de δ en base sur la ligne au RHS le plus négatif ---
    min_i = min(range(m), key=lambda i: b[i])
    if b[min_i] < Fraction(0):
        leaving_row = min_i + 1
        pivot_val   = tableau_p1[leaving_row][art_col]   # = −1

        force_snap = _snapshot(tableau_p1, basis_p1, all_vars, m, num_all,
                               art_col, leaving_row, None, pivot_val)
        force_snap["number"] = start
        force_snap["status"] = "pivot"
        force_snap["caption"] = (
            f"Forçage : RHS le plus négatif sur la ligne {slack_vars[min_i]} "
            f"(b = {fmt(b[min_i])}). On pivote δ sur cette ligne — toutes les "
            "lignes redeviennent admissibles."
        )
        force_snap["steps_title"] = "Forcer δ en base"
        force_snap["steps_desc"] = (
            "On rend δ basique sur la ligne choisie, puis on l'élimine des autres "
            "lignes et de la ligne objectif."
        )
        force_snap["pivot_steps"] = _compute_pivot_steps(
            tableau_p1, basis_p1, all_vars, m, num_all, art_col, leaving_row, pivot_val
        )
        phase1_iters.append(force_snap)

        # Pivot effectif
        tableau_p1[leaving_row] = [x / pivot_val for x in tableau_p1[leaving_row]]
        for k in range(m + 1):
            if k != leaving_row:
                factor = tableau_p1[k][art_col]
                if factor != 0:
                    tableau_p1[k] = [
                        tableau_p1[k][j] - factor * tableau_p1[leaving_row][j]
                        for j in range(num_all + 1)
                    ]
        basis_p1[min_i] = art_col
        start += 1

    # --- Simplexe standard sur le problème auxiliaire ---
    p1_status = _simplex_core(
        tableau_p1, basis_p1, all_vars, m, num_all, phase1_iters, start_iter=start
    )

    if p1_status["status"] == "max_iter":
        return {
            "status": "max_iter",
            "message": "Nombre maximal d'itérations atteint en Phase 1 : cyclage possible.",
            "phase1": {
                "status": "max_iter",
                "iterations": phase1_iters,
                "var_names": all_vars,
            },
        }

    # --- Valeur de δ à l'optimum de Phase 1 ---
    delta_val = Fraction(0)
    for i, var_idx in enumerate(basis_p1):
        if var_idx == art_col:
            delta_val = tableau_p1[i + 1][-1]
            break

    if delta_val > Fraction(0):
        return {
            "status": "infeasible",
            "message": (
                "Le problème est infaisable : à l'optimum de Phase 1, "
                f"δ = {fmt(delta_val)} > 0."
            ),
            "phase1": {
                "status": "infeasible",
                "iterations": phase1_iters,
                "optimal_value": fmt(delta_val),
                "var_names": all_vars,
            },
        }

    # --- δ encore en base à 0 → la pivoter hors de la base ---
    for i in range(m):
        if basis_p1[i] != art_col:
            continue
        for j in range(n + m):
            if tableau_p1[i + 1][j] != Fraction(0):
                pv = tableau_p1[i + 1][j]
                tableau_p1[i + 1] = [x / pv for x in tableau_p1[i + 1]]
                for k in range(m + 1):
                    if k != i + 1:
                        fac = tableau_p1[k][j]
                        if fac != Fraction(0):
                            tableau_p1[k] = [
                                tableau_p1[k][l] - fac * tableau_p1[i + 1][l]
                                for l in range(num_all + 1)
                            ]
                basis_p1[i] = j
                break

    # -----------------------------------------------------------------------
    # Phase 2 : max c^T x depuis la base admissible de Phase 1
    # -----------------------------------------------------------------------
    p2_vars = orig_vars + slack_vars        # on supprime la colonne δ
    num_p2  = n + m

    tableau_p2 = [row[:num_p2] + [row[-1]] for row in tableau_p1]
    basis_p2   = basis_p1[:]

    # Nouvelle ligne objectif : objectif original
    lf2 = [Fraction(0)] * num_p2 + [Fraction(0)]
    for j in range(n):
        lf2[j] = c[j]
    tableau_p2[0] = lf2

    # Élimination des variables de base de la nouvelle LF
    for i, var_idx in enumerate(basis_p2):
        factor = tableau_p2[0][var_idx]
        if factor != 0:
            tableau_p2[0] = [
                tableau_p2[0][k] - factor * tableau_p2[i + 1][k]
                for k in range(num_p2 + 1)
            ]

    phase2_iters = []
    p2_status = _simplex_core(tableau_p2, basis_p2, p2_vars, m, num_p2, phase2_iters)

    if p2_status["status"] != "optimal":
        msg = (
            "Le problème est non borné."
            if p2_status["status"] == "unbounded"
            else "Nombre maximal d'itérations atteint en Phase 2 : cyclage possible."
        )
        return {
            "status": p2_status["status"],
            "message": msg,
            "phase1": {
                "status": "optimal",
                "iterations": phase1_iters,
                "optimal_value": "0",
                "var_names": all_vars,
            },
            "phase2": {
                "status": p2_status["status"],
                "iterations": phase2_iters,
                "var_names": p2_vars,
            },
        }

    # -----------------------------------------------------------------------
    # Extraction de la solution
    # -----------------------------------------------------------------------
    z_star   = -tableau_p2[0][-1]
    solution = {name: "0" for name in orig_vars}
    for i, var_idx in enumerate(basis_p2):
        if var_idx < n:
            solution[p2_vars[var_idx]] = fmt(tableau_p2[i + 1][-1])

    return {
        "status": "optimal",
        "optimal_value": fmt(z_star),
        "solution": solution,
        "phase1": {
            "status": "optimal",
            "iterations": phase1_iters,
            "optimal_value": "0",
            "var_names": all_vars,
        },
        "phase2": {
            "status": "optimal",
            "iterations": phase2_iters,
            "optimal_value": fmt(z_star),
            "solution": solution,
            "var_names": p2_vars,
        },
        "n": n,
        "m": m,
        "var_names": orig_vars,
        # État final brut (Fractions) — utilisé par les méthodes entières
        # (coupes de Gomory, Branch-and-Bound) pour lire le tableau optimal.
        "final": {
            "tableau": tableau_p2,
            "basis": basis_p2,
            "var_names": p2_vars,
            "num_vars": num_p2,
            "n": n,
            "m": m,
            "z": z_star,
        },
    }
