#!/usr/bin/env python3
"""A small, explainable ELIZA-style psychotherapist chatbot.

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
            "apology",
            r"\b(?:sorry|apolog(?:y|ize))\b(?:\s+(.*))?",
            ("Please do not apologize.", "Apologies are not necessary. What feelings are you having?"),
            90,
        ),
        (
            "remember",
            r"\bi remember (.*)",
            ("Do you often think of {0}?", "What else do you recollect about {0}?", "Why do you remember {0} just now?"),
            85,
        ),
        (
            "dream",
            r"\bi dream(?:ed|t)? (.*)",
            ("What does dreaming about {0} suggest to you?", "Have you ever fantasized about {0} while awake?"),
            80,
        ),
        (
            "family",
            r"\b(?:mother|father|parent|sister|brother|family)\b(?:.*)",
            ("Tell me more about your family.", "How do you feel about your family?", "Who else in your family comes to mind?"),
            75,
        ),
        (
            "because",
            r"\bbecause (.*)",
            ("Is that the real reason?", "What other reasons might there be?", "Does that reason explain anything else?"),
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
            ("Why do you need {0}?", "Would getting {0} really help you?", "Are you sure you need {0}?"),
            82,
        ),
        (
            "i_am",
            r"\bi am (.*)",
            ("How long have you been {0}?", "How do you feel about being {0}?", "Why do you tell me you are {0}?"),
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
            ("You seem quite certain.", "I see. Please go on."),
            45,
        ),
        (
            "no",
            r"\b(?:no|nope|never)\b",
            ("Why not?", "Are you saying no just to be negative?", "You are being a little negative."),
            45,
        ),
        (
            "question",
            r"\b(?:what|how|when|where|who) (.*)",
            ("What do you think?", "Why do you ask?", "What answer would please you most?"),
            30,
        ),
        (
            "default",
            r"(.*)",
            ("Please tell me more.", "Can you elaborate on that?", "How does that make you feel?", "goto:family"),
            0,
        ),
    ]
    rules = [Rule(name, re.compile(pattern), responses, priority) for name, pattern, responses, priority in raw_rules]
    return tuple(sorted(rules, key=lambda rule: rule.priority, reverse=True))


class Eliza:
    """A deterministic-by-seed ELIZA engine with a small deferred-topic memory."""

    def __init__(self, seed: int | None = None) -> None:
        self.rules = compile_rules()
        self.by_name = {rule.name: rule for rule in self.rules}
        self.random = random.Random(seed)
        self.memory: deque[str] = deque(maxlen=5)

    def respond(self, user_input: str) -> str:
        """Return one response, prioritising a deferred topic occasionally."""
        text = normalize(user_input)
        if not text:
            return "Please say a little more."

        if self.memory and self.random.random() < 0.20:
            return self.memory.popleft()
        return self._apply_rules(text)

    def _apply_rules(self, text: str, start_rule: str | None = None) -> str:
        rules = (self.by_name[start_rule],) if start_rule else self.rules
        for rule in rules:
            match = rule.pattern.search(text)
            if not match:
                continue
            captures = tuple(reflect(group or "") for group in match.groups())
            template = self.random.choice(rule.responses)
            if template.startswith("goto:"):
                return self._apply_rules(text, template.removeprefix("goto:"))
            response = template.format(*captures)
            # Save concrete prompts for later rather than a vague fallback.
            if rule.name in {"need", "remember", "dream"} and len(self.memory) < self.memory.maxlen:
                self.memory.append(response)
            return response
        return "Please tell me more."


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
