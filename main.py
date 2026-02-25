"""
Plant Based Agent — entry point principale.
Coordina i sotto-agenti: social, calendar, booking, email.
"""

import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def main() -> None:
    print("Plant Based Agent avviato.")
    # TODO: orchestrare i sotto-agenti


if __name__ == "__main__":
    main()
