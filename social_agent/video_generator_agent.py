import os
import time
from typing import Optional

import requests
from dotenv import load_dotenv

from .models import VideoConcept, VideoGenerationResult

load_dotenv()

RUNWAY_API_BASE = "https://api.dev.runwayml.com/v1"
RUNWAY_VERSION = "2024-11-06"

# Ratio per platform (gen4.5 supporta solo questi due valori)
_RATIO_9_16 = "720:1280"   # Instagram Reels (portrait)
_RATIO_16_9 = "1280:720"   # Facebook Video (landscape)


class RunwayAPIError(Exception):
    """Raised when Runway returns a FAILED task status."""


class VideoGeneratorAgent:
    def __init__(self):
        api_secret = os.getenv("RUNWAYML_API_SECRET", "")
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_secret}",
            "X-Runway-Version": RUNWAY_VERSION,
            "Content-Type": "application/json",
        })

    def generate(
        self,
        concept: VideoConcept,
        platform: str,
        additional_notes: Optional[str] = None,
    ) -> VideoGenerationResult:
        """
        Entry point. Always returns a VideoGenerationResult — never raises.
        Graceful degradation: any failure → status="failed".
        additional_notes: improvement instructions from Spielbierg for regeneration.
        """
        try:
            ratio = _RATIO_9_16 if platform.lower() == "instagram" else _RATIO_16_9
            prompt = self._build_runway_prompt(concept, additional_notes)

            print(f"\n  [Runway] Avvio generazione video con Gen-4.5...")
            task_id = self._create_task(prompt, ratio, duration=10)
            video_url = self._poll_task(task_id)

            print(f"\n  [Runway] Video generato: {video_url}")
            return VideoGenerationResult(
                status="succeeded",
                video_url=video_url,
                task_id=task_id,
                platform_format=concept.platform_format,
                prompt_used=prompt,
            )

        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else "?"
            error_msg = f"HTTP {status_code}: {exc}"
            print(f"\n  [Runway] Errore HTTP: {error_msg}")
            return VideoGenerationResult(status="failed", error=error_msg)

        except RunwayAPIError as exc:
            error_msg = str(exc)
            print(f"\n  [Runway] Generazione fallita: {error_msg}")
            return VideoGenerationResult(status="failed", error=error_msg)

        except TimeoutError as exc:
            error_msg = str(exc)
            print(f"\n  [Runway] Timeout: {error_msg}")
            return VideoGenerationResult(status="failed", error=error_msg)

        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            print(f"\n  [Runway] Errore inatteso: {error_msg}")
            return VideoGenerationResult(status="failed", error=error_msg)

    def _build_runway_prompt(
        self,
        concept: VideoConcept,
        additional_notes: Optional[str] = None,
    ) -> str:
        """
        Build a ≤1000-char photorealistic food video prompt.
        Always photorealistic — no CGI, no animation language.
        Priority: additional_notes (Spielbierg) | base keywords | visual_style | hook | scenes | palette | cinematography
        """
        parts: list[str] = []

        # Spielbierg improvement notes go first for maximum weight
        if additional_notes:
            parts.append(additional_notes.strip())

        parts.append("cinematic food video, photorealistic, 4K, professional food photography")

        # Visual style — strip any residual CGI language
        if concept.visual_style:
            style = concept.visual_style
            for bad in ("CGI", "cgi", "animation", "3D render", "particle simulation"):
                style = style.replace(bad, "")
            style = style.strip(" ,|—-")
            if style:
                parts.append(style)

        # Hook — opening shot
        if concept.hook_description:
            parts.append(concept.hook_description)

        # First two scenes with visual details and camera movement
        for scene in concept.scenes[:2]:
            desc = scene.description
            if scene.visual_details:
                desc += f", {scene.visual_details}"
            if scene.camera_movement:
                desc += f", {scene.camera_movement}"
            parts.append(desc)

        # Color palette
        if concept.color_palette:
            parts.append("colors: " + ", ".join(concept.color_palette))

        # Cinematography notes (first sentence)
        if concept.cinematography_notes:
            first = concept.cinematography_notes.split(".")[0].strip()
            if first:
                parts.append(first)

        # Closing food video keywords
        parts.append("appetizing, warm natural light, slow motion details, real hands cooking")

        prompt = " | ".join(parts)
        return prompt[:1000]

    def _create_task(self, prompt: str, ratio: str, duration: int) -> str:
        """POST to Runway text_to_video endpoint, return task ID."""
        response = self._session.post(
            f"{RUNWAY_API_BASE}/text_to_video",
            json={
                "promptText": prompt,
                "model": "gen4.5",
                "duration": duration,
                "ratio": ratio,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["id"]

    def _poll_task(self, task_id: str) -> str:
        """
        Poll the task until SUCCEEDED, FAILED, or 420s timeout.
        Returns the video URL on success.
        """
        deadline = time.monotonic() + 420
        poll_interval = 5

        while True:
            elapsed = int(time.monotonic() - (deadline - 420))
            print(f"  [Runway] Generazione video in corso... ({elapsed}s)", end="\r")

            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Runway task {task_id} non completata entro 420 secondi."
                )

            time.sleep(poll_interval)

            response = self._session.get(f"{RUNWAY_API_BASE}/tasks/{task_id}")
            response.raise_for_status()
            data = response.json()
            status = data.get("status", "")

            if status == "SUCCEEDED":
                output = data.get("output", [])
                if not output:
                    raise RunwayAPIError(f"Task {task_id} SUCCEEDED ma output vuoto.")
                return output[0]

            if status == "FAILED":
                failure_reason = data.get("failure", "unknown reason")
                raise RunwayAPIError(
                    f"Task {task_id} fallita: {failure_reason}"
                )

            # PENDING or RUNNING — continue polling
