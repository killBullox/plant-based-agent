import base64
import json
import os
import tempfile
from typing import Optional

import anthropic
import cv2
import requests
from dotenv import load_dotenv

from .models import SpielbiergReview, VideoConcept

load_dotenv()

_TOOL = {
    "name": "submit_video_review",
    "description": "Invia la revisione strutturata del video.",
    "input_schema": {
        "type": "object",
        "properties": {
            "approved": {
                "type": "boolean",
                "description": (
                    "True se il video è approvato "
                    "(realism_score >= 7 AND adherence_score >= 6)."
                ),
            },
            "realism_score": {
                "type": "integer",
                "description": (
                    "Punteggio realismo fotografico 1-10 "
                    "(1=CGI/cartone, 10=iper-realistico)."
                ),
            },
            "adherence_score": {
                "type": "integer",
                "description": (
                    "Punteggio aderenza al testo del post 1-10 "
                    "(1=nessuna aderenza, 10=perfetta)."
                ),
            },
            "issues": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Problemi specifici con riferimento al frame "
                    "(es. 'frame 3: lenticchie con texture plasticosa')."
                ),
            },
            "improved_prompt_notes": {
                "type": "string",
                "description": (
                    "Istruzioni specifiche per migliorare il prompt Runway in inglese, "
                    "formato lista separata da | "
                    "(es. \"add 'glistening real lenticchie, matte rough texture, steam' "
                    "| remove any CG sheen\")."
                ),
            },
            "verdict": {
                "type": "string",
                "description": "Verdetto sintetico in una frase.",
            },
        },
        "required": [
            "approved",
            "realism_score",
            "adherence_score",
            "issues",
            "improved_prompt_notes",
            "verdict",
        ],
    },
}


class SpielbiergAgent:
    def __init__(self):
        self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

    def review_video(
        self,
        video_url: str,
        concept: Optional[VideoConcept],
        caption: str,
        hashtags: list[str],
    ) -> SpielbiergReview:
        """Entry point. Never raises."""
        try:
            frames_b64 = self._download_and_extract_frames(video_url)
            messages = self._build_messages(frames_b64, concept, caption, hashtags)
            return self._call_claude(messages)
        except Exception as exc:
            print(f"  [Spielbierg] Errore: {exc} — approvazione automatica.")
            return SpielbiergReview(
                approved=True,
                realism_score=0,
                adherence_score=0,
                issues=[],
                improved_prompt_notes="",
                verdict="Auto-approvato per errore tecnico.",
            )

    def _download_and_extract_frames(self, video_url: str) -> list[str]:
        """Download video, extract 6 equidistant frames, return as base64 JPEG strings."""
        response = requests.get(video_url, timeout=60, stream=True)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = tmp.name
            for chunk in response.iter_content(chunk_size=8192):
                tmp.write(chunk)

        try:
            cap = cv2.VideoCapture(tmp_path)
            if not cap.isOpened():
                raise RuntimeError(f"Impossibile aprire il video: {tmp_path}")

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames <= 0:
                raise RuntimeError("Video senza frame.")

            n_frames = 6
            indices = [int(total_frames * i / n_frames) for i in range(n_frames)]

            frames_b64: list[str] = []
            for idx in indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if not ret:
                    continue

                # Resize to 720px width maintaining aspect ratio
                h, w = frame.shape[:2]
                target_w = 720
                target_h = int(h * target_w / w)
                frame = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)

                # Encode as JPEG quality 85
                ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if not ret:
                    continue

                frames_b64.append(base64.b64encode(buffer.tobytes()).decode("utf-8"))

            cap.release()

            if not frames_b64:
                raise RuntimeError("Nessun frame estratto dal video.")

            return frames_b64

        finally:
            os.unlink(tmp_path)

    def _build_messages(
        self,
        frames_b64: list[str],
        concept: Optional[VideoConcept],
        caption: str,
        hashtags: list[str],
    ) -> list[dict]:
        """Build multimodal Claude message with frames + context."""
        content: list[dict] = []

        hashtags_str = " ".join(f"#{h}" for h in hashtags) if hashtags else ""

        concept_text = ""
        if concept:
            concept_text = (
                f"\n## Video Concept\n"
                f"Titolo: {concept.title}\n"
                f"Stile: {concept.visual_style}\n"
                f"Hook: {concept.hook_description}\n"
            )
            if concept.scenes:
                scenes_lines = "\n".join(
                    f"  Scena {s.scene_number}: {s.description}"
                    for s in concept.scenes
                )
                concept_text += f"Scene:\n{scenes_lines}\n"

        context_text = (
            f"## Post Caption\n{caption}\n\n"
            f"## Hashtags\n{hashtags_str}\n"
            f"{concept_text}\n"
            f"## Frame del video (estratti uniformemente)\n"
            f"Analizza i {len(frames_b64)} frame qui sotto e valuta il video."
        )

        content.append({"type": "text", "text": context_text})

        for i, frame_b64 in enumerate(frames_b64):
            content.append({"type": "text", "text": f"Frame {i + 1}:"})
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": frame_b64,
                },
            })

        return [{"role": "user", "content": content}]

    def _call_claude(self, messages: list[dict]) -> SpielbiergReview:
        """Call claude-opus-4-6 with tool submit_video_review, tool_choice=any."""
        from .prompts import SPIELBIERG_SYSTEM_PROMPT

        response = self._client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2000,
            system=SPIELBIERG_SYSTEM_PROMPT,
            tools=[_TOOL],
            tool_choice={"type": "any"},
            messages=messages,
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == "submit_video_review":
                inp = block.input
                return SpielbiergReview(
                    approved=inp["approved"],
                    realism_score=inp["realism_score"],
                    adherence_score=inp["adherence_score"],
                    issues=inp["issues"],
                    improved_prompt_notes=inp["improved_prompt_notes"],
                    verdict=inp["verdict"],
                )

        raise RuntimeError("Claude non ha chiamato submit_video_review.")
