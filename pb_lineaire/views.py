from fractions import Fraction
from django.shortcuts import render, redirect
from .simplex import run_simplex
from .simplex_two_phase import run_two_phase


def index(request):
    return render(request, "pb_lineaire/index.html")


def solve(request):
    if request.method != "POST":
        return redirect("pb_lineaire:index")

    try:
        n        = int(request.POST.get("n_vars", 2))
        m        = int(request.POST.get("n_constraints", 2))
        obj_type = request.POST.get("obj_type", "max")
        method   = request.POST.get("method", "simplex")

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
        A_std, b_std = [], []
        for i in range(m):
            if operators[i] == "ge":
                A_std.append([-x for x in A[i]])
                b_std.append(-b[i])
            else:
                A_std.append(A[i])
                b_std.append(b[i])

        c_solve = [-ci for ci in c] if obj_type == "min" else c

        if method == "two_phase":
            return _solve_two_phase(request, c, c_solve, A_std, b_std, A, b, n, m, obj_type, operators)

        if method == "auto":
            if not all(bi >= 0 for bi in b_std):
                return _solve_two_phase(request, c, c_solve, A_std, b_std, A, b, n, m, obj_type, operators)

        result = run_simplex(c_solve, A_std, b_std)

        if obj_type == "min" and result.get("status") == "optimal":
            result["optimal_value"] = str(-Fraction(result["optimal_value"]))

        op_display = [{"ge": "≥", "eq": "="}.get(op, "≤") for op in operators]
        constraints = list(zip(
            [[str(aij) for aij in row] for row in A],
            op_display,
            [str(bi) for bi in b],
        ))

        context = {
            "result": result,
            "n": n,
            "m": m,
            "obj_type": obj_type,
            "c_display": [str(ci) for ci in c],
            "constraints": constraints,
        }
        return render(request, "pb_lineaire/result.html", context)

    except Exception as e:
        return render(request, "pb_lineaire/index.html", {"error": str(e)})


def _solve_two_phase(request, c_orig, c_solve, A_std, b_std, A_orig, b_orig, n, m, obj_type, operators=None):
    result = run_two_phase(c_solve, A_std, b_std)

    if obj_type == "min" and result.get("status") == "optimal":
        result["optimal_value"] = str(-Fraction(result["optimal_value"]))
        if "phase2" in result and result["phase2"].get("status") == "optimal":
            result["phase2"]["optimal_value"] = result["optimal_value"]

    context = _build_context(result, c_orig, A_orig, b_orig, n, m, obj_type, "two_phase", operators)
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
