"""
Branch-and-Bound — cf. doc/branch_and_bound.md.

Résout  max Z = c^T x   s.c.  A x ≤ b,  x ≥ 0,  x entier
par énumération intelligente d'un arbre d'exploration.

Schéma du cours :
  1. Résoudre la relaxation LP du nœud courant (Simplexe / deux phases).
  2. Relaxation infaisable → élaguer le nœud.
  3. Solution entière → mettre à jour l'incumbent (meilleure solution entière)
     puis élaguer.
  4. Borne ≤ incumbent → élaguer (aucune amélioration possible).
  5. Sinon, brancher sur une variable fractionnaire x_j :
        fils gauche  : x_j ≤ ⌊x*_j⌋        fils droit : x_j ≥ ⌈x*_j⌉
  6. Sélection du nœud suivant : meilleure borne (best-bound), comme dans le
     pseudo-code du cours (file de priorité).
  Terminaison : file vide, ou limite de nœuds atteinte (incumbent partiel).
"""

import math
from fractions import Fraction

from .simplex import fmt
from .lp_relax import solve_lp_auto, extract_x

MAX_NODES = 40


def _is_integer(v):
    return Fraction(v).denominator == 1


def _frac_part(v):
    return v - Fraction(math.floor(v))


def run_branch_and_bound(c_input, A_input, b_input, minimize=False, max_nodes=MAX_NODES):
    n = len(c_input)
    c = [Fraction(v) for v in c_input]
    A = [[Fraction(v) for v in row] for row in A_input]
    b = [Fraction(v) for v in b_input]

    def disp(z):
        return fmt(-z if minimize else z)

    # Nœud : contraintes de branchement accumulées depuis la racine.
    root = {
        "id": 0, "parent": None, "depth": 0,
        "branch_label": None, "extra": [],           # [(row, rhs, label)]
        "parent_bound": None, "children": [],
    }
    nodes = {0: root}
    queue = [root]
    next_id = 1

    incumbent = None        # {"value": Fraction, "x": [...], "node": id}
    order = []              # ids dans l'ordre d'exploration
    processed = 0
    truncated = False

    while queue:
        if processed >= max_nodes:
            truncated = True
            break

        # --- Sélection best-bound : borne du parent la plus élevée ---
        best_i = 0
        for i in range(1, len(queue)):
            pb_i = queue[i]["parent_bound"]
            pb_b = queue[best_i]["parent_bound"]
            if pb_b is not None and (pb_i is None or pb_i > pb_b):
                best_i = i
        node = queue.pop(best_i)
        processed += 1
        order.append(node["id"])

        # --- Relaxation LP du nœud ---
        A_node = [row[:] for row in A] + [extra[0] for extra in node["extra"]]
        b_node = b[:] + [extra[1] for extra in node["extra"]]
        lp = solve_lp_auto(c, A_node, b_node)

        node["lp"] = lp
        node["lp_method"] = lp["method"]
        node["prefix"] = f"n{node['id']}-"

        if lp["status"] == "infeasible" or lp["status"] == "non_admissible":
            node["status"] = "infeasible"
            node["reason"] = "Relaxation LP infaisable → nœud élagué."
            continue

        if lp["status"] == "unbounded":
            node["status"] = "unbounded"
            node["reason"] = "Relaxation LP non bornée."
            if node["id"] == 0:
                return _result("unbounded", incumbent, root,
                               [nodes[i] for i in order], processed,
                               minimize, n,
                               message="La relaxation LP de la racine est non bornée : "
                                       "le Branch-and-Bound ne peut pas conclure.")
            continue

        if lp["status"] == "max_iter":
            # Élaguer ici serait mathématiquement faux (région possiblement
            # admissible) : on interrompt l'exploration avec un statut explicite.
            node["status"] = "error"
            node["reason"] = "Relaxation LP : nombre maximal d'itérations atteint (cyclage possible)."
            return _result("max_iter", incumbent, root,
                           [nodes[i] for i in order], processed, minimize, n,
                           message="Cyclage possible dans une relaxation LP : "
                                   "exploration interrompue. Incumbent partiel ci-dessous le cas échéant.")

        final = lp["final"]
        x = extract_x(final, n)
        bound = final["z"]                      # borne supérieure du sous-arbre (max)
        node["bound"] = bound
        node["bound_display"] = disp(bound)
        node["x_pairs"] = [
            {"var": f"x{j+1}", "value": fmt(x[j]), "frac": not _is_integer(x[j])}
            for j in range(n)
        ]

        # --- Élagage par borne ---
        # (en interne : max ; à l'affichage le sens de comparaison suit l'objectif)
        comp = "≥" if minimize else "≤"
        if incumbent is not None and bound <= incumbent["value"]:
            node["status"] = "pruned"
            node["reason"] = (
                f"Borne = {disp(bound)} {comp} incumbent = {disp(incumbent['value'])} "
                "→ aucune amélioration possible, nœud élagué."
            )
            continue

        # --- Solution entière → incumbent ---
        if all(_is_integer(v) for v in x):
            node["status"] = "integer"
            incumbent = {"value": bound, "x": x[:], "node": node["id"]}
            node["reason"] = (
                f"Solution entière : nouvel incumbent Z = {disp(bound)}. "
                "Nœud élagué (rien à brancher)."
            )
            node["is_incumbent_update"] = True
            # Élaguer les nœuds en attente dominés par le nouvel incumbent
            still_open = []
            for q in queue:
                if q["parent_bound"] is not None and q["parent_bound"] <= incumbent["value"]:
                    q["status"] = "pruned"
                    q["reason"] = (
                        f"Borne du parent = {disp(q['parent_bound'])} {comp} incumbent "
                        f"= {disp(incumbent['value'])} → élagué sans résolution."
                    )
                else:
                    still_open.append(q)
            queue = still_open
            continue

        # --- Branchement : variable la plus fractionnaire ---
        best_j, best_score = None, None
        for j in range(n):
            if not _is_integer(x[j]):
                f = _frac_part(x[j])
                score = min(f, 1 - f)
                if best_score is None or score > best_score:
                    best_j, best_score = j, score

        v = x[best_j]
        fl, ce = math.floor(v), math.ceil(v)
        node["status"] = "branched"
        node["frac_var"] = f"x{best_j+1}"
        node["frac_value"] = fmt(v)
        node["reason"] = (
            f"x{best_j+1} = {fmt(v)} fractionnaire → branchement : "
            f"x{best_j+1} ≤ {fl}  |  x{best_j+1} ≥ {ce}."
        )

        e_row = [Fraction(0)] * n
        e_row[best_j] = Fraction(1)
        neg_row = [Fraction(0)] * n
        neg_row[best_j] = Fraction(-1)

        for row, rhs, label in (
            (e_row, Fraction(fl), f"x{best_j+1} ≤ {fl}"),
            (neg_row, Fraction(-ce), f"x{best_j+1} ≥ {ce}"),
        ):
            child = {
                "id": next_id, "parent": node["id"], "depth": node["depth"] + 1,
                "branch_label": label,
                "extra": node["extra"] + [(row, rhs, label)],
                "parent_bound": bound, "children": [],
            }
            nodes[next_id] = child
            node["children"].append(child)
            queue.append(child)
            next_id += 1

    # Nœuds jamais explorés (limite atteinte) → marqués comme tels
    for q in queue:
        q["status"] = "unexplored"
        q["reason"] = "Nœud non exploré (limite de nœuds atteinte)."

    nodes_list = [nodes[i] for i in order]      # nœuds dans l'ordre d'exploration

    if truncated:
        return _result("max_nodes", incumbent, root, nodes_list, processed, minimize, n,
                       message=f"Limite de {max_nodes} nœuds atteinte. "
                               + ("Meilleure solution entière trouvée (incumbent) ci-dessous."
                                  if incumbent else "Aucune solution entière trouvée."))

    if incumbent is None:
        return _result("infeasible", None, root, nodes_list, processed, minimize, n,
                       message="L'arbre a été entièrement exploré sans trouver "
                               "de solution entière : le problème entier est infaisable.")

    return _result("optimal", incumbent, root, nodes_list, processed, minimize, n)


def _result(status, incumbent, root, nodes_list, processed, minimize, n, message=None):
    res = {
        "status": status,
        "tree": root,
        "nodes_list": nodes_list,
        "n_nodes": processed,
        "minimize": minimize,
        "message": message,
    }
    if incumbent is not None:
        z = -incumbent["value"] if minimize else incumbent["value"]
        res["optimal_value"] = fmt(z)
        res["solution"] = {f"x{j+1}": fmt(incumbent["x"][j]) for j in range(n)}
        res["incumbent_node"] = incumbent["node"]
    return res
