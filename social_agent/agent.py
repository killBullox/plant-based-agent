import json
import os
from typing import Any, Optional

import anthropic
from dotenv import load_dotenv

from .meta_client import MetaClient
from .models import ContentReview, Platform, PostDraft, SpielbiergReview, VideoConcept, VideoGenerationResult
from .prompts import SYSTEM_PROMPT
from .smcc_agent import SMCCAgent
from .spielbierg_agent import SpielbiergAgent
from .vc_agent import VCAgent
from .video_generator_agent import VideoGeneratorAgent

load_dotenv()

MAX_LOOP_ITERATIONS = 20


class ApprovalDeniedError(Exception):
    """Raised when the user rejects a post draft and provides feedback."""

    def __init__(self, feedback: str):
        super().__init__(feedback)
        self.feedback = feedback


# ── Tool definitions (JSON schema for Claude) ──────────────────────────────────

TOOLS: list[dict] = [
    {
        "name": "get_recent_posts",
        "description": (
            "Recupera i post recenti da Instagram e/o Facebook per evitare duplicati "
            "e mantenere varietà nel calendario editoriale."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "platforms": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["instagram", "facebook"]},
                    "description": "Piattaforme da cui recuperare i post recenti.",
                    "default": ["instagram", "facebook"],
                },
                "limit": {
                    "type": "integer",
                    "description": "Numero massimo di post per piattaforma (default 5).",
                    "default": 5,
                },
            },
            "required": [],
        },
    },
    {
        "name": "create_video_concept_with_vc",
        "description": (
            "Chiama il Video Creator (VC) — ex animator Pixar — per generare un concept video CGI "
            "che accompagna il post. Il VC crea uno storyboard dettagliato con scene, stile visivo, "
            "lighting cinematografico e note di produzione. "
            "Chiamare SEMPRE dopo aver generato la bozza e PRIMA di review_with_smcc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "enum": ["instagram", "facebook"],
                    "description": "Piattaforma di destinazione (influenza formato e durata video).",
                },
                "caption": {
                    "type": "string",
                    "description": "Testo della bozza del post per cui creare il video.",
                },
                "content_theme": {
                    "type": "string",
                    "description": (
                        "Tema principale del contenuto, es. 'ricetta bowl con barbabietola', "
                        "'consigli proteine vegetali', 'meal prep domenicale'."
                    ),
                },
            },
            "required": ["platform", "caption", "content_theme"],
        },
    },
    {
        "name": "generate_video_with_runway",
        "description": (
            "Chiama Runway ML Gen-4.5 per generare un video reale dal concept VC. "
            "Il VideoConcept viene letto automaticamente dallo stato interno — non è necessario passarlo. "
            "Chiamare SEMPRE dopo create_video_concept_with_vc e PRIMA di review_video_with_spielbierg. "
            "Se Runway restituisce status 'failed', continuare il flusso senza video (graceful degradation). "
            "Se Spielbierg ha rifiutato un tentativo precedente, passa additional_prompt_notes con le sue note."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "enum": ["instagram", "facebook"],
                    "description": "Piattaforma di destinazione (determina il ratio del video: 9:16 o 16:9).",
                },
                "additional_prompt_notes": {
                    "type": "string",
                    "description": (
                        "Note di miglioramento da Spielbierg per il prossimo tentativo. "
                        "Usare il campo improved_prompt_notes dalla revisione precedente."
                    ),
                },
            },
            "required": ["platform"],
        },
    },
    {
        "name": "review_video_with_spielbierg",
        "description": (
            "Chiama Spielbierg per analizzare la qualità realistica e l'aderenza al post del video generato. "
            "Spielbierg estrae frame reali dal video e li analizza con Claude vision. "
            "Chiamare SEMPRE dopo generate_video_with_runway e PRIMA di review_with_smcc. "
            "Se restituisce status 'rejected', seguire le istruzioni nel campo 'instruction': "
            "richiamare generate_video_with_runway con additional_prompt_notes, poi di nuovo review_video_with_spielbierg. "
            "Max 3 tentativi totali, poi procedere con review_with_smcc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "caption": {
                    "type": "string",
                    "description": "Caption corrente del post.",
                },
                "hashtags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista di hashtag proposti (senza #).",
                    "default": [],
                },
            },
            "required": ["caption"],
        },
    },
    {
        "name": "review_with_smcc",
        "description": (
            "Chiama lo SMCC (Social Media Content Checker) per rivedere la bozza del post. "
            "Lo SMCC ottimizza caption e hashtag per l'engagement della community plant-based, "
            "bilancia autenticità di nicchia con appeal mainstream, ed elimina linguaggio 'performativo'. "
            "Il video concept (se presente nello stato) viene automaticamente incluso nella revisione. "
            "Chiamare SEMPRE dopo generate_video_with_runway e PRIMA di request_approval."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "enum": ["instagram", "facebook"],
                    "description": "Piattaforma di destinazione.",
                },
                "caption": {
                    "type": "string",
                    "description": "Testo della bozza del post da rivedere.",
                },
                "hashtags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista di hashtag proposti (senza #).",
                    "default": [],
                },
            },
            "required": ["platform", "caption"],
        },
    },
    {
        "name": "request_approval",
        "description": (
            "Mostra la bozza del post all'utente nel terminale e chiede approvazione. "
            "Chiamare SEMPRE prima di pubblicare, usando la caption e gli hashtag revisionati dall'SMCC. "
            "Restituisce 'approved' oppure lancia un errore con il feedback dell'utente."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "enum": ["instagram", "facebook"],
                    "description": "Piattaforma di destinazione del post.",
                },
                "caption": {
                    "type": "string",
                    "description": "Testo del post (caption o messaggio) — usare la versione revisionata da SMCC.",
                },
                "hashtags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista di hashtag senza # — usare la versione revisionata da SMCC.",
                    "default": [],
                },
                "image_url": {
                    "type": "string",
                    "description": "URL dell'immagine (opzionale, solo per Instagram).",
                },
            },
            "required": ["platform", "caption"],
        },
    },
    {
        "name": "publish_instagram_post",
        "description": (
            "Pubblica un post su Instagram Business. "
            "Richiede approvazione precedente tramite request_approval."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "caption": {
                    "type": "string",
                    "description": "Testo completo del post (caption + hashtag).",
                },
                "image_url": {
                    "type": "string",
                    "description": "URL pubblico dell'immagine (richiesto da Meta API).",
                },
            },
            "required": ["caption"],
        },
    },
    {
        "name": "publish_facebook_post",
        "description": (
            "Pubblica un post sulla Facebook Page. "
            "Richiede approvazione precedente tramite request_approval."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Testo completo del post.",
                },
            },
            "required": ["message"],
        },
    },
]


class SocialAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        self.meta = MetaClient()
        self._approved_draft: Optional[PostDraft] = None
        self._current_video_concept: Optional[VideoConcept] = None
        self._current_video_url: Optional[str] = None
        self._current_review: Optional[ContentReview] = None
        self._current_spielbierg_review: Optional[SpielbiergReview] = None
        self._spielbierg_attempts: int = 0

    # ── Tool handlers ──────────────────────────────────────────────────────────

    def _handle_get_recent_posts(self, platforms: list[str], limit: int = 5) -> str:
        results: list[dict] = []
        for p in platforms:
            if p == "instagram":
                posts = self.meta.instagram_get_recent_posts(limit=limit)
            else:
                posts = self.meta.facebook_get_recent_posts(limit=limit)
            for post in posts:
                results.append(post.model_dump())
        if not results:
            return json.dumps({"posts": [], "note": "Nessun post recente trovato (o errore API)."})
        return json.dumps({"posts": results})

    def _handle_create_video_concept_with_vc(
        self,
        platform: str,
        caption: str,
        content_theme: str,
    ) -> str:
        try:
            print("\n  [VC] Generazione concept video CGI in corso...")
            agent = VCAgent()
            concept = agent.create_concept(
                platform=platform,
                caption=caption,
                content_theme=content_theme,
            )
            self._current_video_concept = concept
            print(f"  [VC] Concept '{concept.title}' generato ({concept.total_duration_seconds}s).")
            return json.dumps({
                "status": "ok",
                "title": concept.title,
                "total_duration_seconds": concept.total_duration_seconds,
                "visual_style": concept.visual_style,
                "platform_format": concept.platform_format,
                "hook_description": concept.hook_description,
                "scenes_count": len(concept.scenes),
                "music_mood": concept.music_mood,
                "color_palette": concept.color_palette,
                "cgi_notes": concept.cgi_notes,
                "production_notes": concept.production_notes,
            })
        except Exception as exc:
            error_msg = f"VCAgent error: {exc}"
            print(f"  [VC] Errore: {error_msg}")
            return json.dumps({"error": error_msg})

    def _handle_generate_video_with_runway(
        self,
        platform: str,
        additional_prompt_notes: Optional[str] = None,
    ) -> str:
        if self._current_video_concept is None:
            return json.dumps({"status": "skipped", "reason": "Nessun video concept disponibile."})
        result = VideoGeneratorAgent().generate(
            self._current_video_concept,
            platform,
            additional_notes=additional_prompt_notes,
        )
        if result.status == "succeeded":
            self._current_video_url = result.video_url
            return json.dumps({
                "status": "succeeded",
                "video_url": result.video_url,
                "task_id": result.task_id,
                "platform_format": result.platform_format,
                "prompt_used": result.prompt_used,
            })
        else:
            self._current_video_url = None
            return json.dumps({
                "status": "failed",
                "error": result.error,
                "note": "Continua il flusso senza video (graceful degradation).",
            })

    def _handle_review_video_with_spielbierg(
        self,
        caption: str,
        hashtags: Optional[list[str]] = None,
    ) -> str:
        if not self._current_video_url:
            return json.dumps({"status": "skipped", "reason": "Nessun video URL disponibile."})

        self._spielbierg_attempts += 1
        print(f"\n  [Spielbierg] Analisi video (tentativo {self._spielbierg_attempts}/3)...")

        review = SpielbiergAgent().review_video(
            video_url=self._current_video_url,
            concept=self._current_video_concept,
            caption=caption,
            hashtags=hashtags or [],
        )
        self._current_spielbierg_review = review

        status = "approved" if review.approved else "rejected"
        print(
            f"  [Spielbierg] {status.upper()} — "
            f"Realism {review.realism_score}/10, Adherence {review.adherence_score}/10"
        )

        result: dict = {
            "status": status,
            "realism_score": review.realism_score,
            "adherence_score": review.adherence_score,
            "issues": review.issues,
            "improved_prompt_notes": review.improved_prompt_notes,
            "verdict": review.verdict,
        }

        if not review.approved:
            if self._spielbierg_attempts < 3:
                result["instruction"] = (
                    "Spielbierg ha rifiutato il video. Chiama generate_video_with_runway "
                    f"con additional_prompt_notes='{review.improved_prompt_notes}', "
                    "poi richiama review_video_with_spielbierg."
                )
            else:
                result["instruction"] = (
                    "3 tentativi esauriti. Procedi con review_with_smcc."
                )

        return json.dumps(result)

    def _handle_review_with_smcc(
        self,
        platform: str,
        caption: str,
        hashtags: Optional[list[str]] = None,
    ) -> str:
        try:
            print("\n  [SMCC] Revisione contenuto in corso...")
            agent = SMCCAgent()

            # Build a text summary of the video concept if available
            video_concept_text: Optional[str] = None
            if self._current_video_concept:
                vc = self._current_video_concept
                scenes_text = "\n".join(
                    f"  Scena {s.scene_number} ({s.duration_seconds}s): {s.description} "
                    f"[camera: {s.camera_movement}]"
                    + (f" — Dettagli: {s.visual_details}" if s.visual_details else "")
                    for s in vc.scenes
                )
                video_concept_text = (
                    f"Titolo: {vc.title}\n"
                    f"Formato: {vc.platform_format}\n"
                    f"Stile: {vc.visual_style}\n"
                    f"Hook: {vc.hook_description}\n"
                    f"Scene:\n{scenes_text}\n"
                    f"Musica: {vc.music_mood}\n"
                    f"Palette: {', '.join(vc.color_palette)}\n"
                    f"Cinematografia: {vc.cinematography_notes}"
                )
                if self._current_video_url:
                    video_concept_text += f"\nVideo URL (Runway): {self._current_video_url}"

            review = agent.review(
                platform=platform,
                caption=caption,
                hashtags=hashtags or [],
                video_concept=video_concept_text,
            )
            self._current_review = review
            print(f"  [SMCC] Revisione completata. Score engagement: {review.engagement_score}/10.")
            return json.dumps({
                "status": "ok",
                "revised_caption": review.revised_caption,
                "revised_hashtags": review.revised_hashtags,
                "engagement_score": review.engagement_score,
                "changes_summary": review.changes_summary,
                "community_fit_notes": review.community_fit_notes,
                "mainstream_appeal_notes": review.mainstream_appeal_notes,
                "video_alignment_notes": review.video_alignment_notes,
            })
        except Exception as exc:
            error_msg = f"SMCCAgent error: {exc}"
            print(f"  [SMCC] Errore: {error_msg}")
            return json.dumps({"error": error_msg})

    def _handle_request_approval(
        self,
        platform: str,
        caption: str,
        hashtags: Optional[list[str]] = None,
        image_url: Optional[str] = None,
    ) -> str:
        hashtags = hashtags or []
        draft = PostDraft(
            caption=caption,
            hashtags=hashtags,
            platform=Platform(platform),
            image_url=image_url,
        )

        separator = "─" * 60
        review = self._current_review
        vc = self._current_video_concept

        # ── Header ──────────────────────────────────────────────────────────────
        print(f"\n{separator}")
        score_str = f" · score engagement: {review.engagement_score}/10" if review else ""
        smcc_str = " (revisionata da SMCC" + score_str + ")" if review else ""
        print(f"  BOZZA POST — {platform.upper()}{smcc_str}")
        print(separator)
        print(draft.full_text)
        if image_url:
            print(f"\n  Immagine: {image_url}")
        if self._current_video_url:
            print(f"\n  VIDEO URL (Runway): {self._current_video_url}")

        # ── Spielbierg verdict (compact) ─────────────────────────────────────
        sp = self._current_spielbierg_review
        if sp and sp.realism_score > 0:
            sp_status = "APPROVED" if sp.approved else "REJECTED"
            print(
                f"\n  Spielbierg: {sp_status} — "
                f"Realism {sp.realism_score}/10 · Adherence {sp.adherence_score}/10 "
                f"(tentativi: {self._spielbierg_attempts})"
            )
            print(f"  Verdetto: {sp.verdict}")

        # ── SMCC notes (compact) ─────────────────────────────────────────────
        if review and review.changes_summary:
            print(f"\n  Modifiche SMCC:")
            for change in review.changes_summary:
                print(f"    • {change}")

        # ── Video concept section ─────────────────────────────────────────────
        if vc:
            print(f"\n{separator}")
            print(f"  VIDEO CONCEPT (VC) — \"{vc.title}\"")
            print(f"  Formato: {vc.platform_format}  ·  Stile: {vc.visual_style}")
            print(f"\n  Hook (0-3s): {vc.hook_description}")
            print(f"\n  Scene:")
            for scene in vc.scenes:
                overlay = f" | testo: {scene.text_overlay}" if scene.text_overlay else ""
                cgi = f" | Dettagli: {scene.visual_details}" if scene.visual_details else ""
                print(
                    f"    {scene.scene_number}. [{scene.duration_seconds}s] {scene.description}"
                    f"\n       Camera: {scene.camera_movement}{overlay}{cgi}"
                )
            print(f"\n  Musica: {vc.music_mood}")
            print(f"  Palette: {', '.join(vc.color_palette)}")
            print(f"  Cinematografia: {vc.cinematography_notes}")
            if vc.production_notes:
                print(f"  Note produzione: {vc.production_notes}")

        print(separator)

        while True:
            answer = input("\nApprovi questo post? [Y/n/feedback]: ").strip()
            if answer.lower() in ("y", "yes", "s", "si", "sì", ""):
                self._approved_draft = draft
                return json.dumps({"status": "approved", "platform": platform})
            elif answer.lower() in ("n", "no"):
                feedback = input("Inserisci il tuo feedback per migliorare il post: ").strip()
                if not feedback:
                    feedback = "Post rifiutato senza feedback specifico."
                raise ApprovalDeniedError(feedback)
            else:
                # The user typed feedback directly
                raise ApprovalDeniedError(answer)

    def _handle_publish_instagram_post(
        self,
        caption: str,
        image_url: Optional[str] = None,
    ) -> str:
        if self._approved_draft is None:
            return json.dumps({
                "success": False,
                "error": "Pubblicazione bloccata: nessuna bozza approvata. Usa prima request_approval.",
            })
        result = self.meta.instagram_publish(caption=caption, image_url=image_url)
        self._approved_draft = None
        self._current_video_concept = None
        self._current_video_url = None
        self._current_review = None
        self._current_spielbierg_review = None
        self._spielbierg_attempts = 0
        return json.dumps(result.model_dump())

    def _handle_publish_facebook_post(self, message: str) -> str:
        if self._approved_draft is None:
            return json.dumps({
                "success": False,
                "error": "Pubblicazione bloccata: nessuna bozza approvata. Usa prima request_approval.",
            })
        result = self.meta.facebook_publish(message=message)
        self._approved_draft = None
        self._current_video_concept = None
        self._current_video_url = None
        self._current_review = None
        self._current_spielbierg_review = None
        self._spielbierg_attempts = 0
        return json.dumps(result.model_dump())

    # ── Dispatcher ─────────────────────────────────────────────────────────────

    def _dispatch_tool(self, tool_name: str, tool_input: dict[str, Any]) -> dict:
        """
        Execute a tool and return a tool_result block.
        ApprovalDeniedError is converted to an is_error tool_result so Claude
        receives the feedback and can regenerate without crashing the loop.
        """
        try:
            if tool_name == "get_recent_posts":
                content = self._handle_get_recent_posts(
                    platforms=tool_input.get("platforms", ["instagram", "facebook"]),
                    limit=tool_input.get("limit", 5),
                )
            elif tool_name == "create_video_concept_with_vc":
                content = self._handle_create_video_concept_with_vc(
                    platform=tool_input["platform"],
                    caption=tool_input["caption"],
                    content_theme=tool_input["content_theme"],
                )
            elif tool_name == "generate_video_with_runway":
                content = self._handle_generate_video_with_runway(
                    platform=tool_input["platform"],
                    additional_prompt_notes=tool_input.get("additional_prompt_notes"),
                )
            elif tool_name == "review_video_with_spielbierg":
                content = self._handle_review_video_with_spielbierg(
                    caption=tool_input["caption"],
                    hashtags=tool_input.get("hashtags", []),
                )
            elif tool_name == "review_with_smcc":
                content = self._handle_review_with_smcc(
                    platform=tool_input["platform"],
                    caption=tool_input["caption"],
                    hashtags=tool_input.get("hashtags", []),
                )
            elif tool_name == "request_approval":
                content = self._handle_request_approval(
                    platform=tool_input["platform"],
                    caption=tool_input["caption"],
                    hashtags=tool_input.get("hashtags", []),
                    image_url=tool_input.get("image_url"),
                )
            elif tool_name == "publish_instagram_post":
                content = self._handle_publish_instagram_post(
                    caption=tool_input["caption"],
                    image_url=tool_input.get("image_url"),
                )
            elif tool_name == "publish_facebook_post":
                content = self._handle_publish_facebook_post(
                    message=tool_input["message"],
                )
            else:
                content = json.dumps({"error": f"Tool sconosciuto: {tool_name}"})
                return {"type": "tool_result", "content": content, "is_error": True}

            return {"type": "tool_result", "content": content, "is_error": False}

        except ApprovalDeniedError as e:
            return {
                "type": "tool_result",
                "content": json.dumps({
                    "status": "rejected",
                    "feedback": e.feedback,
                    "instruction": (
                        "L'utente ha rifiutato la bozza. Incorpora il feedback e genera "
                        "una nuova bozza, poi esegui nuovamente l'intero flusso: "
                        "create_video_concept_with_vc → generate_video_with_runway → "
                        "review_with_smcc → request_approval."
                    ),
                }),
                "is_error": True,
            }

    # ── Agentic loop ───────────────────────────────────────────────────────────

    def run(self, user_request: str) -> str:
        """
        Run the social agent with the given user request.
        Returns the final text response from Claude.
        """
        messages: list[dict] = [{"role": "user", "content": user_request}]

        for iteration in range(MAX_LOOP_ITERATIONS):
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=16000,
                thinking={"type": "adaptive", "budget_tokens": 8000},
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            # Collect text from the response (may be mixed with thinking/tool_use blocks)
            text_parts: list[str] = []
            tool_uses: list[dict] = []

            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_uses.append(block)

            if response.stop_reason == "end_turn":
                return "\n".join(text_parts) if text_parts else "(nessuna risposta testuale)"

            if response.stop_reason == "tool_use" and tool_uses:
                # Append Claude's full response (including thinking blocks) to messages
                messages.append({"role": "assistant", "content": response.content})

                # Execute all tools and collect results
                tool_results: list[dict] = []
                for tool_block in tool_uses:
                    result = self._dispatch_tool(tool_block.name, tool_block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": result["content"],
                        "is_error": result.get("is_error", False),
                    })

                messages.append({"role": "user", "content": tool_results})
                continue

            # Unexpected stop reason
            break

        return "Limite massimo di iterazioni raggiunto."
