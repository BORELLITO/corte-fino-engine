"""No-GPU adversarial tests of a single anonymous S04 video generation candidate."""
import inspect
import unittest
from agents import e01_s04_one_shot_zero_gpu_candidate as subject

class TestS04SingleFreeTrial(unittest.TestCase):
    def test_exact_canonical_duration_and_no_room_a_confusion(self):
        self.assertEqual(subject.PROJECT,"VERBO_NO_CHAO_EXCLUSIVO")
        self.assertEqual(subject.SCENE,"VNC-E01V2-S04")
        self.assertEqual(subject.DURATION_REQUIRED,5.82)
        self.assertEqual(subject.FRAMES,145)
        self.assertEqual(subject.FPS_TARGET,24)

    def test_no_private_media_and_no_master_or_publication(self):
        e=subject.report_template()
        self.assertIsNone(e["input"]["input_image"])
        self.assertFalse(e["user_private_media_uploaded"])
        self.assertFalse(e["external_account_used"])
        self.assertFalse(e["can_enter_master"])
        self.assertFalse(e["publication_authorized"])
        self.assertEqual(e["money_spent"],0)
        self.assertEqual(e["job_submissions"],0)

    def test_prompt_requires_symbolic_not_historical_and_no_written_words(self):
        p=subject.PROMPT
        self.assertIn("symbolic",p.lower())
        self.assertIn("NOT a historical portrait",p)
        self.assertIn("BLANK",p)
        self.assertIn("No ink marks",p)
        self.assertIn("No ink marks, no letters, no words",p)

    def test_no_auto_retry_or_paid_service_bypass(self):
        text=inspect.getsource(subject.run)
        self.assertEqual(text.count("client.submit("),1)
        self.assertNotIn("while True:",text)
        self.assertNotIn("HF_TOKEN",text)
        self.assertNotIn("retry(",text)
        self.assertIn("job_submissions",text)

    def test_missing_or_unsafe_video_output_is_rejected(self):
        for value in ([],{},None,42,["not_a_real_video.mp4"]):
            with self.subTest(value=str(value)):
                with self.assertRaises(ValueError):
                    subject.extract_output_file(value)

if __name__=="__main__":
    unittest.main()
