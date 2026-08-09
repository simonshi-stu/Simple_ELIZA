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
            "Family relationships can carry a lot. What feels most important about this for you?",
            "It sounds as though this relationship matters to you. How has it been affecting you?",
            "Would you like to tell me more about what happens with your family?",
        })

    def test_empty_input_has_a_safe_response(self):
        self.assertEqual(self.bot.respond("  ?! "), "Please say a little more.")

    def test_abuse_overrides_a_family_rule(self):
        reply = self.bot.respond("My mother abuses me")
        self.assertIn("You do not deserve abuse or violence", reply)
        self.assertIn("immediate danger", reply)

    def test_crisis_overrides_saved_memory(self):
        self.bot.memory.append("Earlier, you mentioned something else.")
        reply = self.bot.respond("I want to hurt myself")
        self.assertIn("Your safety matters more than this chat", reply)

    def test_help_request_offers_a_next_step(self):
        reply = self.bot.respond("What can I do about this?")
        self.assertTrue("small step" in reply or "options" in reply)


if __name__ == "__main__":
    unittest.main()
