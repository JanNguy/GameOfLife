import unittest

from game.scenario_orchestrator import generate_questions_for_context


class ScenarioOrchestratorTests(unittest.TestCase):
    def test_generate_questions_for_context_returns_binary_questions(self):
        questions = generate_questions_for_context(
            "Il y a plus d'eau, les zones basses sont inondées, les habitants doivent décider de rester ou de migrer.",
            max_questions=3,
        )

        self.assertTrue(len(questions) > 0)
        for question in questions:
            self.assertIn("question", question)
            self.assertIn("domain", question)
            self.assertIn("type", question)
            self.assertEqual(question["type"], "binary")
            self.assertIn("id", question)


if __name__ == "__main__":
    unittest.main()
