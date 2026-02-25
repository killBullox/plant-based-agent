"""
Dry-run: genera post + video senza pubblicare nulla.
- input() auto-approvato
- Meta publish patched (nessuna chiamata API reale)
- MAX_LOOP_ITERATIONS alzato a 40 per 3 post × 8 step
"""
import builtins
import social_agent.agent as _agent_module

# ── 1. Aumenta il limite loop per 3 post ─────────────────────────────────────
_agent_module.MAX_LOOP_ITERATIONS = 40

# ── 2. Auto-approva ogni post ─────────────────────────────────────────────────
def _auto_approve(prompt=""):
    print(f"{prompt}y  ← auto-approvato (dry run)")
    return "y"
builtins.input = _auto_approve

# ── 3. Blocca le publish (dry run) ────────────────────────────────────────────
from social_agent.meta_client import MetaClient
from social_agent.models import PublishResult, Platform

def _fake_instagram_publish(self, caption, image_url=None):
    print(f"\n  [DRY RUN] Instagram publish SKIPPED — {len(caption)} chars")
    return PublishResult(success=True, platform=Platform.INSTAGRAM, post_id="dry-run-ig")

def _fake_facebook_publish(self, message):
    print(f"\n  [DRY RUN] Facebook publish SKIPPED — {len(message)} chars")
    return PublishResult(success=True, platform=Platform.FACEBOOK, post_id="dry-run-fb")

MetaClient.instagram_publish = _fake_instagram_publish
MetaClient.facebook_publish = _fake_facebook_publish

# ── 4. Esegui ─────────────────────────────────────────────────────────────────
from social_agent import SocialAgent

REQUEST = """\
Genera 3 post per il brand "Beet It! — nutrizione vegetale che spacca".

Il brand è:
- Tono fresco, giovane, ironico — non infantile
- Colori: rosso/viola barbabietola
- Target: chiunque voglia avvicinarsi al plant based
- Valori: energia, semplicità, sostenibilità (senza sermoni)

Crea un post su:
1. Una ricetta veloce con barbabietola
2. Un fatto sorprendente sulla nutrizione plant based
3. Un post motivazionale anti-luoghi comuni sul vegano

Modalità DRY RUN: mostra testo, hashtag e URL video — non pubblicare nulla.
"""

agent = SocialAgent()
result = agent.run(REQUEST)

print("\n" + "=" * 60)
print("RISULTATO FINALE")
print("=" * 60)
print(result)
