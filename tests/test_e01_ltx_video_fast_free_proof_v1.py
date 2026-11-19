"""Fail-closed offline regressions for VNC LTX Video Fast candidate."""
import unittest
from unittest.mock import patch
from pathlib import Path
from agents import e01_ltx_video_fast_free_proof_v1 as m


class TestLTXFastOneShot(unittest.TestCase):
    def test_canonical_storyboard_immutable(self):
        self.assertTrue(m.validate_source())

    def test_exact_anonymous_request_only(self):
        request = (m.PROMPT, m.NEGATIVE, None, None, m.HEIGHT, m.WIDTH,
                   "text-to-video", m.SECONDS, 9, 42251, False, 3.0, False)
        self.assertTrue(m.validate_request(request))
        for index, replacement in [(2, "/private/face.jpg"), (3, "private.mp4"),
                                   (6, "image-to-video"), (7, 2.0), (4, 512),
                                   (11, 4.0), (12, True)]:
            altered = list(request)
            altered[index] = replacement
            with self.subTest(index=index), self.assertRaises(ValueError):
                m.validate_request(tuple(altered))

    def test_no_false_success_without_real_media(self):
        for result in (None, [], [None], [""], [{"path": "/not/a/file.mp4"}]):
            with self.subTest(result=result), self.assertRaises(ValueError):
                m.video_path_from_result(result)

    def test_identical_frames_are_not_motion(self):
        frame = bytes([55]) * (64 * 112)
        with self.assertRaisesRegex(ValueError, "near_static_or_fake_motion"):
            m.adjacent_frame_motion_score(frame * 10, 64 * 112)
        with self.assertRaises(ValueError):
            m.adjacent_frame_motion_score(frame * 3, 64 * 112)
        video = b"".join(bytes([x]) * (64 * 112) for x in range(0, 16))
        self.assertGreater(m.adjacent_frame_motion_score(video, 64 * 112), 0.55)

    def test_bad_file_is_not_accepted_as_proof(self):
        with self.assertRaises(ValueError):
            m.verify_mp4(Path("/tmp/nonexistent-vnc-ltx-media-file-0001.mp4"))

    def test_no_generation_when_workflow_dispatch_or_replay(self):
        vars = [
            {"GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_RUN_ATTEMPT": "1",
             "GITHUB_REF": "refs/heads/" + m.BRANCH},
            {"GITHUB_EVENT_NAME": "push", "GITHUB_RUN_ATTEMPT": "2",
             "GITHUB_REF": "refs/heads/" + m.BRANCH},
            {"GITHUB_EVENT_NAME": "push", "GITHUB_RUN_ATTEMPT": "1",
             "GITHUB_REF": "refs/heads/main"},
        ]
        for item in vars:
            with self.subTest(item=item), \
                patch.dict("os.environ", item, clear=True), \
                patch.object(m, "check_space_running") as get, \
                patch.object(m, "consume_lock_before_request") as lock, \
                patch.object(m, "report"), \
                self.assertRaises(SystemExit):
                m.main()
            get.assert_not_called()
            lock.assert_not_called()

    def test_private_media_or_publishing_not_in_prompt(self):
        self.assertIn("CLOSED", m.PROMPT)
        self.assertIn("from behind", m.PROMPT)
        self.assertIn("raindrops", m.PROMPT)
        self.assertNotIn("API_KEY", m.PROMPT)
        self.assertEqual(m.PROVIDER_API, "/text_to_video")
        self.assertEqual(m.SECONDS, 6.0)
        self.assertGreater(m.SECONDS, m.TARGET_SCENE)


if __name__ == "__main__":
    unittest.main()
