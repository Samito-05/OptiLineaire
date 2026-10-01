import logging
import re
from fractions import Fraction

from django.conf import settings
from django.shortcuts import render, redirect

from .simplex import run_simplex, DetailBudget
from .simplex_two_phase import run_two_phase
from .gomory import run_gomory
from .branch_bound import run_branch_and_bound

logger = logging.getLogger(__name__)

MAX_VARS = 30
MAX_CONSTRAINTS = 30

# Entier, décimal (point ou virgule), notation scientifique courte, ou fraction p/q
_NUMBER = re.compile(
    r"[+-]?(\d{1,12}(\.\d{0,12})?|\.\d{1,12})([eE][+-]?\d{1,2})?"
    r"|[+-]?\d{1,12}/\d{1,12}"
)

_OP_TEX = {"le": r"\le", "ge": r"\ge", "eq": "="}


class InputError(ValueError):
    """Saisie invalide : le message est affiché tel quel à l'utilisateur."""


def index(request, error=None):
    return render(request, "pb_lineaire/index.html", {
        "error": error,
        "var_choices": range(1, MAX_VARS + 1),
        "constraint_choices": range(1, MAX_CONSTRAINTS + 1),
    })


def solve(request):
    if request.method != "POST":
        return redirect("pb_lineaire:index")

    try:
        problem = _parse_problem(request.POST)
    except InputError as e:
        return index(request, error=str(e))

    try:
        return _solve(request, problem)
    except Exception:
        if settings.DEBUG:
            raise
        logger.exception("Échec de la résolution")
        return index(request, error="Erreur interne pendant la résolution du problème.")


# ---------------------------------------------------------------------------
# Lecture et validation du formulaire
# ---------------------------------------------------------------------------

def _parse_count(post, key, label, maximum):
    raw = post.get(key, "").strip()
    try:
        value = int(raw)
    except ValueError:
        raise InputError(f"{label} : « {raw} » n'est pas un entier.")
    if not 1 <= value <= maximum:
        raise InputError(f"{label} : {value} est hors limites (de 1 à {maximum}).")
    return value


def _parse_number(post, key, label):
    raw = post.get(key, "")
    text = "".join(raw.split()).replace(",", ".").replace("−", "-")
    if not text:
        return Fraction(0)
    if not _NUMBER.fullmatch(text):
        raise InputError(
            f"{label} : « {raw.strip()} » n'est pas un nombre valide "
            "(exemples : 3, -2.5, 1/3)."
        )
    try:
        return Fraction(text)
    except ZeroDivisionError:
        raise InputError(f"{label} : division par zéro dans « {raw.strip()} ».")


def _parse_problem(post):
    n = _parse_count(post, "n_vars", "Nombre de variables", MAX_VARS)
    m = _parse_count(post, "n_constraints", "Nombre de contraintes", MAX_CONSTRAINTS)

    c = [_parse_number(post, f"c_{j}", f"Coefficient c{j+1}") for j in range(n)]
    A, b, operators = [], [], []
    for i in range(m):
        A.append([
            _parse_number(post, f"a_{i}_{j}", f"Contrainte C{i+1}, coefficient de x{j+1}")
            for j in range(n)
        ])
        b.append(_parse_number(post, f"b_{i}", f"Contrainte C{i+1}, second membre"))
        op = post.get(f"op_{i}", "le")
        operators.append(op if op in _OP_TEX else "le")

    return {
        "n": n, "m": m, "c": c, "A": A, "b": b, "operators": operators,
        "obj_type": "min" if post.get("obj_type") == "min" else "max",
        "integer": post.get("integer") in ("on", "1", "true"),
        "int_method": "bb" if post.get("int_method") == "bb" else "gomory",
    }


# ---------------------------------------------------------------------------
# Résolution
# ---------------------------------------------------------------------------

def _solve(request, problem):
    c, A, b = problem["c"], problem["A"], problem["b"]
    minimize = problem["obj_type"] == "min"

    # Convertir vers la forme standard (max, <= uniquement)
    # "ge" : multiplier par -1 ; "eq" : scinder en deux contraintes (<= et >=)
    A_std, b_std, origins = [], [], []
    for i, op in enumerate(problem["operators"]):
        if op == "ge":
            A_std.append([-x for x in A[i]])
            b_std.append(-b[i])
            origins.append(f"C{i+1} × (−1)")
        elif op == "eq":
            A_std.append(A[i])
            b_std.append(b[i])
            origins.append(f"C{i+1}, côté ≤")
            A_std.append([-x for x in A[i]])
            b_std.append(-b[i])
            origins.append(f"C{i+1}, côté ≥, × (−1)")
        else:
            A_std.append(A[i])
            b_std.append(b[i])
            origins.append(f"C{i+1}")

    c_solve = [-ci for ci in c] if minimize else c
    std = {"c": c_solve, "A": A_std, "b": b_std, "origins": origins}
    budget = DetailBudget()

    # ------------------------------------------------------------------
    # Sélection automatique de la méthode :
    #   • variables entières  → coupes de Gomory ou Branch-and-Bound
    #     (seul choix laissé à l'utilisateur : les deux s'appliquent)
    #   • un b_i < 0 (forme ≤) → méthode des deux phases
    #   • sinon                → Simplexe direct (origine admissible)
    # ------------------------------------------------------------------
    lp_note = "Chaque relaxation LP est résolue par Simplexe ou deux phases selon le signe des \\(b_i\\)."

    if problem["integer"] and problem["int_method"] == "bb":
        result = run_branch_and_bound(c_solve, A_std, b_std, minimize=minimize, budget=budget)
        context = _build_context(result, problem, std, "bb", budget)
        context["auto_reason"] = (
            "Variables entières (\\(x_j \\in \\mathbb{Z}\\)) → Branch-and-Bound (votre choix). " + lp_note
        )
        return render(request, "pb_lineaire/result_branch_bound.html", context)

    if problem["integer"]:
        result = run_gomory(c_solve, A_std, b_std, minimize=minimize, budget=budget)
        context = _build_context(result, problem, std, "gomory", budget)
        context["auto_reason"] = (
            "Variables entières (\\(x_j \\in \\mathbb{Z}\\)) → méthode des coupes de Gomory (votre choix). " + lp_note
        )
        # Les coupes n'ont pas abouti : Branch-and-Bound garantit la progression.
        if result["status"] in ("max_cuts", "stalled"):
            context["fallback"] = run_branch_and_bound(
                c_solve, A_std, b_std, minimize=minimize, budget=budget
            )
            context["omitted"] = _omitted(budget)
        return render(request, "pb_lineaire/result_gomory.html", context)

    if any(bi < 0 for bi in b_std):
        neg = next(i for i, bi in enumerate(b_std) if bi < 0)
        result = run_two_phase(c_solve, A_std, b_std, budget=budget)
        if minimize and result.get("status") == "optimal":
            result["optimal_value"] = str(-Fraction(result["optimal_value"]))
            result["phase2"]["optimal_value"] = result["optimal_value"]
        context = _build_context(result, problem, std, "two_phase", budget)
        context["auto_reason"] = (
            f"Après mise sous forme \\(\\le\\), \\(b_{{{neg+1}}} = {_tex_num(b_std[neg])} < 0\\) : "
            "l'origine n'est pas admissible → méthode des deux phases "
            "(variable artificielle unique \\(\\delta\\))."
        )
        return render(request, "pb_lineaire/result_two_phase.html", context)

    result = run_simplex(c_solve, A_std, b_std, budget=budget)
    if minimize and result.get("status") == "optimal":
        result["optimal_value"] = str(-Fraction(result["optimal_value"]))
    context = _build_context(result, problem, std, "simplex", budget)
    context["auto_reason"] = (
        "Tous les \\(b_i \\ge 0\\) après mise sous forme \\(\\le\\) : "
        "l'origine est admissible → méthode du Simplexe."
    )
    return render(request, "pb_lineaire/result.html", context)


# ---------------------------------------------------------------------------
# Contexte d'affichage
# ---------------------------------------------------------------------------

def _tex_num(value):
    f = Fraction(value)
    sign = "-" if f < 0 else ""
    if f.denominator == 1:
        return f"{sign}{abs(f.numerator)}"
    return f"{sign}\\frac{{{abs(f.numerator)}}}{{{f.denominator}}}"


def _tex_expr(coefs, letter="x"):
    """Combinaison linéaire en LaTeX : [3, -2, 0, 1] → 3x_{1} - 2x_{2} + x_{4}."""
    parts = []
    for j, coef in enumerate(coefs, start=1):
        if coef == 0:
            continue
        a = abs(coef)
        term = f"{'' if a == 1 else _tex_num(a)}{letter}_{{{j}}}"
        if parts:
            parts.append(f" {'-' if coef < 0 else '+'} {term}")
        else:
            parts.append(f"-{term}" if coef < 0 else term)
    return "".join(parts) or "0"


def _omitted(budget):
    return {"steps": budget.omitted_steps, "tableaux": budget.omitted_tableaux}


def _build_context(result, problem, std, method, budget):
    minimize = problem["obj_type"] == "min"
    transformed = minimize or any(op != "le" for op in problem["operators"])

    std_form = None
    if transformed:
        std_form = {
            "minimize": minimize,
            "objective": (
                ("\\max Z' = -Z = " if minimize else "\\max Z = ") + _tex_expr(std["c"])
            ),
            "rows": [
                {
                    "tex": f"{_tex_expr(row)} \\le {_tex_num(bi)}",
                    "slack": f"y{i+1}",
                    "origin": origin,
                }
                for i, (row, bi, origin) in enumerate(zip(std["A"], std["b"], std["origins"]))
            ],
        }

    return {
        "result": result,
        "n": problem["n"],
        "m": problem["m"],
        "obj_type": problem["obj_type"],
        "method": method,
        "objective_tex": f"\\{problem['obj_type']} Z = {_tex_expr(problem['c'])}",
        "constraints_tex": [
            f"{_tex_expr(row)} {_OP_TEX[op]} {_tex_num(bi)}"
            for row, op, bi in zip(problem["A"], problem["operators"], problem["b"])
        ],
        "std_form": std_form,
        "omitted": _omitted(budget),
    }
