# OptiLinéaire Project Documentation

**Status:** Django Linear Programming Solver with Simplex & Two-Phase Methods  
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
│
├── OptiLineaire/                      # Django project settings
│   ├── __init__.py
│   ├── asgi.py                        # ASGI entry point
│   ├── settings.py                    # Django configuration
│   ├── urls.py                        # Root URL routing
│   └── wsgi.py                        # WSGI entry point
│
└── pb_lineaire/                       # Main application (Linear Programming)
    ├── __init__.py
    ├── admin.py                       # Django admin (unused)
    ├── apps.py                        # App configuration
    ├── models.py                      # Database models (unused)
    ├── urls.py                        # App URL routing
    ├── views.py                       # Request handlers
    │
    ├── simplex.py                     # Algorithm: Standard Simplex (Phase 1)
    ├── simplex_two_phase.py           # Algorithm: Two-Phase Method
    ├── tests.py                       # Unit tests (to expand)
    │
    ├── migrations/
    │   └── __init__.py
    │
    ├── static/
    │   └── pb_lineaire/
    │       └── global.css             # Global styles (light/dark theme)
    │
    ├── templates/
    │   └── pb_lineaire/
    │       ├── base.html              # Base template (Bootstrap 5)
    │       ├── index.html             # Input form for LP problem definition
    │       ├── result.html            # Results display (Simplex or Two-Phase)
    │       ├── result_two_phase.html  # Two-Phase specific results
    │       └── _iterations.html       # Reusable iteration display partial
    │
    └── templatetags/
        ├── __init__.py
        └── math_notation.py           # Custom template filters for LaTeX rendering
```

---

## 🔧 Technology Stack

| Component | Details |
|-----------|---------|
| **Backend** | Django 5.2.6 |
| **Frontend** | Bootstrap 5.3.3, MathJax 3 (LaTeX rendering) |
| **Math Library** | Python's `fractions.Fraction` (exact rational arithmetic) |
| **Styling** | CSS Custom Properties, Light/Dark theme support |
| **Language** | Python 3.8+ |

---

## 📐 Algorithms & Core Requirements (From TP Spec)

### Part I: Standard Simplex Method (Origin Admissible)
**File:** `pb_lineaire/simplex.py`

**Problem Form:**
```
max Z = c^T x  s.t.  Ax ≤ b,  x ≥ 0
where origin (x = 0) is admissible (all b_i ≥ 0)
```

**Requirements:**
- ✅ Implement simplex tableau using **list of lists**
- ✅ Maintain explicit **basis** (dict or equivalent)
- ✅ **Entering variable selection:** most negative reduced cost (c_j - z_j)
- ✅ **Leaving variable selection:** minimum ratio test (b_i / a_ij where a_ij > 0)
- ✅ **Pivot operation:** row reduction (elementary row operations)
- ✅ **Detect:**
  - Optimal solution (all reduced costs ≥ 0)
  - Unbounded problem (entering column all ≤ 0)
- ✅ **Display per iteration:**
  - Current tableau
  - Entering variable name
  - Leaving variable name

**Data Structures:**
```python
# Simplex result dictionary
{
    "status": "optimal|unbounded|non_admissible",
    "objective_value": Fraction(...),
    "solution": {x1: ..., x2: ...},
    "iterations": [
        {
            "iteration": 0,
            "tableau": [[...], [...], ...],
            "basis": {col_idx: var_name, ...},
            "entering": "x1",
            "leaving": "y1",
            "pivot": (row, col),
            "operations": "description"
        },
        ...
    ],
    "message": "description"
}
```

---

### Part II: Two-Phase Method (Origin Not Admissible)
**File:** `pb_lineaire/simplex_two_phase.py`

**Problem Form:**
```
max Z = c^T x  s.t.  Ax ≤ b,  x ≥ 0
where some b_i < 0 (origin not admissible)
```

**Phase 1: Find Initial Admissible Solution**
- ✅ Transform problem: for b_i < 0, multiply row by −1 → −A_i x ≤ −b_i
- ✅ Introduce **artificial variables** a_j with coefficient +1 in base
- ✅ Introduce **surplus variables** y_i with coefficient −1 for ≥ constraints
- ✅ Solve auxiliary problem: **min Σ a_j** (or **max −Σ a_j**)
- ✅ **Detect infeasibility:** if Phase 1 optimal value > 0, problem is infeasible

**Phase 2: Solve Original Problem**
- ✅ Remove artificial variables from tableau
- ✅ Use basis obtained from Phase 1
- ✅ Solve original problem: max c^T x using standard simplex

**Requirements:**
- ✅ **Detect cases:**
  - Optimal solution (if exists)
  - Infeasible problem
  - Unbounded problem
- ✅ **Display iterations** for both Phase 1 and Phase 2

---

## 🎨 Frontend & User Interface

### Input Form (`index.html`)
**User provides:**
- Number of variables (n)
- Number of constraints (m)
- Objective type: Maximize or Minimize
- Constraint operators: ≤, ≥, or =
- Objective coefficients: c₁, c₂, ..., cₙ
- Constraint matrix: A (m × n)
- RHS vector: b (m × 1)
- Method selection: Simplex, Two-Phase, or Auto

**Features:**
- Dynamic form generation (n×m matrix input)
- Random fill button (quick test examples)
- Method auto-detection (check if origin is admissible)

### Results Display (`result.html`, `result_two_phase.html`)
**Display Requirements:**
- ✅ Initial tableau with annotations
- ✅ **Step-by-step visualization:**
  - Highlight entering variable (column) in **blue**
  - Highlight leaving variable (row) in **yellow**
  - Highlight pivot element in **red**
- ✅ Display elementary row operations (description)
- ✅ Next Step button (iterate one step at a time)
- ✅ Final result: optimal value, solution (x₁, x₂, ..., xₙ)
- ✅ LaTeX rendering for mathematical notation (MathJax)

---

## 🔗 URL Routing

**File:** `pb_lineaire/urls.py`

| Endpoint | Method | Handler | Purpose |
|----------|--------|---------|---------|
| `/` | GET | `index` | Display input form |
| `/solve/` | POST | `solve` | Submit LP problem & compute solution |

**Flow:**
1. User fills form on `/` and submits
2. POST to `/solve/` with problem data
3. View chooses algorithm and calls `run_simplex()` or `run_two_phase()`
4. Renders `result.html` or `result_two_phase.html` with iteration data
5. User clicks "Next Step" (frontend pagination) to view each iteration

---

## 📊 View & Controller Logic

**File:** `pb_lineaire/views.py`

### `index(request)` - GET /
- Renders empty form

### `solve(request)` - POST /solve/
1. **Parse input:**
   - `n_vars`, `m_constraints` (integers)
   - `obj_type` (max/min)
   - `method` (simplex/two_phase/auto)
   - Objective coefficients `c[i]`
   - Constraint matrix `A[i][j]`
   - RHS vector `b[i]`
   - Operators `op[i]` (le/ge/eq)

2. **Normalize constraints:**
   - Convert ≥ to ≤: multiply row by −1
   - Convert = to two ≤ constraints (if needed)
   - Result: standard form with only ≤ and b_i ≥ 0

3. **Choose algorithm:**
   - **Auto mode:** if all b_i ≥ 0 → use simplex; else → use two_phase
   - **Explicit selection:** user chooses method

4. **Call algorithm:**
   - `run_simplex(c, A_std, b_std)` → returns result dict
   - `run_two_phase(c, A_std, b_std)` → returns result dict

5. **Return response:**
   - Render `result.html` with iteration data
   - Pass to template: iterations, objective value, final solution

---

## 🔢 Numerical Representation

**Precision:** Use `fractions.Fraction` from Python's standard library

**Why Fractions?**
- Exact rational arithmetic (no floating-point errors)
- Preserve mathematical exactness through all iterations
- Display: `Fraction(1, 3)` → "1/3"

**Utility Function:**
```python
def fmt(f):
    """Format Fraction: 3/1 → '3', 1/3 → '1/3'"""
    f = Fraction(f)
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"
```

---

## 📝 Naming Conventions

### Variable Names (in algorithms)
| Type | Format | Examples |
|------|--------|----------|
| **Original variables** | `x{i}` where i = 1..n | x1, x2, x3 |
| **Slack/Surplus variables** | `y{i}` where i = 1..m | y1, y2 (instead of s1, s2) |
| **Artificial variables** | `a{j}` where j = 1..num_art | a1, a2 |

### Function Names
| Pattern | Purpose | Example |
|---------|---------|---------|
| `run_*` | Entry point, public API | `run_simplex()`, `run_two_phase()` |
| `_*` | Internal helper function | `_simplex_core()`, `_compute_pivot_steps()` |
| `fmt()` | Format number to string | `fmt(Fraction(3, 2))` → "3/2" |

### Result Dictionary Keys
- `status`: "optimal", "unbounded", "infeasible", "non_admissible"
- `objective_value`: Fraction or None
- `solution`: {var_name: Fraction, ...}
- `iterations`: list of iteration snapshots
- `message`: human-readable string

---

## 🧪 Testing

**File:** `pb_lineaire/tests.py`

### Test Cases to Implement

**Test 1: Simple Admissible Problem (Simplex)**
```
max Z = 3x₁ + 2x₂
s.t. x₁ + x₂ ≤ 4
     x₁ ≤ 2
     x₂ ≤ 3
     x₁, x₂ ≥ 0
Expected: Z = 11, x₁ = 2, x₂ = 3
```

**Test 2: Non-Admissible Problem (Two-Phase)**
```
max Z = x₁ + x₂
s.t. x₁ + x₂ ≥ 2
     x₁ ≤ 3
     x₂ ≤ 3
     x₁, x₂ ≥ 0
Expected: Requires Phase 1 due to ≥ constraint
```

**Test 3: Unbounded Problem**
```
max Z = x₁ + x₂
s.t. x₁ + x₂ ≤ 10
     x₁, x₂ ≥ 0
Expected: status = "unbounded"
```

**Test 4: Infeasible Problem**
```
max Z = x₁ + x₂
s.t. x₁ + x₂ ≥ 10
     x₁ ≤ 1
     x₂ ≤ 1
     x₁, x₂ ≥ 0
Expected: status = "infeasible"
```

---

## 🎯 Precise Requirements Checklist

### Backend Implementation
- [x] **simplex.py:**
  - [x] Build initial tableau with slack variables
  - [x] Choose entering variable (most negative reduced cost)
  - [x] Choose leaving variable (minimum ratio test)
  - [x] Pivot operation
  - [x] Detect optimal, unbounded, non-admissible
  - [x] Snapshot each iteration
  - [x] Return structured result

- [x] **simplex_two_phase.py:**
  - [x] Phase 1: build auxiliary problem with artificial variables
  - [x] Phase 1: minimize sum of artificial variables
  - [x] Detect infeasibility (Phase 1 optimal > 0)
  - [x] Phase 2: remove artificials and solve original problem
  - [x] Return structured result with both phases

- [x] **views.py:**
  - [x] Parse form input
  - [x] Normalize constraints (≥, = to ≤ form)
  - [x] Route to correct algorithm
  - [x] Pass iterations to template

### Frontend Implementation
- [x] **index.html:**
  - [x] Dynamic form generation (n variables, m constraints)
  - [x] Matrix input for A, vector input for b
  - [x] Operator selection (≤, ≥, =)
  - [x] Random fill button
  - [x] Method selection (auto/simplex/two_phase)

- [x] **result.html / result_two_phase.html:**
  - [x] Display tableaus for each iteration
  - [x] Highlight entering column (blue)
  - [x] Highlight leaving row (yellow)
  - [x] Highlight pivot element (red)
  - [x] Display operation description
  - [x] Next Step button (paginate through iterations)
  - [x] Display final solution and objective value
  - [x] LaTeX rendering (MathJax)

- [x] **global.css:**
  - [x] Light/dark theme support
  - [x] Color variables for highlighting
  - [x] Responsive table styling
  - [x] Form styling

### Documentation & Deliverables
- [ ] **Report (5-10 pages):** (Not code, to be generated separately)
  - Explanation of both methods
  - Implementation description
  - Analysis of results
  - Detailed iteration walkthrough
  
- [ ] **Trace file:**
  - Iteration history
  - Successive tableaus
  - Pivot choices

---

## 🚀 Running the Project

### Setup
```bash
cd OptiLineaire
pip install -r requirements.txt
```

### Run Development Server
```bash
python manage.py runserver
```

### Access Application
```
http://localhost:8000/
```

### Run Tests
```bash
python manage.py test pb_lineaire
```

---

## 📋 Current Implementation Status

### ✅ Complete
- Simplex algorithm (one-phase, origin admissible)
- Two-phase method (for non-admissible origins)
- Django views & URL routing
- HTML templates with Bootstrap styling
- LaTeX/MathJax integration
- Light/dark theme support
- Fraction-based exact arithmetic

### 🔄 In Progress / To Expand
- [ ] Comprehensive test suite
- [ ] Edge case handling (degenerate cycles, multiple optima)
- [ ] Trace file generation (for reporting)
- [ ] Performance optimization (for large problems)
- [ ] Accessibility improvements

---

## 🔍 Code Quality Guidelines

### Comments & Documentation
- Explain the **why**, not the what
- Use French for mathematical descriptions (align with TP spec)
- Use English for code comments (Python convention)
- Each function: docstring with purpose, inputs, outputs

### Function Structure
```python
def my_algorithm(input_data):
    """
    Brief description.
    
    Args:
        input_data (Type): Description
    
    Returns:
        dict: Result with keys: 'status', 'objective_value', 'solution', 'iterations'
    """
    # Implementation
    return result
```

### Iteration Snapshots
Every iteration should capture:
```python
{
    "iteration": iteration_number,
    "tableau": deepcopy(tableau),  # Current state
    "basis": dict(basis),           # Variable to column mapping
    "entering": "x1",              # Entering variable name
    "leaving": "y2",               # Leaving variable name
    "pivot": (row_idx, col_idx),   # Pivot element location
    "operations": "description"     # Row operations performed
}
```

---

## 🐛 Common Patterns & Utilities

### Formatting Numbers
```python
# Use fmt() for all display output
from pb_lineaire.simplex import fmt
print(fmt(Fraction(3, 2)))  # "3/2"
print(fmt(Fraction(6, 2)))  # "3"
```

### Detecting Algorithm Needs
```python
# Check if origin is admissible
all_positive = all(bi >= 0 for bi in b)
if all_positive:
    result = run_simplex(c, A, b)
else:
    result = run_two_phase(c, A, b)
```

### Building Initial Basis
```python
# For simplex: slack variables form initial basis
basis = {}
for i in range(m):
    col_index = n + i  # slack variable column
    basis[col_index] = f"y{i+1}"
```

---

## 📞 Key Contacts (Group-Based)

- **Implementation:** Team (5 members)
- **Review:** Instructors verify against TP spec
- **Submission:** Code + Report + Trace file

---

## 📚 References

- **TP Specification:** Provided PDF (Optimization Linéaire, 2025/2026)
- **Simplex Theory:** Standard reference (any LP textbook)
- **Django Docs:** https://docs.djangoproject.com/
- **MathJax Docs:** https://docs.mathjax.org/

---

## 🎓 Learning Objectives

By implementing this project, students will:
1. ✅ Understand the simplex algorithm in detail
2. ✅ Handle non-admissible origins (two-phase method)
3. ✅ Detect special cases (unbounded, infeasible)
4. ✅ Build an interactive web UI with Django
5. ✅ Work with exact rational arithmetic
6. ✅ Practice modular, well-documented code

---

**Last Updated:** 2026-06-10  
**Version:** 1.0 (Full Specification)
