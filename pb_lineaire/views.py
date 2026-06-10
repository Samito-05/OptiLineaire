from fractions import Fraction
from django.shortcuts import render, redirect
from .simplex import run_simplex
from .simplex_two_phase import run_two_phase
from .gomory import run_gomory
from .branch_bound import run_branch_and_bound


def index(request):
    return render(request, "pb_lineaire/index.html")


def solve(request):
    if request.method != "POST":
        return redirect("pb_lineaire:index")

    try:
        n        = int(request.POST.get("n_vars", 2))
        m        = int(request.POST.get("n_constraints", 2))
        obj_type = request.POST.get("obj_type", "max")
        method   = request.POST.get("method", "auto")
        integer  = request.POST.get("integer") in ("on", "1", "true")
        int_method = request.POST.get("int_method", "gomory")

        c = [Fraction(request.POST.get(f"c_{i}", "0").strip() or "0") for i in range(n)]

        A = []
        b = []
        operators = []
        for i in range(m):
            A.append([
                Fraction(request.POST.get(f"a_{i}_{j}", "0").strip() or "0")
                for j in range(n)
            ])
            b.append(Fraction(request.POST.get(f"b_{i}", "0").strip() or "0"))
            operators.append(request.POST.get(f"op_{i}", "le").strip() or "le")

        # Convertir vers la forme standard (<= uniquement)
        # "ge" : multiplier par -1 ; "eq" : scinder en deux contraintes (<= et >=)
        A_std, b_std = [], []
        for i in range(m):
            if operators[i] == "ge":
                A_std.append([-x for x in A[i]])
                b_std.append(-b[i])
            elif operators[i] == "eq":
                A_std.append(A[i])
                b_std.append(b[i])
                A_std.append([-x for x in A[i]])
                b_std.append(-b[i])
            else:
                A_std.append(A[i])
                b_std.append(b[i])

        c_solve = [-ci for ci in c] if obj_type == "min" else c
        minimize = obj_type == "min"

        # ------------------------------------------------------------------
        # Sélection automatique de la méthode :
        #   • variables entières  → coupes de Gomory ou Branch-and-Bound
        #     (seul choix laissé à l'utilisateur : les deux s'appliquent)
        #   • un b_i < 0 (forme ≤) → méthode des deux phases
        #   • sinon                → Simplexe direct (origine admissible)
        # ------------------------------------------------------------------
        if integer:
            if int_method == "bb":
                result = run_branch_and_bound(c_solve, A_std, b_std, minimize=minimize)
                auto_reason = (
                    "Variables entières (\\(x_j \\in \\mathbb{Z}\\)) → Branch-and-Bound (votre choix). "
                    "Chaque relaxation LP est résolue par Simplexe ou deux phases selon le signe des \\(b_i\\)."
                )
                context = _build_context(result, c, A, b, n, m, obj_type, "bb", operators)
                context["auto_reason"] = auto_reason
                return render(request, "pb_lineaire/result_branch_bound.html", context)
            result = run_gomory(c_solve, A_std, b_std, minimize=minimize)
            auto_reason = (
                "Variables entières (\\(x_j \\in \\mathbb{Z}\\)) → méthode des coupes de Gomory (votre choix). "
                "Chaque relaxation LP est résolue par Simplexe ou deux phases selon le signe des \\(b_i\\)."
            )
            context = _build_context(result, c, A, b, n, m, obj_type, "gomory", operators)
            context["auto_reason"] = auto_reason
            return render(request, "pb_lineaire/result_gomory.html", context)

        if method == "two_phase":
            return _solve_two_phase(request, c, c_solve, A_std, b_std, A, b, n, m, obj_type, operators,
                                    auto_reason="Méthode des deux phases (demandée explicitement).")

        if method != "simplex" and not all(bi >= 0 for bi in b_std):
            neg = next(i for i, bi in enumerate(b_std) if bi < 0)
            return _solve_two_phase(
                request, c, c_solve, A_std, b_std, A, b, n, m, obj_type, operators,
                auto_reason=(
                    f"Après mise sous forme \\(\\le\\), \\(b_{{{neg+1}}} = {b_std[neg]} < 0\\) : "
                    "l'origine n'est pas admissible → méthode des deux phases "
                    "(variable artificielle unique \\(\\delta\\))."
                ),
            )

        result = run_simplex(c_solve, A_std, b_std)

        if obj_type == "min" and result.get("status") == "optimal":
            result["optimal_value"] = str(-Fraction(result["optimal_value"]))

        context = _build_context(result, c, A, b, n, m, obj_type, "simplex", operators)
        context["auto_reason"] = (
            "Tous les \\(b_i \\ge 0\\) après mise sous forme \\(\\le\\) : "
            "l'origine est admissible → méthode du Simplexe."
            if method != "simplex"
            else "Méthode du Simplexe (demandée explicitement)."
        )
        return render(request, "pb_lineaire/result.html", context)

    except Exception as e:
        return render(request, "pb_lineaire/index.html", {"error": str(e)})


def _solve_two_phase(request, c_orig, c_solve, A_std, b_std, A_orig, b_orig, n, m, obj_type,
                     operators=None, auto_reason=None):
    result = run_two_phase(c_solve, A_std, b_std)

    if obj_type == "min" and result.get("status") == "optimal":
        result["optimal_value"] = str(-Fraction(result["optimal_value"]))
        if "phase2" in result and result["phase2"].get("status") == "optimal":
            result["phase2"]["optimal_value"] = result["optimal_value"]

    context = _build_context(result, c_orig, A_orig, b_orig, n, m, obj_type, "two_phase", operators)
    context["auto_reason"] = auto_reason
    return render(request, "pb_lineaire/result_two_phase.html", context)


def _build_context(result, c, A, b, n, m, obj_type, method, operators=None):
    op_display = [
        {"ge": "≥", "eq": "="}.get(op, "≤")
        for op in (operators or ["le"] * len(b))
    ]
    return {
        "result": result,
        "n": n,
        "m": m,
        "obj_type": obj_type,
        "method": method,
        "c_display": [str(ci) for ci in c],
        "constraints": list(zip(
            [[str(aij) for aij in row] for row in A],
            op_display,
            [str(bi) for bi in b],
        )),
    }
