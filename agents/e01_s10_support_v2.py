"""One stronger S10 support-shot candidate from a free public real 4K video.

Separate from earlier S10 cafe rejected source. All release/rights gates stay off.
"""
from __future__ import annotations
import json
from pathlib import Path
from agents import e01_two_real_stock_support as intake

OUTPUT=Path("artifacts/e01_s10_support_v2")
SOURCE={
 "scene_id":"VNC-E01V2-S10",
 "video_id":6381001,
 "start":0.25,
 "seconds":8.0,
 "minimum":6.6,
 "creator":"Liza Summer",
 "group":"COMMUNITY_D",
 "source_page":"https://www.pexels.com/video/woman-holding-the-hand-of-another-person-6381001/"
}
BASE={
 "episode_id":"VNC-W01-E1",
 "source_type":"FREE_PEXELS_CAMERA_STOCK",
 "license_url":"https://www.pexels.com/license/",
 "source_has_same_recurring_protagonist":False,
 "private_model_release_verified":False,
 "right_to_imply_subject_endorses_religion":False,
 "editorial_acceptance":False,
 "master_approved":False,
 "publication_authorized":False,
 "zero_payment":True,
 "no_api_key":True
}

def run():
 OUTPUT.mkdir(parents=True,exist_ok=True)
 intake.OUT=OUTPUT
 result=intake.inspect(SOURCE)
 obj={**BASE,"scene":result,
      "technical_candidate_count":int(result.get("status")=="PHYSICAL_VIDEO_VALIDATED_EDITORIAL_PENDING")}
 (OUTPUT/"report.json").write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print(json.dumps({"status":result["status"],"editorial_acceptance":False,
                  "publication_authorized":False}),flush=True)
 return 0 if obj["technical_candidate_count"] else 2

if __name__=="__main__":
 raise SystemExit(run())
