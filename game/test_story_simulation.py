import unittest

from game.decision_engine import simulate_story


class StorySimulationTests(unittest.TestCase):
    def test_market_crash_produces_ranked_agent_stories(self):
        agents = [
            {
                "agent_id": "investor",
                "age": 40,
                "capital_gain_mean": 5000,
                "income_rate": 0.8,
                "education": "Masters",
                "occupation": "Prof-specialty",
                "sample_size": 100,
            },
            {
                "agent_id": "worker",
                "age": 24,
                "capital_gain_mean": 0,
                "income_rate": 0.1,
                "education": "HS-grad",
                "occupation": "Other-service",
                "sample_size": 10,
            },
        ]
        questions = [{"id": "investment", "type": "binary"}, {"id": "employment", "type": "binary"}]

        story = simulate_story(agents, "crash boursier mondial", questions)

        self.assertEqual(story.scenario_kind, "market_crash")
        self.assertEqual(len(story.chapters), 3)
        self.assertEqual(len(story.outcomes), 2)
        self.assertEqual(story.ranking[0].agent_id, "investor")
        self.assertTrue(story.ranking[0].timeline)

    def test_apocalypse_can_eliminate_vulnerable_agents(self):
        agents = [
            {
                "agent_id": "vulnerable",
                "age": 82,
                "capital_gain_mean": 0,
                "income_rate": 0,
                "education": "HS-grad",
                "occupation": "Other-service",
                "sample_size": 5,
            },
            {
                "agent_id": "prepared",
                "age": 38,
                "capital_gain_mean": 6000,
                "income_rate": 0.9,
                "education": "Masters",
                "occupation": "Prof-specialty",
                "sample_size": 100,
            },
        ]
        questions = [{"id": "investment", "type": "binary"}, {"id": "employment", "type": "binary"}]

        story = simulate_story(agents, "fin du monde après une catastrophe nucléaire", questions)

        self.assertEqual(story.scenario_kind, "apocalypse")
        self.assertFalse(next(outcome for outcome in story.outcomes if outcome.agent_id == "vulnerable").survived)
        self.assertTrue(next(outcome for outcome in story.outcomes if outcome.agent_id == "prepared").survived)


if __name__ == "__main__":
    unittest.main()