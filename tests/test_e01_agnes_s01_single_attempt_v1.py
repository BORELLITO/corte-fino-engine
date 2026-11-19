"""Offline regression tests: one authorized free S01 attempt, no secret/network."""
import unittest
from unittest.mock import patch
from agents import e01_agnes_s01_single_attempt_v1 as s


class TestOneShotS01(unittest.TestCase):
    def test_only_exact_current_price_can_pass(self):
        doc = """# Model Pricing
Only items priced at zero are free
Agent Plan usage is billed
For default users (`default`)
## Video models
<tr>
<td>`agnes-video-2.5-flash`</td>
<td>720P video duration</td>
<td>`$0.025 / second`</td>
<td>**`$0 / second`**</td>
</tr>
all billing items are free during the limited-time free promotion
""" + ("supplemental official terms " * 150)
        self.assertTrue(s.price_is_zero(doc))
        self.assertFalse(s.price_is_zero(doc.replace("**`$0 / second`**",
                                                  "`$0.025 / second`")))
        self.assertFalse(s.price_is_zero(doc.replace("agnes-video-2.5-flash",
                                                  "agnes-video-2.5")))
        self.assertFalse(s.price_is_zero(doc.replace("default users (`default`)",
                                                  "paid users only")))
        self.assertFalse(s.price_is_zero(doc.replace("Agent Plan usage is billed",
                                                  "Agent Plan is free")))

    def test_existing_canonical_gate_is_never_activated_on_disk(self):
        with patch.object(s.transport, "submit_once",
                          return_value={"video_id": "job_123456", "status": "JOB_SUBMITTED_NOT_APPROVED"}) as submit:
            result = s.submit_with_ephemeral_proven_gate("fake-key-no-network")
        self.assertEqual(result["video_id"], "job_123456")
        gate = s.transport.gate_config()
        self.assertFalse(gate["enable_submission"])
        self.assertFalse(gate["scene_generation_authorized"])
        self.assertEqual(submit.call_args.kwargs["auth"] if "auth" in submit.call_args.kwargs
                         else submit.call_args.args[1], s.AUTHORIZATION)

    def test_must_not_call_provider_on_invalid_event_or_rerun(self):
        for event, ref, attempt in (
            ("workflow_dispatch", "refs/heads/" + s.BRANCH, "1"),
            ("push", "refs/heads/main", "1"),
            ("push", "refs/heads/" + s.BRANCH, "2"),
        ):
            env = {"GITHUB_EVENT_NAME": event, "GITHUB_REF": ref,
                   "GITHUB_RUN_ATTEMPT": attempt, "AGNES_API_KEY": "fake-key-123456",
                   "VNC_S01_AUTHORIZATION": s.AUTHORIZATION}
            with self.subTest(event=event, ref=ref, attempt=attempt), \
                 patch.dict("os.environ", env, clear=True), \
                 patch.object(s.transport, "model_preflight") as preflight, \
                 patch.object(s, "fetch_price_proof") as price, \
                 self.assertRaises(SystemExit):
                s.main()
            preflight.assert_not_called()
            price.assert_not_called()


if __name__ == "__main__":
    unittest.main()
