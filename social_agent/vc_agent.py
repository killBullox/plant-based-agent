import os

import anthropic
from dotenv import load_dotenv

from .models import VideoConcept
from .prompts import VC_SYSTEM_PROMPT

load_dotenv()

# ── VC tool definition ─────────────────────────────────────────────────────────

VC_TOOLS: list[dict] = [
    {
        "name": "submit_video_concept",
        "description": (
            "Invia il concept video completo con storyboard, stile visivo e note di produzione CGI. "
            "Usa questo tool per restituire il video concept strutturato."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Titolo del video concept (breve e evocativo).",
                },
                "total_duration_seconds": {
                    "type": "integer",
                    "description": "Durata totale del video in secondi.",
                },
                "visual_style": {
                    "type": "string",
                    "description": "Descrizione dello stile visivo generale (CGI, color grading, atmosfera).",
                },
                "platform_format": {
                    "type": "string",
                    "description": "Formato piattaforma, es. 'Reels 9:16 30s', 'Facebook 16:9 45s'.",
                },
                "hook_description": {
                    "type": "string",
                    "description": "Descrizione dei primi 3 secondi — l'hook che deve catturare immediatamente.",
                },
                "scenes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "scene_number": {"type": "integer"},
                            "description": {"type": "string"},
                            "duration_seconds": {"type": "integer"},
                            "camera_movement": {"type": "string"},
                            "text_overlay": {"type": "string"},
                            "cgi_elements": {"type": "string"},
                        },
                        "required": [
                            "scene_number",
                            "description",
                            "duration_seconds",
                            "camera_movement",
                        ],
                    },
                    "description": "Lista delle scene del video in ordine cronologico.",
                },
                "music_mood": {
                    "type": "string",
                    "description": "Mood musicale consigliato (genere, tempo, atmosfera emotiva).",
                },
                "color_palette": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista di 3-5 colori dominanti in formato descrittivo o hex.",
                },
                "cgi_notes": {
                    "type": "string",
                    "description": "Note tecniche CGI: effetti speciali, simulazioni fisiche, particle systems.",
                },
                "production_notes": {
                    "type": "string",
                    "description": "Note di produzione generali per il team di animazione.",
                },
            },
            "required": [
                "title",
                "total_duration_seconds",
                "visual_style",
                "platform_format",
                "hook_description",
                "scenes",
                "music_mood",
                "color_palette",
                "cgi_notes",
                "production_notes",
            ],
        },
    }
]


class VCAgent:
    """Video Creator — ex Pixar, crea concept video CGI per contenuti social plant-based."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

    def create_concept(
        self,
        platform: str,
        caption: str,
        content_theme: str,
    ) -> VideoConcept:
        """
        Genera un concept video CGI per accompagnare il post social.

        Args:
            platform: "instagram" o "facebook"
            caption: testo del post per cui creare il video
            content_theme: tema principale del contenuto (es. "ricetta bowl", "consigli proteici")

        Returns:
            VideoConcept con storyboard completo e note di produzione CGI
        """
        platform_hint = (
            "Reels verticale 9:16, 15-30 secondi, hook nei primi 3s"
            if platform == "instagram"
            else "Video 16:9 oppure 1:1, 30-60 secondi, più narrativo"
        )

        user_message = f"""Crea un concept video CGI per questo contenuto {platform.upper()}.

## Tema del contenuto
{content_theme}

## Caption del post
{caption}

## Formato suggerito
{platform_hint}

Crea un concept video che renda questo contenuto visivamente irresistibile. \
Usa il tuo stile CGI tipico: ingredienti che danzano, lighting cinematografico, pacing Reels/TikTok.

Invia il concept usando il tool submit_video_concept."""

        response = self.client.messages.create(
            model="claude-opus-4-6",
            max_tokens=8000,
            thinking={"type": "adaptive", "budget_tokens": 4000},
            system=VC_SYSTEM_PROMPT,
            tools=VC_TOOLS,
            tool_choice={"type": "tool", "name": "submit_video_concept"},
            messages=[{"role": "user", "content": user_message}],
        )

        for block in response.content:
            if hasattr(block, "type") and block.type == "tool_use":
                return VideoConcept(**block.input)

        raise ValueError("VCAgent: nessun tool_use trovato nella risposta")
