from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Platform(str, Enum):
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"


class PostDraft(BaseModel):
    caption: str
    hashtags: list[str] = []
    platform: Platform
    image_url: Optional[str] = None

    @property
    def full_text(self) -> str:
        parts = [self.caption]
        if self.hashtags:
            parts.append(" ".join(f"#{tag.lstrip('#')}" for tag in self.hashtags))
        return "\n\n".join(parts)


class PublishResult(BaseModel):
    success: bool
    platform: Platform
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    error: Optional[str] = None


class RecentPost(BaseModel):
    post_id: str
    platform: Platform
    caption: Optional[str] = None
    timestamp: Optional[str] = None
    permalink: Optional[str] = None


# ── Sub-agent output models ────────────────────────────────────────────────────

class VideoScene(BaseModel):
    scene_number: int
    description: str
    duration_seconds: int
    camera_movement: str
    text_overlay: Optional[str] = None
    visual_details: Optional[str] = None   # lighting, texture, dettagli visivi reali


class VideoConcept(BaseModel):
    title: str
    total_duration_seconds: int
    visual_style: str
    platform_format: str        # e.g. "Reels 9:16 10s"
    hook_description: str       # primi 2 secondi
    scenes: list[VideoScene]
    music_mood: str
    color_palette: list[str]
    cinematography_notes: str   # luce, lens, set, atmosfera
    production_notes: str


class VideoGenerationResult(BaseModel):
    status: str                        # "succeeded" | "failed"
    video_url: Optional[str] = None
    task_id: Optional[str] = None
    error: Optional[str] = None
    platform_format: str = ""
    prompt_used: Optional[str] = None
    local_path: Optional[str] = None  # percorso file salvato localmente


class ContentReview(BaseModel):
    revised_caption: str
    revised_hashtags: list[str]
    engagement_score: int = Field(ge=1, le=10)
    changes_summary: list[str]
    community_fit_notes: str
    mainstream_appeal_notes: str
    video_alignment_notes: Optional[str] = None


class SpielbiergReview(BaseModel):
    approved: bool
    realism_score: int = Field(ge=0, le=10)    # 0=errore tecnico, 1=CGI/cartone, 10=iper-realistico
    adherence_score: int = Field(ge=0, le=10)   # 0=errore tecnico, 1=nessuna aderenza, 10=perfetta
    issues: list[str]                            # problemi specifici con riferimento al frame
    improved_prompt_notes: str                   # istruzioni per migliorare il prompt Runway
    verdict: str                                 # verdetto sintetico
