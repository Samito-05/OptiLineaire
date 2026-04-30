"""
Méthode des deux phases du simplexe.

Résout  max Z = c^T x   s.c.   Ax ≤ b,  x ≥ 0
même lorsque certains b_i < 0 (origine non admissible).

Stratégie pour b_i < 0 :
  • Multiplier la ligne i par −1  →  −A_i x ≤ −b_i  (RHS positif)
  • Ajouter une variable d'écart surplus s_i  (coeff −1, car contrainte ≥)
  • Ajouter une variable artificielle a_j  (coeff +1, en base initiale)

Phase 1 :  min Σ a_j   ≡   max −Σ a_j
Phase 2 :  max c^T x  sur la base admissible trouvée en Phase 1
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
    # Utiliser 'y' pour les variables d'écart (au lieu de 's')
    slack_vars = [f"y{i+1}" for i in range(m)]

    # Lignes nécessitant une variable artificielle (b_i < 0)
    needs_art  = [b[i] < Fraction(0) for i in range(m)]
    num_art    = sum(needs_art)
    art_vars   = [f"a{j+1}" for j in range(num_art)]

    all_vars   = orig_vars + slack_vars + art_vars   # colonnes Phase 1
    num_all    = n + m + num_art
    art_start  = n + m                               # indice première artificielle

    # -----------------------------------------------------------------------
    # Construction du tableau des contraintes
    # -----------------------------------------------------------------------
    constraint_rows = []
    basis           = []
    art_j           = 0

    for i in range(m):
        row = [Fraction(0)] * (num_all + 1)
        if not needs_art[i]:
            # b_i >= 0 → contrainte standard : A_i x + y_i = b_i
            for j in range(n):
                row[j] = A[i][j]
            row[n + i]  = Fraction(1)    # slack y_{i+1}
            row[-1]     = b[i]
            basis.append(n + i)          # y_{i+1} en base
        else:
            # b_i < 0 → multiplier par −1 : −A_i x − y_i + a_j = −b_i
            for j in range(n):
                row[j] = -A[i][j]
            row[n + i]             = Fraction(-1)   # surplus (coeff −1) (y_{i+1})
            row[art_start + art_j] = Fraction(1)    # artificielle a_{j+1}
            row[-1]                = -b[i]           # RHS positif
            basis.append(art_start + art_j)          # a_{j+1} en base
            art_j += 1

        constraint_rows.append(row)

    # -----------------------------------------------------------------------
    # Phase 1 : max −Σ a_j
    # -----------------------------------------------------------------------
    lf1 = [Fraction(0)] * num_all + [Fraction(0)]
    for j in range(num_art):
        lf1[art_start + j] = Fraction(-1)

    tableau_p1 = [lf1[:]] + [row[:] for row in constraint_rows]
    basis_p1   = basis[:]

    # Élimination des artificielles de la LF Phase 1
    # (car elles sont en base, on soustrait leurs lignes × leur coeff dans LF)
    for i, var_idx in enumerate(basis_p1):
        if var_idx >= art_start:
            factor = tableau_p1[0][var_idx]          # vaut −1
            if factor != 0:
                tableau_p1[0] = [
                    tableau_p1[0][k] - factor * tableau_p1[i + 1][k]
                    for k in range(num_all + 1)
                ]

    phase1_iters = []
    p1_status = _simplex_core(
        tableau_p1, basis_p1, all_vars, m, num_all, phase1_iters
    )

    # z_p1 = max(−Σa) ; min(Σa) = −z_p1
    z_p1      = -tableau_p1[0][-1]
    min_sum_a = -z_p1              # valeur minimale de la somme des artificielles

    # Infaisabilité si min(Σa) > 0
    if min_sum_a > Fraction(0):
        return {
            "status": "infeasible",
            "message": (
                "Le problème est infaisable : "
                f"la valeur minimale des variables artificielles est {fmt(min_sum_a)} > 0."
            ),
            "phase1": {
                "status": "infeasible",
                "iterations": phase1_iters,
                "optimal_value": fmt(min_sum_a),
                "var_names": all_vars,
            },
        }

    # Cas dégénéré : une artificielle reste en base avec valeur 0 → la pivoter hors de la base
    for i in range(m):
        if basis_p1[i] < art_start:
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
    p2_vars  = orig_vars + slack_vars    # on supprime les colonnes artificielles
    num_p2   = n + m

    # Supprimer les colonnes artificielles du tableau
    tableau_p2 = []
    for row in tableau_p1:
        tableau_p2.append(row[:num_p2] + [row[-1]])

    basis_p2 = basis_p1[:]

    # Nouvelle LF Phase 2 : objectif original
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
    p2_status = _simplex_core(
        tableau_p2, basis_p2, p2_vars, m, num_p2, phase2_iters
    )

    if p2_status["status"] == "unbounded":
        return {
            "status": "unbounded",
            "message": "Le problème est non borné.",
            "phase1": {
                "status": "optimal",
                "iterations": phase1_iters,
                "optimal_value": "0",
                "var_names": all_vars,
            },
            "phase2": {
                "status": "unbounded",
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
    }
