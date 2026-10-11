"""Segment plan, cache keys, and boundary continuity.

Run from whatif/:  python3 -m unittest tests.test_segments
"""

from __future__ import annotations

import copy
import shutil
import unittest
from pathlib import Path

from engine.segments import (
    SegmentContinuityError,
    assemble,
    code_digest,
    encode_sequence,
    ffmpeg_command,
    file_hash,
    frame_name,
    frame_seed,
    plan_segments,
    run_segments,
    segment_key,
    verify_boundaries_against_full,
)
from engine.spec import channels_at, load_yaml, resolve

SPEC = Path(__file__).resolve().parents[1] / "episodes" / "humans_disappeared.yaml"


def _spec(seconds, fps=30):
    beats = []
    for index, length in enumerate(seconds):
        beats.append(
            {
                "id": f"b{index}",
                "narration": "word",
                "seconds": length,
                "channels": {"vegetation": round(0.05 * index, 4)},
            }
        )
    return {
        "id": "synthetic",
        "fps": fps,
        "width": 64,
        "height": 64,
        "scene": {"seed": 11, "pieces": ["city"]},
        "camera": {"location": [0, -1, 2], "target": [0, 1, 0], "lens": 40},
        "beats": beats,
    }


def _pixel(resolved, frame) -> bytes:
    sample = channels_at(resolved, frame)
    veg = round(float(sample["vegetation"]), 6)
    return f"{frame}|{frame_seed(frame)}|{veg}\n".encode()


def _writer(resolved, ext="png"):
    def render(segment, dest):
        dest.mkdir(parents=True, exist_ok=True)
        for frame in range(segment["render_start"], segment["render_end"] + 1):
            (dest / frame_name(frame, ext)).write_bytes(_pixel(resolved, frame))

    return render


def _full(directory, resolved, ext="png"):
    directory.mkdir(parents=True, exist_ok=True)
    for frame in range(1, resolved["frame_count"] + 1):
        (directory / frame_name(frame, ext)).write_bytes(_pixel(resolved, frame))


class PlanTest(unittest.TestCase):
    def test_chunks_stay_inside_two_to_five_seconds_and_cover_the_film(self):
        resolved = resolve(_spec([1.0, 1.0, 6.0, 3.0, 0.5, 0.5]))
        segments = plan_segments(resolved, min_seconds=2.0, max_seconds=5.0, handles=2)
        fps = resolved["fps"]
        max_frames = int(round(5.0 * fps))
        frames = []
        for segment in segments:
            length = segment["end_frame"] - segment["start_frame"] + 1
            self.assertLessEqual(length, max_frames, msg=segment)
            self.assertGreaterEqual(segment["start_frame"] - segment["render_start"], 0)
            self.assertLessEqual(segment["start_frame"] - segment["render_start"], 2)
            self.assertLessEqual(segment["render_end"] - segment["end_frame"], 2)
            frames.extend(range(segment["start_frame"], segment["end_frame"] + 1))
        self.assertEqual(frames, list(range(1, resolved["frame_count"] + 1)))
        # The 6 s beat cannot fit in one chunk.
        self.assertGreater(len(segments), 3)
        self.assertEqual(segments[0]["render_start"], 1)

    def test_episode_plan_covers_every_frame(self):
        resolved = resolve(load_yaml(SPEC))
        segments = plan_segments(resolved)
        frames = []
        max_frames = int(round(5.0 * resolved["fps"]))
        for segment in segments:
            length = segment["end_frame"] - segment["start_frame"] + 1
            self.assertLessEqual(length, max_frames, msg=segment["id"])
            self.assertGreaterEqual(segment["render_end"], segment["end_frame"])
            frames.extend(range(segment["start_frame"], segment["end_frame"] + 1))
        self.assertEqual(frames, list(range(1, resolved["frame_count"] + 1)))
        self.assertGreaterEqual(len(segments), 2)


class CacheKeyTest(unittest.TestCase):
    def test_a_beat_edit_rerenders_only_the_segments_that_sample_it(self):
        resolved = resolve(_spec([4.0, 4.0, 4.0, 4.0]))
        segments = plan_segments(resolved)
        code = "code"
        assets = "assets"
        keys = [
            segment_key(resolved, segment, code=code, assets=assets, samples=8, scale=1.0, image_format="png")
            for segment in segments
        ]
        edited = copy.deepcopy(resolved)
        target = segments[1]
        # Anchors sit on the old curve, outside the neighbor handle window,
        # so only this chunk's samples move.
        anchor = target["start_frame"] + 3
        bump = target["start_frame"] + 12
        # Stay more than two frames off the next key. A nearer key is a hard cut
        # and would change the neighbor's handle samples.
        restore = target["end_frame"] - 3
        self.assertLess(bump + 3, restore)
        old_anchor = channels_at(resolved, anchor)["vegetation"]
        old_restore = channels_at(resolved, restore)["vegetation"]
        keys_v = [(frame, value) for frame, value in edited["channels"]["vegetation"] if frame not in (anchor, bump, restore)]
        keys_v.extend([(anchor, old_anchor), (bump, 0.77), (restore, old_restore)])
        edited["channels"]["vegetation"] = sorted(keys_v)
        edited_keys = [
            segment_key(edited, segment, code=code, assets=assets, samples=8, scale=1.0, image_format="png")
            for segment in segments
        ]
        changed = [index for index, (before, after) in enumerate(zip(keys, edited_keys)) if before != after]
        self.assertEqual(changed, [1])

    def test_shared_inputs_rerender_every_segment(self):
        resolved = resolve(_spec([3.0, 3.0]))
        segments = plan_segments(resolved)
        before = [segment_key(resolved, segment, code="a", assets="b", samples=8, scale=1, image_format="png") for segment in segments]
        after_code = [segment_key(resolved, segment, code="z", assets="b", samples=8, scale=1, image_format="png") for segment in segments]
        moved = copy.deepcopy(resolved)
        moved["camera"] = {"location": [9, 9, 9], "target": [0, 0, 0], "lens": 40}
        after_camera = [segment_key(moved, segment, code="a", assets="b", samples=8, scale=1, image_format="png") for segment in segments]
        self.assertTrue(all(a != b for a, b in zip(before, after_code)))
        self.assertTrue(all(a != b for a, b in zip(before, after_camera)))

    def test_code_digest_tracks_file_bytes(self):
        root = Path(__file__).resolve().parents[1]
        first = code_digest([root / "engine" / "spec.py"])
        self.assertEqual(first, code_digest([root / "engine" / "spec.py"]))
        self.assertEqual(len(first), 64)


class ContinuityTest(unittest.TestCase):
    def _run(self, resolved, directory, render_fn, full=None, force=False):
        return run_segments(
            resolved,
            cache_dir=directory / "cache",
            assemble_dir=directory / "assembled",
            render_fn=render_fn,
            code="code",
            assets="assets",
            samples=4,
            scale=0.5,
            image_format="png",
            full_reference=full,
            force=force,
        )

    def test_boundary_frames_match_a_full_render_and_handles_are_dropped(self):
        resolved = resolve(_spec([3.0, 3.5, 4.0]))
        root = Path("/tmp/whatif_segments")
        if root.exists():
            import shutil

            shutil.rmtree(root)
        full = root / "full"
        _full(full, resolved)
        calls = []

        def render(segment, dest):
            calls.append(segment["id"])
            _writer(resolved)(segment, dest)

        manifest = self._run(resolved, root, render, full=full)
        self.assertTrue(manifest["overlaps_ok"])
        self.assertTrue(manifest["full_match"])
        self.assertEqual(len(calls), len(manifest["segments"]))
        assembled = root / "assembled"
        assembled_frames = set()
        for frame in range(1, resolved["frame_count"] + 1):
            path = assembled / frame_name(frame, "png")
            self.assertTrue(path.is_file(), msg=frame)
            self.assertEqual(path.read_bytes(), _pixel(resolved, frame))
            assembled_frames.add(frame)
        self.assertEqual(assembled_frames, set(range(1, resolved["frame_count"] + 1)))
        for segment in manifest["entries"]:
            if segment["render_start"] < segment["start_frame"]:
                handle = segment["render_start"]
                self.assertTrue((Path(segment["cache"]) / frame_name(handle, "png")).is_file())
        # A second pass reuses the cache.
        calls.clear()
        again = self._run(resolved, root, render, full=full)
        self.assertEqual(calls, [])
        self.assertTrue(all(segment["cached"] for segment in again["segments"]))

    def test_a_segment_local_seed_fails_the_boundary_check(self):
        resolved = resolve(_spec([3.0, 3.0]))
        root = Path("/tmp/whatif_segments_bad")
        if root.exists():
            import shutil

            shutil.rmtree(root)

        def render(segment, dest):
            dest.mkdir(parents=True, exist_ok=True)
            for frame in range(segment["render_start"], segment["render_end"] + 1):
                blob = f"{segment['id']}|{frame}|{frame_seed(frame)}".encode()
                (dest / frame_name(frame, "png")).write_bytes(blob)

        with self.assertRaises(SegmentContinuityError):
            self._run(resolved, root, render)

    def test_assembly_is_one_contiguous_sequence(self):
        resolved = resolve(_spec([2.5, 2.5]))
        root = Path("/tmp/whatif_segments_assemble")
        if root.exists():
            import shutil

            shutil.rmtree(root)
        manifest = self._run(resolved, root, _writer(resolved))
        kept = []
        for segment in manifest["entries"]:
            kept.extend(range(segment["start_frame"], segment["end_frame"] + 1))
        self.assertEqual(kept, list(range(1, resolved["frame_count"] + 1)))
        names = sorted(path.name for path in (root / "assembled").glob("f_*.png"))
        self.assertEqual(names[0], "f_0001.png")
        self.assertEqual(names[-1], frame_name(resolved["frame_count"], "png"))
        self.assertEqual(len(names), resolved["frame_count"])

    def test_full_reference_flags_a_different_pixel(self):
        resolved = resolve(_spec([3.0, 3.0]))
        root = Path("/tmp/whatif_segments_ref")
        if root.exists():
            import shutil

            shutil.rmtree(root)
        full = root / "full"
        _full(full, resolved)
        # Flip one boundary pixel in the reference after a matching render by
        # checking the helper directly on a tampered file.
        manifest = self._run(resolved, root, _writer(resolved), full=full)
        segment = manifest["entries"][0]
        reference = full / frame_name(segment["end_frame"], "png")
        reference.write_bytes(b"not the same frame")
        mismatches = verify_boundaries_against_full(
            manifest["entries"],
            lambda item: item["cache"],
            full,
            "png",
        )
        self.assertTrue(any(item["frame"] == segment["end_frame"] for item in mismatches))
        self.assertNotEqual(file_hash(reference), file_hash(Path(segment["cache"]) / frame_name(segment["end_frame"], "png")))

    def test_ffmpeg_command_is_one_frame_accurate_encode(self):
        command = ffmpeg_command(
            Path("/tmp/assembled"),
            Path("/tmp/episode.mp4"),
            fps=30,
            frame_count=1470,
            ext="png",
        )
        self.assertEqual(command[0], "ffmpeg")
        self.assertIn("-framerate", command)
        self.assertIn("30", command)
        self.assertIn("/tmp/assembled/f_%04d.png", command)
        self.assertIn("1470", command)
        self.assertEqual(command[-1], "/tmp/episode.mp4")

    def test_ffmpeg_writes_one_file_for_the_sequence(self):
        if shutil.which("ffmpeg") is None:
            self.skipTest("ffmpeg is not installed")
        from PIL import Image

        root = Path("/tmp/whatif_segments_encode")
        if root.exists():
            shutil.rmtree(root)
        root.mkdir()
        for frame, color in ((1, (20, 40, 60)), (2, (80, 100, 120))):
            Image.new("RGB", (16, 32), color).save(root / frame_name(frame, "png"))
        dest = root / "episode.mp4"
        encode_sequence(root, dest, fps=30, frame_count=2, ext="png")
        self.assertTrue(dest.is_file())
        self.assertGreater(dest.stat().st_size, 100)


class AssembleHelperTest(unittest.TestCase):
    def test_assemble_refuses_a_gap(self):
        root = Path("/tmp/whatif_segments_gap")
        if root.exists():
            import shutil

            shutil.rmtree(root)
        cache = root / "one"
        cache.mkdir(parents=True)
        (cache / "f_0001.png").write_bytes(b"a")
        segment = {
            "start_frame": 1,
            "end_frame": 1,
            "cache": str(cache),
        }
        with self.assertRaises(RuntimeError):
            assemble([segment], lambda item: item["cache"], root / "out", "png", frame_count=2)


if __name__ == "__main__":
    unittest.main()
