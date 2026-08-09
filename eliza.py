#!/usr/bin/env python3
"""A small, explainable ELIZA-style supportive conversation chatbot.

The program deliberately uses only Python's standard library.  Its goal is not
to understand language, but to make its rule-based decisions visible and easy
to extend.
"""

from __future__ import annotations

import random
import re
from collections import deque
from dataclasses import dataclass
from typing import Pattern


REFLECTIONS = {
    "am": "are",
    "are": "am",
    "i": "you",
    "i'd": "you would",
    "i'll": "you will",
    "i've": "you have",
    "me": "you",
    "mine": "yours",
    "my": "your",
    "myself": "yourself",
    "you": "I",
    "you'd": "I would",
    "you'll": "I will",
    "you've": "I have",
    "your": "my",
    "yours": "mine",
    "yourself": "myself",
    "was": "were",
    "were": "was",
}


@dataclass(frozen=True)
class Rule:
    """One ordered language rule.

    ``pattern`` has normal regular-expression syntax.  Each response can use
    ``{0}``, ``{1}``, ... to insert a captured group after pronoun reflection.
    A response beginning with ``goto:`` delegates to another rule by name.
    """

    name: str
    pattern: Pattern[str]
    responses: tuple[str, ...]
    priority: int = 0


def normalize(text: str) -> str:
    """Lowercase input and remove punctuation that adds no rule information."""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9'\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def reflect(text: str) -> str:
    """Switch first/second-person words without accidental partial replacements."""
    return re.sub(
        r"\b[\w']+\b",
        lambda match: REFLECTIONS.get(match.group(0).lower(), match.group(0)),
        text.lower(),
    )


def compile_rules() -> tuple[Rule, ...]:
    """Build the rule base in one place so it is simple to read and extend."""
    raw_rules = [
        (
            "crisis",
            r"\b(?:suicide|suicidal|kill myself|end my life|self harm|hurt myself)\b",
            (
                "I'm really sorry you're carrying this. Your safety matters more than this chat. "
                "Are you in immediate danger or thinking of acting on these thoughts right now? "
                "Please contact local emergency services or a crisis line now, or reach out to someone you trust who can be with you.",
            ),
            110,
        ),
        (
            "abuse_or_violence",
            r"\b(?:abuse[ds]?|abusive|assault(?:ed)?|hit me|beat me|violence|unsafe at home)\b",
            (
                "I'm really sorry you're experiencing this. You do not deserve abuse or violence, and you deserve to be safe. "
                "Are you in immediate danger right now? If so, please contact local emergency services or a trusted person who can help you get somewhere safe.",
            ),
            105,
        ),
        (
            "apology",
            r"\b(?:sorry|apolog(?:y|ize))\b(?:\s+(.*))?",
            (
                "You do not need to apologize for bringing that up. I'm glad you said it. What is this like for you?",
                "No apology is needed here. It sounds important; would you like to tell me a little more?",
            ),
            90,
        ),
        (
            "remember",
            r"\bi remember (.*)",
            (
                "That memory seems meaningful. What feelings come up when you remember {0}?",
                "What else do you recollect about {0}?",
                "Why do you think {0} came to mind just now?",
            ),
            85,
        ),
        (
            "dream",
            r"\bi dream(?:ed|t)? (.*)",
            (
                "That dream sounds vivid. What does dreaming about {0} bring up for you?",
                "Have you ever thought about {0} while awake?",
            ),
            80,
        ),
        (
            "emotion",
            r"\b(?:sad|lonely|anxious|anxiety|afraid|scared|overwhelmed|stressed|upset|hurt|angry|exhausted|hopeless)\b(?:.*)",
            (
                "That sounds really difficult. You do not have to carry it alone. What feels hardest right now?",
                "I'm sorry that this has been weighing on you. Would it help to describe what is making you feel this way?",
                "It makes sense to want support when things feel this heavy. What would feel most helpful in this moment?",
            ),
            78,
        ),
        (
            "family",
            r"\b(?:mother|father|parent|sister|brother|family)\b(?:.*)",
            (
                "Family relationships can carry a lot. What feels most important about this for you?",
                "It sounds as though this relationship matters to you. How has it been affecting you?",
                "Would you like to tell me more about what happens with your family?",
            ),
            75,
        ),
        (
            "help_request",
            r"\b(?:what (?:can|should) i do|how can i cope|help me)\b(?:.*)",
            (
                "We can take this one small step at a time. What feels most urgent, and is there one trusted person or practical step that could support you today?",
                "I cannot make the decision for you, but we can think it through together. What options do you see, even if none feels ideal?",
            ),
            73,
        ),
        (
            "because",
            r"\bbecause (.*)",
            ("That sounds like an important reason. What else might be contributing?", "Does that reason explain anything else for you?"),
            70,
        ),
        (
            "why_dont_you",
            r"\bwhy don't you (.*)",
            ("Do you really think I do not {0}?", "Perhaps eventually I will {0}.", "Do you really want me to {0}?"),
            65,
        ),
        (
            "why_cant_i",
            r"\bwhy can't i (.*)",
            ("Do you think you should be able to {0}?", "If you could {0}, what would you do?"),
            65,
        ),
        (
            "need",
            r"\bi need (.*)",
            (
                "That sounds important to you. What would change for you if you had {0}?",
                "Wanting {0} makes sense. What kind of support would help you move toward it?",
                "What do you think you need most about {0}?",
            ),
            82,
        ),
        (
            "i_am",
            r"\bi am (.*)",
            ("How long have you been {0}?", "How do you feel about being {0}?", "Thank you for telling me. What has being {0} been like for you?"),
            55,
        ),
        (
            "you_are",
            r"\byou are (.*)",
            ("What makes you think I am {0}?", "Does it please you to believe I am {0}?"),
            55,
        ),
        (
            "can_you",
            r"\bcan you (.*)",
            ("What makes you think I cannot {0}?", "If I could {0}, then what?"),
            50,
        ),
        (
            "yes",
            r"\b(?:yes|yeah|certainly|indeed)\b",
            ("Thank you for telling me. Please go on when you are ready.", "I hear that. What feels important to say next?"),
            45,
        ),
        (
            "no",
            r"\b(?:no|nope|never)\b",
            ("That is okay. What makes that feel like a no for you?", "I hear your hesitation. What is behind it?"),
            45,
        ),
        (
            "question",
            r"\b(?:what|how|when|where|who) (.*)",
            (
                "That is a thoughtful question. What answer feels most true to you so far?",
                "What would feel like a helpful answer right now?",
                "I may not have the whole answer, but we can explore it together. What makes you ask?",
            ),
            30,
        ),
        (
            "default",
            r"(.*)",
            (
                "I'm listening. Please tell me more.",
                "Take your time. Can you elaborate on that?",
                "That sounds worth exploring. How does it make you feel?",
                "goto:family",
            ),
            0,
        ),
    ]
    rules = [Rule(name, re.compile(pattern), responses, priority) for name, pattern, responses, priority in raw_rules]
    return tuple(sorted(rules, key=lambda rule: rule.priority, reverse=True))


class Eliza:
    """A deterministic-by-seed ELIZA engine with safety-first rule routing."""

    def __init__(self, seed: int | None = None) -> None:
        self.rules = compile_rules()
        self.by_name = {rule.name: rule for rule in self.rules}
        self.random = random.Random(seed)
        self.memory: deque[str] = deque(maxlen=5)
        self.turns = 0

    def respond(self, user_input: str) -> str:
        """Return one response, prioritising a deferred topic occasionally."""
        text = normalize(user_input)
        if not text:
            return "Please say a little more."

        # Safety is checked before memory, so an earlier topic can never hide a
        # new message about abuse or self-harm.
        for rule in self.rules:
            if rule.priority < 100:
                break
            match = rule.pattern.search(text)
            if match:
                self.turns += 1
                return self._respond_to_match(rule, match, text)

        self.turns += 1
        if self.turns > 2 and self.memory and self.random.random() < 0.15:
            return self.memory.popleft()
        return self._apply_rules(text)

    def _apply_rules(self, text: str, start_rule: str | None = None) -> str:
        rules = (self.by_name[start_rule],) if start_rule else self.rules
        for rule in rules:
            match = rule.pattern.search(text)
            if not match:
                continue
            return self._respond_to_match(rule, match, text)
        return "Please tell me more."

    def _respond_to_match(self, rule: Rule, match: re.Match[str], text: str) -> str:
        """Reflect captures, assemble one reply, and optionally retain a topic."""
        captures = tuple(reflect(group or "") for group in match.groups())
        template = self.random.choice(rule.responses)
        if template.startswith("goto:"):
            return self._apply_rules(text, template.removeprefix("goto:"))
        response = template.format(*captures)

        # Retain a fresh, non-repetitive follow-up rather than replaying the
        # response verbatim. Safety messages are intentionally never retained.
        if rule.name in {"need", "remember", "dream"} and captures and captures[0]:
            topic = captures[0]
            self.memory.append(f"Earlier, you mentioned {topic}. Does that still feel important to you?")
        return response


def main() -> None:
    bot = Eliza()
    print("ELIZA: Hello. I am ELIZA. How are you feeling today?")
    while True:
        try:
            user_input = input("You: ")
        except (EOFError, KeyboardInterrupt):
            print("\nELIZA: Goodbye. Take care.")
            return
        if normalize(user_input) in {"quit", "exit", "bye", "goodbye"}:
            print("ELIZA: Goodbye. Take care.")
            return
        print(f"ELIZA: {bot.respond(user_input)}")


if __name__ == "__main__":
    main()
