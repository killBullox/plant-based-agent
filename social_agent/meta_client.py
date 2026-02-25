import os
import requests
from typing import Optional
from dotenv import load_dotenv

from .models import Platform, PublishResult, RecentPost

load_dotenv()

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


class MetaAPIError(Exception):
    """Raised when Meta Graph API returns an error (even with HTTP 200)."""

    def __init__(self, message: str, code: Optional[int] = None, subcode: Optional[int] = None):
        super().__init__(message)
        self.code = code
        self.subcode = subcode


def _check_meta_response(data: dict) -> None:
    """Raise MetaAPIError if the response contains an error object."""
    if "error" in data:
        err = data["error"]
        raise MetaAPIError(
            err.get("message", "Unknown Meta API error"),
            code=err.get("code"),
            subcode=err.get("error_subcode"),
        )


class MetaClient:
    def __init__(self):
        self.ig_access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
        self.ig_account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
        self.fb_page_id = os.getenv("FACEBOOK_PAGE_ID", "")
        self.fb_page_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
        self._session = requests.Session()

    # ── Instagram ──────────────────────────────────────────────────────────────

    def instagram_publish(
        self,
        caption: str,
        image_url: Optional[str] = None,
    ) -> PublishResult:
        """Two-step Instagram publish: create container → publish container."""
        try:
            # Step 1: create media container
            container_payload: dict = {
                "caption": caption,
                "access_token": self.ig_access_token,
            }
            if image_url:
                container_payload["image_url"] = image_url
                container_payload["media_type"] = "IMAGE"
            else:
                # Reels/carousel require media; for text-only we use a placeholder
                # In practice IG requires an image — caller should always pass one.
                container_payload["media_type"] = "IMAGE"

            resp = self._session.post(
                f"{GRAPH_API_BASE}/{self.ig_account_id}/media",
                json=container_payload,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            _check_meta_response(data)
            container_id = data["id"]

            # Step 2: publish container
            publish_resp = self._session.post(
                f"{GRAPH_API_BASE}/{self.ig_account_id}/media_publish",
                json={"creation_id": container_id, "access_token": self.ig_access_token},
                timeout=30,
            )
            publish_resp.raise_for_status()
            publish_data = publish_resp.json()
            _check_meta_response(publish_data)
            post_id = publish_data["id"]

            return PublishResult(
                success=True,
                platform=Platform.INSTAGRAM,
                post_id=post_id,
                post_url=f"https://www.instagram.com/p/{post_id}/",
            )
        except MetaAPIError as e:
            return PublishResult(success=False, platform=Platform.INSTAGRAM, error=str(e))
        except requests.RequestException as e:
            return PublishResult(success=False, platform=Platform.INSTAGRAM, error=str(e))

    def instagram_get_recent_posts(self, limit: int = 5) -> list[RecentPost]:
        """Return recent IG posts for editorial context. Silent fallback on error."""
        try:
            resp = self._session.get(
                f"{GRAPH_API_BASE}/{self.ig_account_id}/media",
                params={
                    "fields": "id,caption,timestamp,permalink",
                    "limit": limit,
                    "access_token": self.ig_access_token,
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            _check_meta_response(data)
            posts = []
            for item in data.get("data", []):
                posts.append(
                    RecentPost(
                        post_id=item["id"],
                        platform=Platform.INSTAGRAM,
                        caption=item.get("caption"),
                        timestamp=item.get("timestamp"),
                        permalink=item.get("permalink"),
                    )
                )
            return posts
        except Exception:
            return []

    # ── Facebook ───────────────────────────────────────────────────────────────

    def facebook_publish(self, message: str) -> PublishResult:
        """Publish to Facebook Page feed using Page Access Token."""
        try:
            resp = self._session.post(
                f"{GRAPH_API_BASE}/{self.fb_page_id}/feed",
                json={"message": message, "access_token": self.fb_page_token},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            _check_meta_response(data)
            post_id = data["id"]

            return PublishResult(
                success=True,
                platform=Platform.FACEBOOK,
                post_id=post_id,
                post_url=f"https://www.facebook.com/{post_id}",
            )
        except MetaAPIError as e:
            return PublishResult(success=False, platform=Platform.FACEBOOK, error=str(e))
        except requests.RequestException as e:
            return PublishResult(success=False, platform=Platform.FACEBOOK, error=str(e))

    def facebook_get_recent_posts(self, limit: int = 5) -> list[RecentPost]:
        """Return recent FB page posts for editorial context. Silent fallback on error."""
        try:
            resp = self._session.get(
                f"{GRAPH_API_BASE}/{self.fb_page_id}/feed",
                params={
                    "fields": "id,message,created_time,permalink_url",
                    "limit": limit,
                    "access_token": self.fb_page_token,
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            _check_meta_response(data)
            posts = []
            for item in data.get("data", []):
                posts.append(
                    RecentPost(
                        post_id=item["id"],
                        platform=Platform.FACEBOOK,
                        caption=item.get("message"),
                        timestamp=item.get("created_time"),
                        permalink=item.get("permalink_url"),
                    )
                )
            return posts
        except Exception:
            return []
