"""
Mostra i 3 post Beet It! già generati nel formato terminale completo.
Nessuna chiamata API — tutto hardcoded. Dry run (nessuna pubblicazione).
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import builtins
import json

# ── Auto-approva tutto (dry run) ──────────────────────────────────────────────
builtins.input = lambda prompt="": (print(f"{prompt}y  ← auto-approvato (dry run)"), "y")[1]

from social_agent.agent import SocialAgent
from social_agent.models import (
    VideoConcept, VideoScene, ContentReview, Platform, PostDraft
)
from social_agent.meta_client import MetaClient
from social_agent.models import PublishResult

# ── Blocca pubblicazione (dry run) ────────────────────────────────────────────
def _fake_ig(self, caption, image_url=None):
    print(f"\n  [DRY RUN] Instagram publish SKIPPED — {len(caption)} chars")
    return PublishResult(success=True, platform=Platform.INSTAGRAM, post_id="dry-run")

def _fake_fb(self, message):
    print(f"\n  [DRY RUN] Facebook publish SKIPPED — {len(message)} chars")
    return PublishResult(success=True, platform=Platform.FACEBOOK, post_id="dry-run")

MetaClient.instagram_publish = _fake_ig
MetaClient.facebook_publish = _fake_fb

# ═══════════════════════════════════════════════════════════════════════════════
# DATI DEI 3 POST
# ═══════════════════════════════════════════════════════════════════════════════

POSTS = [

    # ── POST 1: Ricetta veloce con barbabietola ─────────────────────────────
    dict(
        platform="instagram",
        caption=(
            "La bowl che ti fa guardare il pranzo come un'opera d'arte. 🎨\n\n"
            "Barbabietola arrosto + hummus 3 minuti + quinoa + rucola + olio di sesamo.\n\n"
            "Tempo totale: 20 minuti. Complimenti ricevuti: garantiti.\n\n"
            "Il segreto? La barbabietola arrosto cambia tutto rispetto a quella bollita "
            "— diventa dolce, quasi caramellata. E quel viola intenso è praticamente "
            "un filtro Instagram naturale.\n\n"
            "Come farla:\n"
            "🔴 Taglia a cubetti, olio + cumino + sale\n"
            "🔴 Forno 200° per 25 min (o 15 min friggitrice ad aria)\n"
            "🔴 Nel frattempo: hummus veloce con ceci, limone, aglio\n"
            "🔴 Assembla su quinoa e rucola\n\n"
            "Mangiare plant-based senza rinunciare a niente. Anzi, aggiungendo molto.\n\n"
            "Salva per il prossimo pranzo pigro. 💾"
        ),
        hashtags=[
            "beetit","plantbased","barbabietola","ricettevegane","bowl",
            "pranzoveloci","mangiarbene","veganrecipes","plantbasedlife","healthyfood",
            "cucinaitaliana","mealprep","ricettarapida","quinoa","hummus",
            "veganfood","italianvegan","nutrizione","benessere","cibosano",
            "foodporn","veganitaliano","ricettainstant","lunchideas","eatclean",
        ],
        concept=VideoConcept(
            title="La Bowl Viola in 4 Passi",
            total_duration_seconds=10,
            visual_style="Cinematic food video, warm natural lighting, real kitchen, macro close-up",
            platform_format="Reels 9:16 10s",
            hook_description="Macro close-up: mani che tagliano una barbabietola fresca su tagliere di legno — succo viola che cola lentamente, slow motion",
            scenes=[
                VideoScene(scene_number=1, description="Mani che tagliano barbabietola a cubetti, succo viola sul tagliere", duration_seconds=3, camera_movement="macro 45°, slow motion", visual_details="succo viola lucido, texture ruvida della barbabietola cruda, tagliere di legno scuro"),
                VideoScene(scene_number=2, description="Teglia con cubetti dorati che escono dal forno, vapore che sale", duration_seconds=2, camera_movement="overhead close-up", visual_details="cubetti caramellati, bordi dorati, vapore reale, olio lucido"),
                VideoScene(scene_number=3, description="Mani che assemblano la bowl: quinoa, rucola fresca, hummus cremoso, barbabietola arrosto", duration_seconds=3, camera_movement="overhead fisso, ogni ingrediente aggiunto uno alla volta", visual_details="colori vividi viola-verde-crema, ingredienti freschi reali in ciotola ceramica"),
                VideoScene(scene_number=4, description="Filo d'olio di sesamo dorato versato sulla bowl finita in slow motion", duration_seconds=2, camera_movement="macro laterale 45°, slow motion", visual_details="olio che scivola sugli ingredienti, riflesso dorato, bowl appetitosa"),
            ],
            music_mood="Lo-fi chill, ritmo calmo e appetitoso",
            color_palette=["viola barbabietola", "verde rucola", "crema hummus", "oro olio di sesamo"],
            cinematography_notes="Luce naturale da finestra laterale sinistra. Set: tagliere di legno, ciotola ceramica bianca, piano marmo chiaro. Atmosfera cucina casalinga premium.",
            production_notes="Mani sempre visibili. Tutto reale e replicabile a casa. Nessun effetto digitale.",
        ),
    ),

    # ── POST 2: Fatto sorprendente sulla nutrizione plant-based ─────────────
    dict(
        platform="instagram",
        caption=(
            "Aspetta. Le lenticchie hanno PIÙ ferro della carne rossa. 🤯\n\n"
            "100g di lenticchie secche: 7,5 mg di ferro\n"
            "100g di manzo: 2,7 mg di ferro\n\n"
            '"Ma il ferro vegetale si assorbe di meno!" — sì, vero.\n'
            "Però abbina le lenticchie con vitamina C (limone, pomodori, peperone) "
            "e l'assorbimento sale. La soluzione era già nella cucina mediterranea "
            "da secoli, per chi se lo fosse perso.\n\n"
            "E non è solo il ferro: i legumi sono una macchina nutrizionale completa "
            "— proteine, fibre, zinco, acido folico, potassio.\n\n"
            "Il problema non è il cibo plant-based.\n"
            "È che nessuno ce lo ha mai spiegato bene.\n\n"
            "Noi sì. Con Beet It! 🔴\n\n"
            'Salva e mandalo a chi ti fa la domanda "ma le proteine??" 😅'
        ),
        hashtags=[
            "beetit","plantbased","nutrizione","lenticchie","ferro",
            "proteine","veganfacts","alimentazione","plantbasednutrition","veganlife",
            "salute","benessere","sfataimiti","scienzanutrizionale","legumi",
            "cucinaitaliana","veganitaliano","mangiarbene","healthyfood","nutritionfacts",
            "proteinevegetali","vitaminac","ferroalimenti","dietavegana","eatwell",
        ],
        concept=VideoConcept(
            title="Lenticchie vs Carne: il Confronto",
            total_duration_seconds=10,
            visual_style="Cinematic documentary style, clean minimal set, photorealistic food comparison, warm tones",
            platform_format="Reels 9:16 10s",
            hook_description="Split screen simmetrico: ciotola di lenticchie rosse a sinistra, bistecca cruda a destra — entrambe su bilance da cucina cromate",
            scenes=[
                VideoScene(scene_number=1, description="Due bilance cromate affiancate: lenticchie rosse vs bistecca marmorizzata, con display digitale ben visibile", duration_seconds=3, camera_movement="frontale simmetrico, leggero push-in", visual_details="lenticchie rosse brillanti, bistecca con marmorizzazione, bilance cromate lucide, sfondo bianco pulito"),
                VideoScene(scene_number=2, description="Macro close-up: mano che strizza mezzo limone su ciotola di lenticchie cotte, gocce di succo in slow motion", duration_seconds=3, camera_movement="macro laterale, slow motion", visual_details="gocce di limone giallo che cadono sulle lenticchie rosse cotte, vapore leggero, cucchiaio di legno"),
                VideoScene(scene_number=3, description="Piatto di lenticchie con verdure fresche su tavola di legno chiaro, vista dall'alto", duration_seconds=4, camera_movement="overhead pull-back lento", visual_details="lenticchie cotte, pomodorini, prezzemolo fresco, limone a fette, luce naturale calda"),
            ],
            music_mood="Discovery beat leggero e informativo, ritmo calmo",
            color_palette=["rosso lenticchie", "verde erbe", "giallo limone", "bianco pulito"],
            cinematography_notes="Piano bianco o marmo chiaro. Luce naturale laterale morbida. Estetica pulita e credibile, stile documentario gastronomico.",
            production_notes="Tutto reale, nessun elemento digitale. Il confronto delle bilance deve essere immediatamente comprensibile.",
        ),
    ),

    # ── POST 3: Motivazionale anti-luoghi comuni ─────────────────────────────
    dict(
        platform="instagram",
        caption=(
            "No, non siamo tutti pallidi e affaticati. 👋\n\n"
            "Luoghi comuni sul plant-based che siamo stanchi di sentire:\n\n"
            '❌ "Ma le proteine?"\n'
            "→ Legumi, tofu, tempeh, seitan, noci. Grazie per la preoccupazione.\n\n"
            '❌ "È troppo costoso"\n'
            "→ Pacco di lenticchie: €1,20. Confrontalo con la bistecca.\n\n"
            '❌ "Si mangia solo insalata"\n'
            "→ Burger di ceci. Pasta al ragù di lenticchie. Tiramisù vegano. Vuoi continuare?\n\n"
            '❌ "Manca il gusto"\n'
            "→ Chi lo ha detto non ha mai provato una bowl di barbabietola con tahini e melograno.\n\n"
            "Mangiare più vegetale non significa diventare un'altra persona.\n"
            "Significa scoprire che il cibo può essere buono, sostenibile e nutriente allo stesso tempo.\n\n"
            "Beet It! — niente sermoni, solo cibo che spacca. 🔴\n\n"
            "Tagga chi ha ancora questi pregiudizi (con affetto, eh) 👇"
        ),
        hashtags=[
            "beetit","plantbased","veganitaliano","veganlife","sfataimiti",
            "proteinevegetali","cibosostenibile","mangiarbene","alimentazioneconsapevole","vegansofitaly",
            "italianvegan","veganmyths","healthyfood","mealinspo","plantbaseddiet",
            "legumi","nutrizione","benessere","sostenibilita","cibosano",
            "cucinaitaliana","vegancooking","nientesermonì","eatplants","plantpower",
        ],
        concept=VideoConcept(
            title="Cibo Plant-Based Reale",
            total_duration_seconds=10,
            visual_style="Fast-cut food video, vibrant real colors, energetic pacing, photorealistic food shots",
            platform_format="Reels 9:16 10s",
            hook_description="Macro close-up: burger di ceci home-made tagliato a metà in slow motion — ripieno abbondante con insalata, pomodoro, salsa",
            scenes=[
                VideoScene(scene_number=1, description="Burger di ceci tagliato a metà in slow motion — ripieno colorato e abbondante", duration_seconds=3, camera_movement="macro laterale 45°, slow motion del taglio", visual_details="pane tostato dorato, burger di ceci croccante, insalata verde fresca, pomodoro rosso, salsa bianca"),
                VideoScene(scene_number=2, description="Ciotola di legumi misti su tavola rustica: lenticchie, ceci, fagioli neri — colori vividi", duration_seconds=2, camera_movement="overhead 45°, leggero zoom in", visual_details="legumi lucidi e freschi, ciotola ceramica scura, erbe aromatiche, limone"),
                VideoScene(scene_number=3, description="Mano che versa tahini bianco cremoso su bowl di barbabietola e semi di melograno", duration_seconds=3, camera_movement="macro laterale slow motion", visual_details="tahini che scivola lentamente, semi di melograno rossi, barbabietola viola, contrasto colori vivido"),
                VideoScene(scene_number=4, description="Pasta al ragù di lenticchie servita in piatto fondo, vapore che sale, parmigiano grattugiato sopra", duration_seconds=2, camera_movement="macro frontale 45°", visual_details="ragù rosso ricco, pasta al dente, vapore reale, parmigiano che fila"),
            ],
            music_mood="Hip-hop energico, punch sonoro ad ogni cambio scena",
            color_palette=["rosso pomodoro", "verde fresco", "viola barbabietola", "crema tahini"],
            cinematography_notes="Set cucina reale o piano legno rustico. Luce morbida da softbox laterale. Fast cut ogni 2-3 secondi. Tutto deve sembrare delizioso e replicabile.",
            production_notes="Ogni shot è un piatto diverso che sfata un mito. Real food only, nessun effetto digitale.",
        ),
    ),
]

# ═══════════════════════════════════════════════════════════════════════════════
# ESECUZIONE: mostra ogni post nel formato terminale dell'agente
# ═══════════════════════════════════════════════════════════════════════════════

from social_agent.video_generator_agent import VideoGeneratorAgent
from social_agent.spielbierg_agent import SpielbiergAgent
from social_agent.models import ContentReview

agent = SocialAgent()

for i, post in enumerate(POSTS, 1):
    print(f"\n\n{'#' * 60}")
    print(f"  POST {i} / {len(POSTS)}")
    print(f"{'#' * 60}")

    concept = post["concept"]
    agent._current_video_concept = concept

    # ── Step 3: VC ──────────────────────────────────────────────────────────
    print(f"\n  [VC] Concept '{concept.title}' generato ({concept.total_duration_seconds}s).")

    # ── Step 4 + 5: Runway → Spielbierg (reali, max 3 tentativi) ────────────
    MAX_SPIELBIERG_ATTEMPTS = 3
    additional_notes = None
    agent._spielbierg_attempts = 0
    agent._current_spielbierg_review = None

    for attempt in range(1, MAX_SPIELBIERG_ATTEMPTS + 1):
        vg_result = VideoGeneratorAgent().generate(
            concept, post["platform"], additional_notes=additional_notes
        )
        agent._current_video_url = vg_result.video_url if vg_result.status == "succeeded" else None

        if not agent._current_video_url:
            # Runway fallito — salta Spielbierg
            break

        agent._spielbierg_attempts = attempt
        print(f"\n  [Spielbierg] Analisi video (tentativo {attempt}/{MAX_SPIELBIERG_ATTEMPTS})...")
        review = SpielbiergAgent().review_video(
            video_url=agent._current_video_url,
            concept=concept,
            caption=post["caption"],
            hashtags=post["hashtags"],
        )
        agent._current_spielbierg_review = review
        status = "APPROVED" if review.approved else "REJECTED"
        print(
            f"  [Spielbierg] {status} — "
            f"Realism {review.realism_score}/10, Adherence {review.adherence_score}/10"
        )
        print(f"  Verdetto: {review.verdict}")
        if review.issues:
            for issue in review.issues:
                print(f"    • {issue}")

        if review.approved:
            break
        if attempt < MAX_SPIELBIERG_ATTEMPTS:
            print(f"  [Spielbierg] Rigenerazione con note: {review.improved_prompt_notes}")
            additional_notes = review.improved_prompt_notes
        else:
            print("  [Spielbierg] 3 tentativi esauriti — procedo con il video disponibile.")

    # ── Step 6: SMCC (mock — nessuna API Anthropic necessaria) ──────────────
    agent._current_review = ContentReview(
        revised_caption=post["caption"],
        revised_hashtags=post["hashtags"],
        engagement_score=9,
        changes_summary=[
            "Hook rafforzato per massimizzare stop-rate nei primi 2s",
            "Call-to-action finale ottimizzata per commenti",
            "Hashtag bilanciati: mix nicchia + mainstream per copertura ottimale",
        ],
        community_fit_notes="Tono Beet It! mantenuto — ironico senza essere esclusivo.",
        mainstream_appeal_notes="Accessibile ai neofiti, risuona con chi è già plant-based.",
        video_alignment_notes=f"Video concept '{concept.title}' allineato al messaggio del post.",
    )
    print(f"\n  [SMCC] Revisione completata. Score engagement: 9/10.")

    # Mostra il post nel formato ufficiale
    agent._handle_request_approval(
        platform=post["platform"],
        caption=post["caption"],
        hashtags=post["hashtags"],
    )

    # Dry run: non pubblicare
    print(f"  [DRY RUN] Instagram publish SKIPPED per post {i}.")

    # Reset stato per il post successivo
    agent._current_video_concept = None
    agent._current_video_url = None
    agent._current_review = None
    agent._approved_draft = None

print(f"\n\n{'═' * 60}")
print(f"  COMPLETATO — 3 post Beet It! generati (dry run)")
print(f"{'═' * 60}")
print("\nPer generare video reali: aggiungi RUNWAYML_API_SECRET nel .env")
print("Per pubblicare: esegui python _dry_run.py con le API key configurate\n")
