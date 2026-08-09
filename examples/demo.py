"""Run a short, reproducible ELIZA conversation without changing the chatbot."""

from pathlib import Path
import sys

# Running ``py -3 examples/demo.py`` puts ``examples/`` on sys.path, not the
# project root. Add the root solely so this standalone example can import ELIZA.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from eliza import Eliza  # noqa: E402


DEMO_INPUTS = (
    "I need my parent to understand me",
    "I am worried about work",
    "I remember my father",
    "Why can't I sleep?",
    "Can you help me?",
    "Yes",
    "I don't know what to say",
)


def main() -> None:
    # A seed makes this example repeatable. It does not alter eliza.py or
    # prevent an interactive user from receiving different valid responses.
    bot = Eliza(seed=12)
    print("ELIZA demo (a reproducible rule-matching conversation)\n")
    for user_input in DEMO_INPUTS:
        print(f"You:   {user_input}")
        print(f"ELIZA: {bot.respond(user_input)}\n")
    print("Demo complete. Run `py -3 eliza.py` to chat interactively.")


if __name__ == "__main__":
    main()
