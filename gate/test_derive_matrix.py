#!/usr/bin/env python3
"""Unit tests for the packs: key parser in derive-matrix.py.

The parser is the load-bearing part of the gate: a language key it silently
drops becomes zero coverage for that language while the gate stays green. These
tests pin the shapes YAML allows (comments, inline values/anchors, quotes,
empty keys) so that regression can't reintroduce a silent drop.

Run: python3 gate/test_derive_matrix.py
"""
import importlib.util
import os
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("dm", os.path.join(HERE, "derive-matrix.py"))
dm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dm)


def keys(yaml_text):
    with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False) as fh:
        fh.write(yaml_text)
        path = fh.name
    try:
        return dm.packs_keys(path)
    finally:
        os.unlink(path)


BASE_TAIL = "query-filters:\n  - exclude:\n      id: js/x\n"


class PacksKeyParser(unittest.TestCase):
    def test_single_key(self):
        self.assertEqual(keys("packs:\n  javascript:\n    - a@1\n" + BASE_TAIL), ["javascript"])

    def test_two_keys(self):
        self.assertEqual(
            keys("packs:\n  javascript:\n    - a@1\n  actions:\n    - b@1\n" + BASE_TAIL),
            ["javascript", "actions"],
        )

    def test_trailing_comment_key_not_dropped(self):
        # The regression the reviewer caught: `actions:  # note` must still parse.
        self.assertEqual(
            keys("packs:\n  javascript:\n    - a@1\n  actions:  # dormant\n    - b@1\n" + BASE_TAIL),
            ["javascript", "actions"],
        )

    def test_inline_anchor_value(self):
        self.assertEqual(keys("packs:\n  javascript: &js\n    - a@1\n" + BASE_TAIL), ["javascript"])

    def test_quoted_key(self):
        self.assertEqual(keys("packs:\n  'javascript':\n    - a@1\n" + BASE_TAIL), ["javascript"])

    def test_space_before_colon(self):
        self.assertEqual(keys("packs:\n  javascript :\n    - a@1\n" + BASE_TAIL), ["javascript"])

    def test_empty_key_still_listed(self):
        # Strict behaviour: you cannot add the key without the leg running.
        self.assertEqual(
            keys("packs:\n  javascript:\n  actions:\n" + BASE_TAIL), ["javascript", "actions"]
        )

    def test_comment_lines_ignored(self):
        self.assertEqual(
            keys("packs:\n  # a comment\n  javascript:\n    - a@1\n" + BASE_TAIL), ["javascript"]
        )

    def test_block_ends_at_next_toplevel(self):
        # A key under a later top-level mapping must not leak into packs keys.
        self.assertEqual(
            keys("packs:\n  javascript:\n    - a@1\nquery-filters:\n  - exclude:\n      id: js/x\n"),
            ["javascript"],
        )

    def test_no_packs_block(self):
        self.assertEqual(keys("name: x\n" + BASE_TAIL), [])


if __name__ == "__main__":
    unittest.main()
