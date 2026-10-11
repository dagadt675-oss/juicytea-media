"""Segment plan, cache keys, and boundary continuity."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

WHATIF = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WHATIF))
sys.path.insert(0, str(WHATIF / "scale_journey"))

from engine.bformat import resolve_b  # noqa: E402
from engine.segments import HANDLE_FRAMES, plan_segments  # noqa: E402

EP = WHATIF / "scale_journey" / "episodes" / "penny_empire.yaml"
ROOT = WHATIF / "scale_journey"


class PlanTest(unittest.TestCase):
    def test_chunks_cover_the_episode_without_overlap(self):
        ep = resolve_b(EP)
        segments = plan_segments(len(ep.frames), ep.fps, ep.beats)
        self.assertEqual(segments[0].start, 0)
        self.assertEqual(segments[-1].end, len(ep.frames))
        for left, right in zip(segments, segments[1:]):
            self.assertEqual(left.end, right.start)
        for segment in segments:
            seconds = (segment.end - segment.start) / ep.fps
            self.assertGreaterEqual(seconds, 2.0 - 1e-6)
            self.assertLessEqual(seconds, 5.0 + 1e-6)
            if segment.start > 0:
                self.assertEqual(segment.handles, (segment.start - 2, segment.start - 1))
            else:
                self.assertEqual(segment.handles, ())
        self.assertEqual(HANDLE_FRAMES, 2)

    def test_only_the_touched_segment_changes_key(self):
        from engine.render_b import _compose_key, _geom, _scene_key, _spec_key, _ui
        from engine.segments import hash_key

        ep = resolve_b(EP)
        segments = plan_segments(len(ep.frames), ep.fps, ep.beats)

        class Args:
            samples = 16
            scale = 100
            preview = True
            plate_format = "png"
            spec = EP

        scene = _scene_key(ep, Args)
        compose = _compose_key()
        spec = _spec_key(EP)

        class Wrap:
            frames = ep.frames

        ep_like = Wrap()

        def key_for(segment):
            rendered = [ep_like.frames[i] for i in segment.render_frames]
            body = [ep_like.frames[i] for i in segment.body]
            plate = hash_key(scene, True, [_geom(ep_like, fr) for fr in rendered])
            return hash_key(plate, compose, spec, [_ui(fr) for fr in body])

        before = [key_for(segment) for segment in segments]
        victim = segments[2]
        changed = list(ep.frames)
        fr = changed[victim.start]
        changed[victim.start] = type(fr)(**{**fr.__dict__, "cam": (fr.cam[0] + 1.0, fr.cam[1], fr.cam[2])})
        ep_like.frames = changed
        after = [key_for(segment) for segment in segments]
        diffs = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
        self.assertEqual(diffs, [victim.index])


class BoundaryTest(unittest.TestCase):
    def test_handle_frames_use_the_same_camera_as_a_full_pass(self):
        from engine.render_b import _geom

        ep = resolve_b(EP)
        segments = plan_segments(len(ep.frames), ep.fps, ep.beats)
        boundary = segments[1]
        full = {fr.frame: _geom(ep, fr) for fr in ep.frames}
        for frame in boundary.render_frames:
            self.assertEqual(full[frame]["cam"], _geom(ep, ep.frames[frame])["cam"])
            self.assertEqual(full[frame]["prev_cam"], _geom(ep, ep.frames[frame])["prev_cam"])
        # The first published frame was rendered with the previous frame as its handle.
        self.assertEqual(boundary.handles[-1], boundary.start - 1)
        self.assertEqual(full[boundary.start]["prev_cam"], full[boundary.handles[-1]]["cam"])

    def test_dropped_handles_are_not_in_the_published_range(self):
        ep = resolve_b(EP)
        for segment in plan_segments(len(ep.frames), ep.fps, ep.beats):
            published = set(segment.body)
            self.assertTrue(set(segment.handles).isdisjoint(published))


if __name__ == "__main__":
    unittest.main()
