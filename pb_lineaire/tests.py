from fractions import Fraction

from django.test import SimpleTestCase
from django.urls import reverse

from .simplex import run_simplex, DetailBudget
from .simplex_two_phase import run_two_phase
from .gomory import run_gomory
from .branch_bound import run_branch_and_bound


# max 3x1 + 9x2  s.c.  x1 + 6x2 <= 15, 9x1 + 4x2 <= 19 — Gomory dépasse 15 coupes
GOMORY_HARD = {
    "c_0": "3", "c_1": "9",
    "a_0_0": "1", "a_0_1": "6", "b_0": "15", "op_0": "le",
    "a_1_0": "9", "a_1_1": "4", "b_1": "19", "op_1": "le",
}
GOMORY_HARD_OPT = "21"


class SimplexTests(SimpleTestCase):
    def test_optimal_simple(self):
        # max Z = 3x1 + 2x2  s.c.  x1 + x2 <= 4, x1 <= 2, x2 <= 3
        # Optimum : Z = 10 en (2, 2)
        result = run_simplex(
            [3, 2],
            [[1, 1], [1, 0], [0, 1]],
            [4, 2, 3],
        )
        self.assertEqual(result["status"], "optimal")
        self.assertEqual(result["optimal_value"], "10")
        self.assertEqual(result["solution"]["x1"], "2")
        self.assertEqual(result["solution"]["x2"], "2")

    def test_fractional_solution(self):
        # max Z = x1 + x2  s.c.  2x1 + x2 <= 3, x1 + 2x2 <= 3
        # Optimum : Z = 2 en (1, 1)
        result = run_simplex(
            [1, 1],
            [[2, 1], [1, 2]],
            [3, 3],
        )
        self.assertEqual(result["status"], "optimal")
        self.assertEqual(result["optimal_value"], "2")

    def test_unbounded(self):
        # max Z = x1 + x2  s.c.  -x1 + x2 <= 1  → non borné
        result = run_simplex(
            [1, 1],
            [[-1, 1]],
            [1],
        )
        self.assertEqual(result["status"], "unbounded")

    def test_non_admissible_origin(self):
        # b contient une valeur négative → origine non admissible
        result = run_simplex(
            [1, 1],
            [[-1, -1]],
            [-2],
        )
        self.assertEqual(result["status"], "non_admissible")

    def test_iterations_recorded(self):
        result = run_simplex(
            [3, 2],
            [[1, 1], [1, 0], [0, 1]],
            [4, 2, 3],
        )
        self.assertGreater(len(result["iterations"]), 0)
        self.assertEqual(result["iterations"][-1]["status"], "optimal")


class AntiCyclingAndBudgetTests(SimpleTestCase):
    # Exemple de Beale : cycle avec la règle du plus grand coefficient seule
    BEALE = (
        [Fraction(3, 4), -150, Fraction(1, 50), -6],
        [[Fraction(1, 4), -60, Fraction(-1, 25), 9],
         [Fraction(1, 2), -90, Fraction(-1, 50), 3],
         [0, 0, 1, 0]],
        [0, 0, 1],
    )

    def test_beale_example_does_not_cycle(self):
        result = run_simplex(*self.BEALE)
        self.assertEqual(result["status"], "optimal")
        self.assertEqual(result["optimal_value"], "1/20")
        self.assertTrue(any(it.get("bland") for it in result["iterations"]))

    def test_non_degenerate_problem_never_uses_bland(self):
        result = run_simplex([3, 2], [[1, 1], [1, 0], [0, 1]], [4, 2, 3])
        self.assertFalse(any(it.get("bland") for it in result["iterations"]))

    def test_budget_limits_recorded_detail_not_the_result(self):
        args = ([5, 4], [[6, 4], [1, 2]], [24, 6])
        full = run_simplex(*args)
        budget = DetailBudget(full_cells=0, tableau_cells=10**9)
        no_steps = run_simplex(*args, budget=budget)
        self.assertEqual(len(no_steps["iterations"]), len(full["iterations"]))
        self.assertFalse(any("pivot_steps" in it for it in no_steps["iterations"]))
        self.assertGreater(budget.omitted_steps, 0)

        budget = DetailBudget(full_cells=0, tableau_cells=0)
        nothing = run_simplex(*args, budget=budget)
        self.assertEqual(nothing["iterations"], [])
        self.assertEqual(budget.omitted_tableaux, len(full["iterations"]))
        self.assertEqual(nothing["optimal_value"], full["optimal_value"])


class TwoPhaseTests(SimpleTestCase):
    def test_optimal_with_negative_rhs(self):
        # max Z = x1 + x2  s.c.  x1 + x2 >= 2 (→ -x1 - x2 <= -2), x1 <= 3, x2 <= 3
        # Optimum : Z = 6 en (3, 3)
        result = run_two_phase(
            [1, 1],
            [[-1, -1], [1, 0], [0, 1]],
            [-2, 3, 3],
        )
        self.assertEqual(result["status"], "optimal")
        self.assertEqual(result["optimal_value"], "6")
        self.assertEqual(result["solution"]["x1"], "3")
        self.assertEqual(result["solution"]["x2"], "3")

    def test_prof_example(self):
        # Exemple du prof : max x1 - x2
        #   -2x1 + x2 <= -2   (b1 < 0)
        #    x1 - 2x2 <= 2
        #    x1 + x2  <= 5
        # Optimum attendu : Z = 3 en (4, 1)
        result = run_two_phase(
            [1, -1],
            [[-2, 1], [1, -2], [1, 1]],
            [-2, 2, 5],
        )
        self.assertEqual(result["status"], "optimal")
        self.assertEqual(result["optimal_value"], "3")
        self.assertEqual(result["solution"]["x1"], "4")
        self.assertEqual(result["solution"]["x2"], "1")

    def test_single_artificial_variable(self):
        # Une seule variable artificielle δ, quel que soit le nombre de b_i < 0
        result = run_two_phase(
            [1, 1],
            [[-1, -1], [-1, 0], [0, 1]],
            [-2, -1, 3],
        )
        self.assertIn("δ", result["phase1"]["var_names"])
        self.assertEqual(result["phase1"]["var_names"].count("δ"), 1)

    def test_infeasible(self):
        # x1 + x2 >= 10, x1 <= 1, x2 <= 1 → infaisable
        result = run_two_phase(
            [1, 1],
            [[-1, -1], [1, 0], [0, 1]],
            [-10, 1, 1],
        )
        self.assertEqual(result["status"], "infeasible")
        self.assertIn("phase1", result)

    def test_unbounded_phase2(self):
        # max Z = x1  s.c.  x1 >= 1 (→ -x1 <= -1) → non borné
        result = run_two_phase(
            [1],
            [[-1]],
            [-1],
        )
        self.assertEqual(result["status"], "unbounded")

    def test_both_phases_have_iterations(self):
        result = run_two_phase(
            [1, 1],
            [[-1, -1], [1, 0], [0, 1]],
            [-2, 3, 3],
        )
        self.assertGreater(len(result["phase1"]["iterations"]), 0)
        self.assertGreater(len(result["phase2"]["iterations"]), 0)


class GomoryTests(SimpleTestCase):
    def test_lp_already_integer(self):
        # Relaxation LP entière dès le départ → 0 coupe
        result = run_gomory(
            [3, 2],
            [[1, 1], [1, 0], [0, 1]],
            [4, 2, 3],
        )
        self.assertEqual(result["status"], "optimal")
        self.assertEqual(result["optimal_value"], "10")
        self.assertEqual(result["n_cuts"], 0)
        self.assertTrue(result["rounds"][0]["is_integer"])

    def test_fractional_lp_needs_cuts(self):
        # max 5x1 + 4x2  s.c.  6x1 + 4x2 <= 24, x1 + 2x2 <= 6
        # Relaxation : (3, 3/2), Z = 21 ; optimum entier : Z = 20 en (4, 0)
        result = run_gomory(
            [5, 4],
            [[6, 4], [1, 2]],
            [24, 6],
        )
        self.assertEqual(result["status"], "optimal")
        self.assertEqual(result["optimal_value"], "20")
        self.assertGreater(result["n_cuts"], 0)
        # Chaque coupe documentée avec ses étapes
        cut = result["rounds"][0]["cut"]
        self.assertIsNotNone(cut)
        self.assertIn("row_eq", cut)
        self.assertIn("frac_rows", cut)
        self.assertIn("cut_tableau", cut)
        self.assertIn("cut_std", cut)

    def test_minimize(self):
        # min x1 + x2  s.c.  3x1 + 2x2 >= 5  → entier : (1,1) Z=2 (ou (0,3)...)
        # forme <= : -3x1 - 2x2 <= -5
        result = run_gomory([-1, -1], [[-3, -2]], [-5], minimize=True)
        self.assertEqual(result["status"], "optimal")
        self.assertEqual(result["optimal_value"], "2")

    def test_infeasible(self):
        result = run_gomory(
            [1, 1],
            [[-1, -1], [1, 0], [0, 1]],
            [-10, 1, 1],
        )
        self.assertEqual(result["status"], "infeasible")

    def test_cuts_have_integer_coefficients(self):
        # Validité : les coupes ajoutées doivent être à coefficients entiers
        # (sinon les écarts des coupes ne sont pas entiers et les coupes
        # suivantes seraient invalides).
        result = run_gomory([5, 4], [[6, 4], [1, 2]], [24, 6])
        self.assertEqual(result["status"], "optimal")
        for rnd in result["rounds"]:
            if rnd["cut"]:
                for coef in rnd["cut"]["new_row"]:
                    self.assertEqual(Fraction(coef).denominator, 1)
                self.assertEqual(Fraction(rnd["cut"]["new_rhs"]).denominator, 1)

    def test_fractional_input_data(self):
        # Données fractionnaires : mise à l'échelle entière des contraintes.
        # x1/2 + x2 <= 5/2 ; x1 + x2/2 <= 5/2 → optimum entier Z = 3 ((2,1) ou (1,2))
        result = run_gomory(
            [1, 1],
            [[Fraction(1, 2), 1], [1, Fraction(1, 2)]],
            [Fraction(5, 2), Fraction(5, 2)],
        )
        self.assertEqual(result["status"], "optimal")
        self.assertEqual(result["optimal_value"], "3")


class BranchAndBoundTests(SimpleTestCase):
    def test_lp_already_integer(self):
        result = run_branch_and_bound(
            [3, 2],
            [[1, 1], [1, 0], [0, 1]],
            [4, 2, 3],
        )
        self.assertEqual(result["status"], "optimal")
        self.assertEqual(result["optimal_value"], "10")
        self.assertEqual(result["n_nodes"], 1)
        self.assertEqual(result["tree"]["status"], "integer")

    def test_branching_needed(self):
        # max 5x1 + 4x2  s.c.  6x1 + 4x2 <= 24, x1 + 2x2 <= 6 → Z* = 20 en (4, 0)
        result = run_branch_and_bound(
            [5, 4],
            [[6, 4], [1, 2]],
            [24, 6],
        )
        self.assertEqual(result["status"], "optimal")
        self.assertEqual(result["optimal_value"], "20")
        self.assertEqual(result["solution"]["x1"], "4")
        self.assertEqual(result["solution"]["x2"], "0")
        self.assertEqual(result["tree"]["status"], "branched")
        self.assertEqual(len(result["tree"]["children"]), 2)

    def test_minimize(self):
        result = run_branch_and_bound([-1, -1], [[-3, -2]], [-5], minimize=True)
        self.assertEqual(result["status"], "optimal")
        self.assertEqual(result["optimal_value"], "2")

    def test_infeasible_integer(self):
        # 2x1 = 1 impossible en entier : 2x1 <= 1 et 2x1 >= 1
        result = run_branch_and_bound(
            [1],
            [[2], [-2]],
            [1, -1],
        )
        self.assertEqual(result["status"], "infeasible")

    def test_min_prune_reason_uses_correct_comparator(self):
        # En minimisation, les bornes affichées sont négées : la comparaison
        # affichée doit être ≥ (et non ≤) pour rester vraie à la lecture.
        result = run_branch_and_bound([-1, -1], [[-3, -2]], [-5], minimize=True)
        for node in result["nodes_list"]:
            reason = node.get("reason", "")
            if "incumbent" in reason and "Borne" in reason:
                self.assertIn("≥", reason)
                self.assertNotIn("≤", reason)

    def test_nodes_have_lp_details(self):
        result = run_branch_and_bound(
            [5, 4],
            [[6, 4], [1, 2]],
            [24, 6],
        )
        for node in result["nodes_list"]:
            self.assertIn("lp", node)
            self.assertIn("reason", node)


class SolveViewTests(SimpleTestCase):
    def _post(self, data):
        return self.client.post(reverse("pb_lineaire:solve"), data)

    def test_get_redirects_to_index(self):
        response = self.client.get(reverse("pb_lineaire:solve"))
        self.assertEqual(response.status_code, 302)

    def test_simplex_max(self):
        response = self._post({
            "n_vars": "2", "n_constraints": "2",
            "obj_type": "max",
            "c_0": "3", "c_1": "2",
            "a_0_0": "1", "a_0_1": "1", "b_0": "4", "op_0": "le",
            "a_1_0": "1", "a_1_1": "0", "b_1": "2", "op_1": "le",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["result"]["status"], "optimal")
        self.assertEqual(response.context["result"]["optimal_value"], "10")

    def test_min_objective_negates_value(self):
        # min Z = x1 + x2  s.c.  x1 + x2 >= 2 → Z* = 2
        response = self._post({
            "n_vars": "2", "n_constraints": "1",
            "obj_type": "min",
            "c_0": "1", "c_1": "1",
            "a_0_0": "1", "a_0_1": "1", "b_0": "2", "op_0": "ge",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["result"]["status"], "optimal")
        self.assertEqual(response.context["result"]["optimal_value"], "2")

    def test_eq_constraint_split(self):
        # max Z = 2x1 + 3x2  s.c.  x1 + x2 = 4, x1 <= 3 → Z* = 12 en (0, 4)
        response = self._post({
            "n_vars": "2", "n_constraints": "2",
            "obj_type": "max",
            "c_0": "2", "c_1": "3",
            "a_0_0": "1", "a_0_1": "1", "b_0": "4", "op_0": "eq",
            "a_1_0": "1", "a_1_1": "0", "b_1": "3", "op_1": "le",
        })
        self.assertEqual(response.status_code, 200)
        result = response.context["result"]
        self.assertEqual(result["status"], "optimal")
        self.assertEqual(result["optimal_value"], "12")
        self.assertEqual(result["solution"]["x1"], "0")
        self.assertEqual(result["solution"]["x2"], "4")

    def test_auto_picks_simplex_when_admissible(self):
        response = self._post({
            "n_vars": "2", "n_constraints": "1",
            "obj_type": "max",
            "c_0": "1", "c_1": "1",
            "a_0_0": "1", "a_0_1": "1", "b_0": "4", "op_0": "le",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pb_lineaire/result.html")

    def test_auto_picks_two_phase_when_not_admissible(self):
        response = self._post({
            "n_vars": "2", "n_constraints": "1",
            "obj_type": "max",
            "c_0": "1", "c_1": "1",
            "a_0_0": "1", "a_0_1": "1", "b_0": "2", "op_0": "ge",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pb_lineaire/result_two_phase.html")

    def test_integer_gomory_route(self):
        response = self._post({
            "n_vars": "2", "n_constraints": "2",
            "obj_type": "max", "integer": "on", "int_method": "gomory",
            "c_0": "5", "c_1": "4",
            "a_0_0": "6", "a_0_1": "4", "b_0": "24", "op_0": "le",
            "a_1_0": "1", "a_1_1": "2", "b_1": "6", "op_1": "le",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pb_lineaire/result_gomory.html")
        self.assertEqual(response.context["result"]["optimal_value"], "20")

    def test_integer_bb_route(self):
        response = self._post({
            "n_vars": "2", "n_constraints": "2",
            "obj_type": "max", "integer": "on", "int_method": "bb",
            "c_0": "5", "c_1": "4",
            "a_0_0": "6", "a_0_1": "4", "b_0": "24", "op_0": "le",
            "a_1_0": "1", "a_1_1": "2", "b_1": "6", "op_1": "le",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pb_lineaire/result_branch_bound.html")
        self.assertEqual(response.context["result"]["optimal_value"], "20")

    def test_integer_min_bb(self):
        # min x1 + x2  s.c.  3x1 + 2x2 >= 5, entier → Z* = 2
        response = self._post({
            "n_vars": "2", "n_constraints": "1",
            "obj_type": "min", "integer": "on", "int_method": "bb",
            "c_0": "1", "c_1": "1",
            "a_0_0": "3", "a_0_1": "2", "b_0": "5", "op_0": "ge",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["result"]["optimal_value"], "2")

    def test_invalid_input_shows_error(self):
        response = self._post({
            "n_vars": "abc", "n_constraints": "2",
            "obj_type": "max",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pb_lineaire/index.html")
        self.assertIn("Nombre de variables", response.context["error"])

    BASE = {
        "n_vars": "2", "n_constraints": "2", "obj_type": "max",
        "c_0": "3", "c_1": "2",
        "a_0_0": "1", "a_0_1": "1", "b_0": "4", "op_0": "le",
        "a_1_0": "1", "a_1_1": "0", "b_1": "2", "op_1": "le",
    }

    def test_bad_numbers_are_rejected_with_a_readable_message(self):
        for bad in ("abc", "1/0", "nan", "inf", "1e200000", "1/2/3"):
            response = self._post({**self.BASE, "c_0": bad})
            self.assertTemplateUsed(response, "pb_lineaire/index.html")
            self.assertIn("Coefficient c1", response.context["error"])
            self.assertNotIn("Fraction", response.context["error"])

    def test_size_limits_are_enforced(self):
        for key in ("n_vars", "n_constraints"):
            for bad in ("0", "-1", "31", "400"):
                response = self._post({**self.BASE, key: bad})
                self.assertTemplateUsed(response, "pb_lineaire/index.html")
                self.assertIn("hors limites", response.context["error"])

    def test_fraction_and_comma_input(self):
        # max x1/2 + 2,5·x2  s.c.  x1 + x2 <= 4, x1 <= 2 → Z* = 10 en (0, 4)
        response = self._post({**self.BASE, "c_0": "1/2", "c_1": "2,5"})
        self.assertEqual(response.context["result"]["optimal_value"], "10")

    def test_single_variable_single_constraint(self):
        response = self._post({
            "n_vars": "1", "n_constraints": "1", "obj_type": "max",
            "c_0": "3", "a_0_0": "2", "b_0": "5", "op_0": "le",
        })
        self.assertEqual(response.context["result"]["optimal_value"], "15/2")

    def test_problem_recap_formats_signs(self):
        response = self._post({**self.BASE, "c_1": "-2", "a_0_1": "-1/3"})
        self.assertEqual(response.context["objective_tex"], "\\max Z = 3x_{1} - 2x_{2}")
        self.assertEqual(response.context["constraints_tex"][0],
                         "x_{1} - \\frac{1}{3}x_{2} \\le 4")
        self.assertIsNone(response.context["std_form"])

    def test_standard_form_shown_when_problem_is_transformed(self):
        # min x1 + x2  s.c.  x1 + x2 >= 2, x1 = 1
        response = self._post({
            "n_vars": "2", "n_constraints": "2", "obj_type": "min",
            "c_0": "1", "c_1": "1",
            "a_0_0": "1", "a_0_1": "1", "b_0": "2", "op_0": "ge",
            "a_1_0": "1", "a_1_1": "0", "b_1": "1", "op_1": "eq",
        })
        std = response.context["std_form"]
        self.assertEqual(std["objective"], "\\max Z' = -Z = -x_{1} - x_{2}")
        self.assertEqual([r["tex"] for r in std["rows"]],
                         ["-x_{1} - x_{2} \\le -2", "x_{1} \\le 1", "-x_{1} \\le -1"])
        self.assertEqual(response.context["result"]["optimal_value"], "2")
        self.assertContains(response, "Forme standard résolue")

    def test_gomory_falls_back_to_branch_and_bound(self):
        # Instance où 15 coupes ne suffisent pas ; optimum entier Z* = 21
        response = self._post({
            "n_vars": "2", "n_constraints": "2", "obj_type": "max",
            "integer": "on", "int_method": "gomory",
            **GOMORY_HARD,
        })
        self.assertTemplateUsed(response, "pb_lineaire/result_gomory.html")
        self.assertEqual(response.context["result"]["status"], "max_cuts")
        self.assertEqual(response.context["fallback"]["status"], "optimal")
        self.assertEqual(response.context["fallback"]["optimal_value"], GOMORY_HARD_OPT)

    def test_large_integer_problem_stays_small(self):
        # 30 × 30 : la page doit rester raisonnable (affichage allégé)
        data = {"n_vars": "30", "n_constraints": "30", "obj_type": "max",
                "integer": "on", "int_method": "bb"}
        for i in range(30):
            data[f"c_{i}"] = str(1 + (7 * i) % 10)
            data[f"b_{i}"] = str(20 + (37 * i) % 100)
            for j in range(30):
                data[f"a_{i}_{j}"] = str(1 + (i * 31 + j * 17) % 20)
        response = self._post(data)
        self.assertEqual(response.status_code, 200)
        self.assertLess(len(response.content), 15_000_000)
