"""
Méthode des coupes de Gomory (Cutting Planes).

Résout  max Z = c^T x   s.c.  A x ≤ b,  x ≥ 0,  x entier.

Procédure du cours :
  1. Résoudre la relaxation linéaire continue (LP) par Simplexe
     (ou deux phases si l'origine n'est pas admissible).
  2. Si la solution est entière → fini.
  3. Sinon, choisir une variable de base x_Bi de valeur fractionnaire et lire
     la ligne du tableau optimal :   x_Bi + Σ_j a_ij t_j = b_i
  4. Extraire les parties fractionnaires {a_ij} (∈ [0,1)) et {b_i}, puis
     construire la coupe de Gomory :   Σ_j {a_ij} t_j ≥ {b_i}
     Elle exclut la solution fractionnaire courante sans exclure d'entiers.
  5. Réexprimer la coupe en variables originales (substitution des écarts),
     l'ajouter au modèle sous forme ≤, puis re-résoudre la relaxation.
  6. Répéter jusqu'à solution entière, ou basculer vers Branch-and-Bound
     si trop de coupes sont nécessaires.

Arithmétique exacte (fractions.Fraction) comme recommandé dans le cours.
"""

import math
from fractions import Fraction

from .simplex import fmt
from .lp_relax import solve_lp_auto, extract_x

MAX_CUTS = 15


# ---------------------------------------------------------------------------
# Helpers d'affichage
# ---------------------------------------------------------------------------

def _expr(terms):
    """
    Formate une combinaison linéaire [(coef, nom), …] en chaîne lisible.
    Les variables (x1, y2…) seront converties en LaTeX par le filtre math_text.
    """
    parts = []
    for coef, name in terms:
        if coef == 0:
            continue
        sign = "− " if coef < 0 else ("+ " if parts else "")
        a = abs(coef)
        coef_str = "" if a == 1 else f"{fmt(a)}·"
        parts.append(f"{sign}{coef_str}{name}")
    return " ".join(parts) if parts else "0"


def _frac_part(v):
    """Partie fractionnaire {v} = v − ⌊v⌋  (toujours dans [0, 1))."""
    return v - Fraction(math.floor(v))


def _is_integer(v):
    return Fraction(v).denominator == 1


# ---------------------------------------------------------------------------
# Point d'entrée public
# ---------------------------------------------------------------------------

def run_gomory(c_input, A_input, b_input, minimize=False, max_cuts=MAX_CUTS):
    n = len(c_input)
    c = [Fraction(v) for v in c_input]
    A_cur = [[Fraction(v) for v in row] for row in A_input]
    b_cur = [Fraction(v) for v in b_input]

    # Validité des coupes : pour x entier, les écarts y = b − Ax doivent être
    # entiers. On met donc chaque contrainte à l'échelle entière (lcm des
    # dénominateurs) — transformation équivalente qui ne change pas le problème.
    for i in range(len(A_cur)):
        D = math.lcm(*[v.denominator for v in A_cur[i] + [b_cur[i]]])
        if D > 1:
            A_cur[i] = [v * D for v in A_cur[i]]
            b_cur[i] = b_cur[i] * D

    rounds = []

    for k in range(max_cuts + 1):
        # --- Étape 1 : relaxation LP (méthode choisie automatiquement) ---
        lp = solve_lp_auto(c, A_cur, b_cur)

        if lp["status"] != "optimal":
            status = lp["status"]
            if status == "infeasible":
                msg = ("La relaxation LP est infaisable" +
                       (" après ajout des coupes." if rounds else "."))
            elif status == "unbounded":
                msg = "La relaxation LP est non bornée : la méthode des coupes ne peut pas conclure."
            else:
                msg = lp.get("message", "Échec de la relaxation LP.")
            rounds.append({
                "number": k,
                "prefix": f"c{k}-",
                "lp": lp,
                "lp_method": lp["method"],
                "lp_failed": True,
                "is_integer": False,
                "cut": None,
            })
            return {"status": status, "message": msg, "rounds": rounds,
                    "n_cuts": k, "minimize": minimize}

        final = lp["final"]
        x = extract_x(final, n)
        z = final["z"]
        z_disp = -z if minimize else z

        x_pairs = [
            {"var": f"x{j+1}", "value": fmt(x[j]), "frac": not _is_integer(x[j])}
            for j in range(n)
        ]
        integer_sol = all(_is_integer(v) for v in x)

        rnd = {
            "number": k,
            "prefix": f"c{k}-",
            "lp": lp,
            "lp_method": lp["method"],
            "lp_failed": False,
            "lp_value": fmt(z_disp),
            "x_pairs": x_pairs,
            "is_integer": integer_sol,
            "cut": None,
        }

        # --- Étape 2 : solution entière → fini ---
        if integer_sol:
            rounds.append(rnd)
            solution = {f"x{j+1}": fmt(x[j]) for j in range(n)}
            return {
                "status": "optimal",
                "optimal_value": fmt(z_disp),
                "solution": solution,
                "rounds": rounds,
                "n_cuts": k,
                "minimize": minimize,
            }

        if k == max_cuts:
            rounds.append(rnd)
            return {
                "status": "max_cuts",
                "message": (
                    f"{max_cuts} coupes ajoutées sans atteindre de solution entière. "
                    "En pratique on bascule alors vers le Branch-and-Bound "
                    "(Branch-and-Cut) pour garantir la progression."
                ),
                "rounds": rounds,
                "n_cuts": k,
                "minimize": minimize,
            }

        # --- Étape 3 : choisir la ligne source (variable de base la plus fractionnaire) ---
        rnd["cut"] = _build_cut(final, A_cur, b_cur, n)
        rounds.append(rnd)

        if rnd["cut"] is None:
            return {
                "status": "stalled",
                "message": (
                    "Impossible de dériver une coupe utile (coefficients tous "
                    "entiers après substitution). Utilisez le Branch-and-Bound."
                ),
                "rounds": rounds,
                "n_cuts": k,
                "minimize": minimize,
            }

        # --- Étape 5 : ajouter la coupe au modèle (forme ≤) ---
        A_cur.append(rnd["cut"]["new_row"])
        b_cur.append(rnd["cut"]["new_rhs"])


# ---------------------------------------------------------------------------
# Construction détaillée d'une coupe de Gomory
# ---------------------------------------------------------------------------

def _build_cut(final, A_cur, b_cur, n):
    """
    Construit la coupe de Gomory depuis le tableau optimal `final`,
    avec toutes les étapes intermédiaires pour l'affichage pédagogique.
    Retourne None si la coupe obtenue est vide (aucun coefficient).
    """
    tableau = final["tableau"]
    basis = final["basis"]
    var_names = final["var_names"]
    num_vars = final["num_vars"]
    m_cur = final["m"]

    # Ligne source : variable de décision basique à la valeur la plus
    # fractionnaire ({v} la plus proche de 1/2 ; à égalité, plus petit indice).
    best_row, best_score = None, None
    for i, var_idx in enumerate(basis):
        rhs = tableau[i + 1][-1]
        if var_idx < n and not rhs.denominator == 1:
            f = _frac_part(rhs)
            score = min(f, 1 - f)
            if best_score is None or score > best_score:
                best_row, best_score = i + 1, score
    if best_row is None:
        return None

    row = tableau[best_row]
    basic_idx = basis[best_row - 1]
    source_var = var_names[basic_idx]
    rhs = row[-1]

    # Termes hors base de la ligne :  x_Bi + Σ a_ij t_j = b_i
    nonbasic_terms = [
        (row[j], var_names[j])
        for j in range(num_vars)
        if j != basic_idx and row[j] != 0
    ]
    row_eq = f"{source_var} {('+ ' + _expr(nonbasic_terms)) if nonbasic_terms else ''} = {fmt(rhs)}".replace("+ −", "− ")

    # Parties fractionnaires {a_ij} de chaque coefficient hors base
    frac_rows = []
    cut_terms = []          # [(f_j, nom)] avec f_j > 0
    for coef, name in nonbasic_terms:
        f = _frac_part(coef)
        frac_rows.append({
            "var": name,
            "coef": fmt(coef),
            "floor": fmt(Fraction(math.floor(coef))),
            "frac": fmt(f),
        })
        if f != 0:
            cut_terms.append((f, name))
    f0 = _frac_part(rhs)

    # Coupe en variables du tableau :  Σ {a_ij} t_j ≥ {b_i}
    cut_tableau = f"{_expr(cut_terms)} ≥ {fmt(f0)}"

    # Substitution des écarts :  y_k = b_k − Σ_j A_kj x_j
    subst_lines = []
    g = [Fraction(0)] * n
    g0 = f0
    for f, name in cut_terms:
        j = var_names.index(name)
        if j < n:
            g[j] += f
        else:
            kk = j - n      # indice de la contrainte d'origine de l'écart
            for jj in range(n):
                g[jj] -= f * A_cur[kk][jj]
            g0 -= f * b_cur[kk]
            slack_def = _expr([(-A_cur[kk][jj], f"x{jj+1}") for jj in range(n)])
            subst_lines.append(
                f"{name} = {fmt(b_cur[kk])} {('+ ' + slack_def) if slack_def != '0' else ''}".replace("+ −", "− ")
            )

    if all(gj == 0 for gj in g):
        return None

    # Coupe en variables originales :  g·x ≥ g0
    cut_x = f"{_expr([(g[j], f'x{j+1}') for j in range(n)])} ≥ {fmt(g0)}"

    # Mise à l'échelle entière + arrondi de Chvátal–Gomory :
    # pour x entier, D·g·x est entier, donc D·g·x ≥ ⌈D·g0⌉.
    # Coefficients entiers → l'écart de la nouvelle contrainte reste entier,
    # ce qui garantit la validité des coupes suivantes.
    D = math.lcm(*[gj.denominator for gj in g])
    g_int = [gj * D for gj in g]
    rhs_scaled = g0 * D
    rhs_int = Fraction(math.ceil(rhs_scaled))
    cut_scaled = f"{_expr([(g_int[j], f'x{j+1}') for j in range(n)])} ≥ {fmt(rhs_int)}"

    # Forme standard ≤ (multiplication par −1), ajoutée au modèle
    new_row = [-gj for gj in g_int]
    new_rhs = -rhs_int
    cut_std = f"{_expr([(new_row[j], f'x{j+1}') for j in range(n)])} ≤ {fmt(new_rhs)}"

    return {
        "source_var": source_var,
        "source_value": fmt(rhs),
        "row_eq": row_eq,
        "frac_rows": frac_rows,
        "rhs_coef": fmt(rhs),
        "rhs_floor": fmt(Fraction(math.floor(rhs))),
        "rhs_frac": fmt(f0),
        "cut_tableau": cut_tableau,
        "subst_lines": subst_lines,
        "cut_x": cut_x,
        "scale": fmt(D) if D > 1 else None,
        "rhs_scaled": fmt(rhs_scaled),
        "strengthened": rhs_int != rhs_scaled,
        "cut_scaled": cut_scaled,
        "cut_std": cut_std,
        "new_row": new_row,
        "new_rhs": new_rhs,
    }
