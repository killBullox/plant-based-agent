import os

import anthropic
from dotenv import load_dotenv

from .models import ContentReview
from .prompts import SMCC_SYSTEM_PROMPT

load_dotenv()

# ── SMCC tool definition ───────────────────────────────────────────────────────

SMCC_TOOLS: list[dict] = [
    {
        "name": "submit_review",
        "description": (
            "Invia la revisione completa del contenuto social. "
            "Usa questo tool per restituire la caption revisionata, gli hashtag ottimizzati "
            "e le note di analisi engagement."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "revised_caption": {
                    "type": "string",
                    "description": "Caption rivista e ottimizzata per l'engagement.",
                },
                "revised_hashtags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista di hashtag ottimizzati (senza #).",
                },
                "engagement_score": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Punteggio engagement stimato da 1 (basso) a 10 (eccellente).",
                },
                "changes_summary": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista di modifiche apportate, ognuna con breve motivazione.",
                },
                "community_fit_notes": {
                    "type": "string",
                    "description": "Note sull'allineamento con la community plant-based esistente.",
                },
                "mainstream_appeal_notes": {
                    "type": "string",
                    "description": "Note sull'appeal per chi si avvicina per la prima volta al plant-based.",
                },
                "video_alignment_notes": {
                    "type": "string",
                    "description": (
                        "Note sull'allineamento tra testo e video concept (opzionale, "
                        "solo se è stato fornito un video concept)."
                    ),
                },
            },
            "required": [
                "revised_caption",
                "revised_hashtags",
                "engagement_score",
                "changes_summary",
                "community_fit_notes",
                "mainstream_appeal_notes",
            ],
        },
    }
]


class SMCCAgent:
    """Social Media Content Checker — rivede contenuti per massimizzare engagement."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

    def review(
        self,
        platform: str,
        caption: str,
        hashtags: list[str] | None = None,
        video_concept: str | None = None,
    ) -> ContentReview:
        """
        Rivede caption e hashtag per una piattaforma specifica.

        Args:
            platform: "instagram" o "facebook"
            caption: testo del post da rivedere
            hashtags: lista di hashtag proposti (senza #)
            video_concept: descrizione testuale del video concept VC (opzionale)

        Returns:
            ContentReview con caption e hashtag revisionati + note di analisi
        """
        hashtags = hashtags or []
        hashtag_str = " ".join(f"#{tag.lstrip('#')}" for tag in hashtags) if hashtags else "(nessun hashtag)"

        user_message = f"""Rivedi questo contenuto per {platform.upper()}.

## Caption proposta
{caption}

## Hashtag proposti
{hashtag_str}
"""
        if video_concept:
            user_message += f"""
## Video concept (VC)
{video_concept}

Tieni conto dell'allineamento tra caption e video concept nella tua revisione.
"""
        else:
            user_message += "\n(Nessun video concept disponibile per questa revisione.)\n"

        user_message += "\nForma il tuo output usando il tool submit_review."

        response = self.client.messages.create(
            model="claude-opus-4-6",
            max_tokens=8000,
            thinking={"type": "adaptive", "budget_tokens": 4000},
            system=SMCC_SYSTEM_PROMPT,
            tools=SMCC_TOOLS,
            tool_choice={"type": "tool", "name": "submit_review"},
            messages=[{"role": "user", "content": user_message}],
        )

        for block in response.content:
            if hasattr(block, "type") and block.type == "tool_use":
                return ContentReview(**block.input)

        raise ValueError("SMCCAgent: nessun tool_use trovato nella risposta")
