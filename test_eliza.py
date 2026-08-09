import unittest

from eliza import Eliza, normalize, reflect


class ElizaTests(unittest.TestCase):
    def setUp(self):
        self.bot = Eliza(seed=7)

    def test_normalize_keeps_contractions(self):
        self.assertEqual(normalize(" Why can't I sleep?! "), "why can't i sleep")

    def test_reflection_swaps_whole_words(self):
        self.assertEqual(reflect("I told you about my cat"), "you told I about your cat")
        self.assertEqual(reflect("mine"), "yours")

    def test_priority_beats_default(self):
        reply = self.bot.respond("I need my family to understand me")
        self.assertIn("your family to understand you", reply)

    def test_family_rule_matches_embedded_word(self):
        reply = self.bot.respond("My mother worries me")
        self.assertIn(reply, {
            "Tell me more about your family.",
            "How do you feel about your family?",
            "Who else in your family comes to mind?",
        })

    def test_empty_input_has_a_safe_response(self):
        self.assertEqual(self.bot.respond("  ?! "), "Please say a little more.")


if __name__ == "__main__":
    unittest.main()
