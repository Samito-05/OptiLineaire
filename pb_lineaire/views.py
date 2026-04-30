from fractions import Fraction
from django.shortcuts import render, redirect
from .simplex import run_simplex


def index(request):
    return render(request, "pb_lineaire/index.html")


def solve(request):
    if request.method != "POST":
        return redirect("pb_lineaire:index")

    try:
        n = int(request.POST.get("n_vars", 2))
        m = int(request.POST.get("n_constraints", 2))
        obj_type = request.POST.get("obj_type", "max")

        c = []
        for i in range(n):
            raw = request.POST.get(f"c_{i}", "0").strip() or "0"
            c.append(Fraction(raw))

        A = []
        for i in range(m):
            row = []
            for j in range(n):
                raw = request.POST.get(f"a_{i}_{j}", "0").strip() or "0"
                row.append(Fraction(raw))
            A.append(row)

        b = []
        for i in range(m):
            raw = request.POST.get(f"b_{i}", "0").strip() or "0"
            b.append(Fraction(raw))

        c_solve = [-ci for ci in c] if obj_type == "min" else c

        result = run_simplex(c_solve, A, b)

        if obj_type == "min" and result.get("status") == "optimal":
            result["optimal_value"] = str(-Fraction(result["optimal_value"]))

        c_display = [str(ci) for ci in c]
        b_display = [str(bi) for bi in b]
        A_display = [[str(aij) for aij in row] for row in A]
        constraints = list(zip(A_display, b_display))

        context = {
            "result": result,
            "n": n,
            "m": m,
            "obj_type": obj_type,
            "c_display": c_display,
            "constraints": constraints,
        }
        return render(request, "pb_lineaire/result.html", context)

    except (ValueError, ZeroDivisionError, Exception) as e:
        return render(request, "pb_lineaire/index.html", {"error": str(e)})
