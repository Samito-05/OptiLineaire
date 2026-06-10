from fractions import Fraction

from django.test import TestCase
from django.urls import reverse

from .simplex import run_simplex
from .simplex_two_phase import run_two_phase
from .gomory import run_gomory
from .branch_bound import run_branch_and_bound


class SimplexTests(TestCase):
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


class TwoPhaseTests(TestCase):
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


class GomoryTests(TestCase):
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


class BranchAndBoundTests(TestCase):
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


class SolveViewTests(TestCase):
    def _post(self, data):
        return self.client.post(reverse("pb_lineaire:solve"), data)

    def test_get_redirects_to_index(self):
        response = self.client.get(reverse("pb_lineaire:solve"))
        self.assertEqual(response.status_code, 302)

    def test_simplex_max(self):
        response = self._post({
            "n_vars": "2", "n_constraints": "2",
            "obj_type": "max", "method": "simplex",
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
            "obj_type": "min", "method": "two_phase",
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
            "obj_type": "max", "method": "auto",
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
            "obj_type": "max", "method": "auto",
            "c_0": "1", "c_1": "1",
            "a_0_0": "1", "a_0_1": "1", "b_0": "4", "op_0": "le",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pb_lineaire/result.html")

    def test_auto_picks_two_phase_when_not_admissible(self):
        response = self._post({
            "n_vars": "2", "n_constraints": "1",
            "obj_type": "max", "method": "auto",
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
            "obj_type": "max", "method": "simplex",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("error", response.context)
