# OptiLinéaire — Project Documentation

**Status:** Django Linear & Integer Programming Solver — Simplex, Two-Phase, Gomory Cuts, Branch-and-Bound
**Type:** Educational Web Application (TP Assignment)
**Language:** Python + Django + JavaScript
**Target:** ING1-GIA, Semestre 2, 2025/2026

---

## 📁 Project Structure

```
OptiLineaire/
├── manage.py                          # Django management script
├── README.md                          # Project overview
├── requirements.txt                   # Python dependencies (Django==5.2.6)
├── run.ps1 / run.sh                   # Quick-start scripts
│
├── OptiLineaire/                      # Django project settings
│   ├── settings.py                    # Django configuration
│   ├── urls.py                        # Root URL routing
│   └── asgi.py / wsgi.py
│
└── pb_lineaire/                       # Main application
    ├── urls.py                        # App URL routing
    ├── views.py                       # Parsing, ≤-normalisation, method auto-selection
    │
    ├── simplex.py                     # Simplex engine (tableau, pivots, snapshots)
    ├── simplex_two_phase.py           # Two-phase method (single artificial δ)
    ├── lp_relax.py                    # Auto LP-relaxation dispatcher (simplex vs two-phase)
    ├── gomory.py                      # Gomory cutting planes (integer programming)
    ├── branch_bound.py                # Branch-and-Bound (integer programming)
    ├── tests.py                       # 33 unit tests (all methods + view routing)
    │
    ├── static/pb_lineaire/
    │   └── global.css                 # Swiss typographic style, light/dark theme
    │
    ├── templates/pb_lineaire/
    │   ├── base.html                  # Bootstrap 5 + MathJax + theme toggle
    │   ├── index.html                 # Input form (integer switch + Gomory/B&B choice)
    │   ├── result.html                # Simplex results
    │   ├── result_two_phase.html      # Two-phase results (Phase 1 + Phase 2)
    │   ├── result_gomory.html         # Gomory results (per-cut derivation steps)
    │   ├── result_branch_bound.html   # B&B results (exploration tree + node details)
    │   ├── _iterations.html           # Tableau iterations partial (param: iter_prefix)
    │   ├── _lp_block.html             # Renders an LP result, simplex or two-phase (params: lp, prefix)
    │   ├── _problem.html              # Problem recap card + "Choix de méthode" banner
    │   ├── _legend.html               # Color legend partial
    │   └── _bb_node.html              # Recursive B&B tree node partial
    │
    └── templatetags/
        └── math_notation.py           # Filters: math_var, math_text, math_index (LaTeX/MathJax)
```

---

## 🔧 Technology Stack

| Component | Details |
|-----------|---------|
| **Backend** | Django 5.2.6 |
| **Frontend** | Bootstrap 5.3.3, MathJax 3 (LaTeX rendering) |
| **Math** | `fractions.Fraction` everywhere — exact rational arithmetic, zero floats |
| **Styling** | CSS custom properties, light/dark theme, Swiss typographic style (Bricolage Grotesque / Archivo / Space Mono) |

---

## ⚠️ Course Conventions (MUST match code and UI)

These follow the professor's course material — do not "fix" them to textbook defaults:

- **Objective row** is called **LF** and sits in tableau row 0.
- **Entering variable:** coefficient **le plus positif** (most POSITIVE) of the LF row — *not* most negative.
- **Optimality:** all LF coefficients **≤ 0**.
- **Objective value** read from the tableau = **−(bottom-right corner)**.
- **Leaving variable:** minimum ratio `b_i / a_ij` over `a_ij > 0`; ties break on smallest row index.
- **Slack variables** are named `y1..ym` (not `s`).
- **Two-phase uses a SINGLE artificial variable δ** (column of −1 on every row), not one artificial per constraint. δ is forced into the basis by one pivot on the row with the most negative RHS — this makes all RHS ≥ 0 at once.
- Minimisation is solved internally as `max (−c)` and the displayed value negated back.

---

## 📐 Methods Implemented

### 1. Standard Simplex — `simplex.py`
For `max c^T x, Ax ≤ b, x ≥ 0` with all `b_i ≥ 0` (origin admissible).
- `run_simplex(c, A, b)` → result dict; refuses (status `non_admissible`) if some `b_i < 0`.
- `_simplex_core(...)` — shared engine reused by every other method; mutates tableau/basis in place, appends per-iteration snapshots (tableau cells with entering/leaving/pivot types, ratios, detailed pivot row-operations via `_compute_pivot_steps`).
- Statuses: `optimal`, `unbounded`, `max_iter` (100-iteration anti-cycling guard; no Bland rule — course lists it as optional mitigation).
- Optimal results carry a `final` key: raw `{tableau, basis, var_names, num_vars, n, m, z}` (Fractions) consumed by the integer methods.

### 2. Two-Phase Method — `simplex_two_phase.py`
For problems where some `b_i < 0` after ≤-normalisation.
- Phase 1: auxiliary problem `max(0·x − δ)` with `Ax + Iy − δe = b`; force δ basic (pivot on most-negative-RHS row); solve; `δ > 0` at optimum → `infeasible`.
- If δ remains basic at 0, it is pivoted out before Phase 2.
- Phase 2: drop δ column, restore original objective, eliminate basic variables from LF, run simplex.
- Returns `phase1` / `phase2` sub-results plus the same `final` raw state.

### 3. Gomory Cutting Planes — `gomory.py` (integer programming)
`run_gomory(c, A, b, minimize=False, max_cuts=15)`:
1. Solve LP relaxation via `lp_relax.solve_lp_auto` (simplex if all `b_i ≥ 0`, else two-phase).
2. All decision variables integer → done.
3. Else pick the **most fractional basic decision variable** ({v} closest to 1/2), read its tableau row `x_Bi + Σ a_ij t_j = b_i`.
4. Fractional parts: cut `Σ {a_ij} t_j ≥ {b_i}` over nonbasic vars (incl. slacks).
5. Substitute slacks (`y_k = b_k − Σ A_kj x_j`) to re-express the cut in original `x` variables.
6. **Validity-critical:** scale the cut to integer coefficients (lcm of denominators) + **Chvátal–Gomory rounding** `⌈D·g0⌉`. Without this, the cut's own slack is non-integer and *subsequent* cuts can wrongly exclude the integer optimum. Fractional input rows are also pre-scaled to integers for the same reason.
7. Add as `≤` row (RHS negative → next relaxation runs two-phase). Repeat.
- Statuses: `optimal`, `infeasible`, `unbounded`, `max_cuts` (suggests B&B, per course), `stalled`.
- Each round records full display data: `row_eq`, `frac_rows` table, `cut_tableau`, `subst_lines`, `cut_x`, `cut_scaled`, `cut_std`, plus the LP result for collapsible iteration display.

### 4. Branch-and-Bound — `branch_bound.py` (integer programming)
`run_branch_and_bound(c, A, b, minimize=False, max_nodes=40)`:
- Node selection: **best-bound** (max parent bound). Branching: **most fractional** variable, children `x_j ≤ ⌊v⌋` / `x_j ≥ ⌈v⌉` (the ≥ child stored as `−x_j ≤ −⌈v⌉`).
- Pruning: LP infeasible; bound ≤ incumbent (internal max-space); integer solution (updates incumbent + prunes dominated pending nodes).
- A node LP hitting `max_iter` **aborts** the whole run with status `max_iter` — never silently pruned (would be mathematically wrong).
- Display: `tree` (nested node dicts, rendered by recursive `_bb_node.html`) + `nodes_list` (exploration order). For min problems the displayed prune comparator flips to `≥` (values are negated for display).
- Statuses: `optimal`, `infeasible`, `unbounded` (root relaxation unbounded → cannot conclude), `max_nodes` (partial incumbent shown), `max_iter`.

---

## 🤖 Method Auto-Selection (`views.solve`)

The index page has **no method toggle**. Selection logic:

1. Parse input; normalise constraints to ≤ form (`≥` → ×(−1); `=` → split into ≤ pair).
2. **Integer checkbox ON** → user must choose between Gomory and B&B (radio, the only genuine choice since both apply) → `result_gomory.html` / `result_branch_bound.html`.
3. **Continuous:** all `b_i ≥ 0` → simplex (`result.html`); any `b_i < 0` → two-phase (`result_two_phase.html`).
4. Every result page shows a **"Choix de méthode"** banner (`auto_reason`) explaining the decision in MathJax notation (e.g. `\(b_1 = -2 < 0\)` → deux phases). Keep variable notation consistent with the tableau (b_i, δ, x_j ∈ ℤ).
5. Legacy `method=simplex|two_phase` POST values are still honoured (used by tests).

---

## 🎨 Frontend Rules

- Swiss typographic style: hairlines, square corners, mono uppercase labels, ink/paper palette.
- **No "AI-look" decorations**: no colored left side bars, no offset box-shadows, no badge color salad. Alerts are flat (thin border). B&B tree nodes are differentiated by **line style** (solid/thick/dashed/dotted), not color. Only meaningful highlights keep color: entering column (blue), leaving row (yellow), pivot cell (red), fractional values (red outline badge).
- All math notation goes through MathJax: templates use filters `math_var` (`"x1"` → `$x_{1}$`), `math_text` (vars inside prose), `math_index`. Python-generated display strings may embed `\( ... \)` LaTeX directly.
- Collapse element IDs must be unique per page: `_iterations.html` takes an `iter_prefix` parameter; Gomory rounds use `c{k}-`, B&B nodes `n{id}-`, phases append `p1-`/`p2-`.
- `_lp_block.html` renders any LP result (handles simplex vs two-phase internally) — use it whenever embedding a relaxation's iterations.

---

## 🔢 Numerical Representation

- `fractions.Fraction` end-to-end; `fmt()` (in `simplex.py`) renders `3/1 → "3"`, `1/3 → "1/3"`.
- Fractional parts: `{v} = v − ⌊v⌋ ∈ [0, 1)` (works for negatives: `{−3/2} = 1/2`).
- Integrality test: `Fraction(v).denominator == 1`.

---

## 📝 Naming Conventions

| Type | Format | Examples |
|------|--------|----------|
| Decision variables | `x{i}`, i = 1..n | x1, x2 |
| Slack variables | `y{i}`, i = 1..m | y1, y2 |
| Artificial variable | `δ` (single, two-phase) | δ |
| Entry points | `run_*` | `run_simplex`, `run_two_phase`, `run_gomory`, `run_branch_and_bound` |
| Internal helpers | `_*` | `_simplex_core`, `_build_cut`, `_snapshot` |

Result dict statuses: `optimal`, `unbounded`, `infeasible`, `non_admissible`, `max_iter`, `max_cuts`, `max_nodes`, `stalled`.

---

## 🧪 Testing & Validation

- `python manage.py test pb_lineaire` — **33 tests**: simplex (5), two-phase (6), Gomory (6), B&B (6), view routing incl. integer routes and min handling (10).
- Key regression tests: Gomory cuts must have integer coefficients; fractional input data; B&B min prune comparator displays `≥`.
- Audited 2026-06-11: results compared against **brute-force enumeration on 190 random instances** (integer & fractional data) — 0 mismatches; simplex vs two-phase cross-checked on 80 instances; two-phase fuzzed on 400 instances (eq pairs, redundant rows) — 0 crashes.
- When touching algorithm code, re-run a brute-force comparison campaign, not just the unit tests.

---

## 🚀 Running

```bash
pip install -r requirements.txt
python manage.py runserver        # http://localhost:8000/
python manage.py test pb_lineaire
```
Or `./run.sh` / `.\run.ps1`.

---

## 📋 Known Limitations (accepted, course-conformant)

- No Bland anti-cycling rule — 100-iteration cap with explicit `max_iter` status instead.
- Gomory may exceed `max_cuts=15` on hard instances → message directs to B&B (as the course prescribes).
- B&B capped at `max_nodes=40` → partial incumbent reported.
- Unbounded LP relaxation of an integer problem → reported as inconclusive/unbounded (cannot distinguish unbounded IP from infeasible IP).

---

**Last Updated:** 2026-06-11
**Version:** 2.0 (LP + Integer Programming, auto method selection)
