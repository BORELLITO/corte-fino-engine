"""Agnes 2.5 Flash zero-cost video adapter PREPARED, explicitly NOT LIVE.

Only produces a validated cost-free request plan. No POST, no login, no credit
card, no paid-model fallback. Official provider API needs an AGNES_API_KEY and
account-specific active $0 price check before ANY submission.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from agents.e01_stock_candidates import ROOT, require

MODEL="agnes-video-2.5-flash"
API="https://apihub.agnes-ai.com/v1/videos"
PRICE_DOC="https://wiki.agnes-ai.com/en/docs/pricing.md"
SCENE_SECONDS=5.74
SCRIPT="c64b57cb9d6529b60b9e80ab7607e5887f909dd00e14cd80ed9ec2b7474a5dc6"
AUDIO="4f2ee1ff0171ddedb7c64e0dce2300c53a0ef105ef12d643a7af6b0a4621942e"
STORY=Path("contracts/e01_v2_12_scene_visual_plan_v1.json")
POLICY=Path("contracts/e01_agnes_flash_free_only_v1.json")

PROMPT=(
 "Original fictional, cinematic photorealistic portrait video, one continuous "
 "six-second shot in a modest small apartment room at night. One anonymous adult "
 "strictly seen from behind, wearing the same charcoal wool jacket throughout, "
 "sits near a rain-covered window. Their face is NEVER visible. A closed dark "
 "notebook lies flat on a worn wood desk under dim amber lamp light. The notebook "
 "must stay SHUT, with zero exposed pages or readable words. Visible raindrops "
 "trickle down glass, nuanced reflections move gently; natural breathing and "
 "almost imperceptible hand motion. Smooth restrained camera push-in. Documentary "
 "plausibility, neutral skin tones, exact anatomy, 35mm visual texture, no "
 "supernatural effects, no logos, no screens, no text, no voice or soundtrack. "
 "Keep the bottom 22 percent dark and empty for separate synced subtitles."
)

def payload():
 return {"model":MODEL,"prompt":PROMPT,"mode":"text",
         "seconds":"6","size":"720P","aspect_ratio":"9:16",
         "seed":42251,"n":1}

def validate(root=ROOT):
 doc=json.loads((root/POLICY).read_text(encoding="utf-8"))
 storyboard=json.loads((root/STORY).read_text(encoding="utf-8"))
 req=payload()
 require(doc.get("schema_version")=="1.0.0"
     and doc.get("model")==MODEL
     and doc.get("endpoint")==API
     and doc.get("account_specific_free_price_verified") is False
     and doc.get("model_available_to_account_verified") is False
     and doc.get("provider_api_key_connected") is False
     and doc.get("zero_automatic_payment_guard") is True
     and doc.get("generation_enabled") is False
     and doc.get("user_publication_authorized") is False
     and doc.get("fallback_to_paid_model") is False
     and doc.get("storyboard_hash")==SCRIPT
     and doc.get("narration_hash")==AUDIO
     and storyboard.get("script_sha256")==SCRIPT
     and storyboard.get("audio_sha256")==AUDIO
     and storyboard["scenes"][0]["id"]=="VNC-E01V2-S01"
     and storyboard["scenes"][0]["end_seconds"]==SCENE_SECONDS,
     "agnes:request_or_billing_gate_conflict")
 require(req["model"]==MODEL and req["seconds"]=="6" and req["size"]=="720P"
     and req["aspect_ratio"]=="9:16" and req["mode"]=="text" and req["n"]==1
     and 200<=len(req["prompt"])<=2000
     and not any(k in req for k in ("billing","payment","quality","num_frames","width","height","videos")),
     "agnes:paid_model_or_invalid_request")
 return {
   "status":"AGNES_FLASH_DRY_RUN_VALID_NO_MEDIA_GENERATED",
   "model":MODEL,"endpoint":API,"mode":req["mode"],
   "seconds":req["seconds"],"resolution":req["size"],
   "ratio":req["aspect_ratio"],
   "promotion_publicly_advertised_but_account_price_unverified":True,
   "secret_configured_from_environment":bool(os.environ.get("AGNES_API_KEY")),
   "request_not_sent":True,"provider_access_unverified":True,
   "provider_queue_not_checked":True,
   "commercial_use_rights_not_cleared":True,
   "publication_authorized":False,
   "monetary_charge":0
 }

if __name__=="__main__":
 print(json.dumps(validate(),ensure_ascii=False,indent=2))
