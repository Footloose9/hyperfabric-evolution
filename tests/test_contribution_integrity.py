"""Independent falsifiers for the limited PR changed-object integrity guard."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contribution_integrity import (  # noqa: E402
    verify_pr_diff, _exact_allowlist, _exact_path_admitted, _path_is_safe,
)


def git(root: Path, *args: str) -> str:
    p = subprocess.run(["git", *args], cwd=root, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.stdout.decode("utf-8").strip()


class ActualGitObjectAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="public_pr_integrity_")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Fictional Test Author")
        git(self.root, "config", "user.email", "test@example.invalid")
        (self.root / "docs").mkdir()
        (self.root / ".gitignore").write_text(
            "# Deny by default\n*\n!.gitignore\n!docs/\n!docs/ok.txt\n", encoding="utf-8")
        git(self.root, "add", "-f", ".gitignore")
        git(self.root, "commit", "-qm", "base")
        self.base = git(self.root, "rev-parse", "HEAD")

    def commit(self, path="docs/ok.txt", content="hello public evidence\n", force=True):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
        if force:
            git(self.root, "add", "-f", path)
        else:
            git(self.root, "add", "--", path)
        git(self.root, "commit", "-qm", "candidate")
        return verify_pr_diff(self.root, self.base, "HEAD")

    def test_expected_exact_public_new_text_passes(self):
        self.assertEqual(self.commit(), [])

    def test_unlisted_file_stays_rejected_even_if_git_forced_it(self):
        self.assertIn("excluded", " ".join(self.commit("docs/private.txt")))

    def test_binary_byte_is_not_public_text(self):
        self.assertIn("NUL/binary", " ".join(self.commit(content=b"one\x00two")))

    def test_oversized_new_file_is_rejected(self):
        self.assertIn("exceeds", " ".join(self.commit(content="a" * 210_000)))

    def test_obvious_private_key_marker_is_rejected(self):
        # Intentionally fictional marker: no actual key or secret material.
        synthetic_fixture_marker = "-----BEGIN " + "PRIVATE KEY-----\nfictional\n"
        self.assertIn("secret marker", " ".join(self.commit(content=synthetic_fixture_marker)))

    def test_executable_bit_is_rejected(self):
        file = self.root / "docs" / "ok.txt"
        file.write_text("echo synthetic\n", encoding="utf-8")
        git(self.root, "add", "-f", "docs/ok.txt")
        git(self.root, "update-index", "--chmod=+x", "docs/ok.txt")
        git(self.root, "commit", "-qm", "candidate")
        self.assertIn("unsupported file mode", " ".join(verify_pr_diff(self.root, self.base)))

    def test_symlink_is_rejected(self):
        path = self.root / "docs" / "ok.txt"
        try:
            os.symlink("../.gitignore", path)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unsupported on this runner")
        git(self.root, "add", "-f", "docs/ok.txt")
        git(self.root, "commit", "-qm", "candidate")
        self.assertIn("unsupported file mode", " ".join(verify_pr_diff(self.root, self.base)))

    def test_deletion_requires_manual_exception(self):
        self.assertEqual(self.commit(), [])
        self.base = git(self.root, "rev-parse", "HEAD")
        git(self.root, "rm", "docs/ok.txt")
        git(self.root, "commit", "-qm", "deletion")
        self.assertIn("deletion requires", " ".join(verify_pr_diff(self.root, self.base)))

    def test_existing_tracked_deletion_cannot_hide_behind_restoration(self):
        self.assertEqual(self.commit(), [])
        self.base = git(self.root, "rev-parse", "HEAD")
        git(self.root, "rm", "docs/ok.txt")
        git(self.root, "commit", "-qm", "transient tracked deletion")
        (self.root / "docs").mkdir(exist_ok=True)
        (self.root / "docs" / "ok.txt").write_text(
            "fictional changed public text\n", encoding="utf-8"
        )
        git(self.root, "add", "-f", "docs/ok.txt")
        git(self.root, "commit", "-qm", "restore path with benign update")
        self.assertIn(
            "historical deletion requires",
            " ".join(verify_pr_diff(self.root, self.base)),
        )

    def test_new_public_file_deletion_in_history_is_not_amnestied(self):
        self.assertEqual(self.commit(), [])
        git(self.root, "rm", "docs/ok.txt")
        git(self.root, "commit", "-qm", "transient deletion of new public file")
        (self.root / "docs").mkdir(exist_ok=True)
        (self.root / "docs" / "ok.txt").write_text(
            "hello public evidence\n", encoding="utf-8"
        )
        git(self.root, "add", "-f", "docs/ok.txt")
        git(self.root, "commit", "-qm", "restore original new file")
        self.assertIn(
            "historical deletion requires",
            " ".join(verify_pr_diff(self.root, self.base)),
        )

    def test_head_allowlist_not_dependent_on_runner_checkout(self):
        # The verifier accepts an explicit arbitrary head SHA; a local
        # checkout of the earlier base must not change that head's policy.
        (self.root / ".gitignore").write_text(
            "*\n!.gitignore\n!docs/\n!docs/ok.txt\n!docs/candidate.txt\n",
            encoding="utf-8",
        )
        candidate = self.root / "docs" / "candidate.txt"
        candidate.write_text("fictional source evidence\n", encoding="utf-8")
        git(self.root, "add", "--", ".gitignore", "docs/candidate.txt")
        git(self.root, "commit", "-qm", "atomic permitted public addition")
        candidate_head = git(self.root, "rev-parse", "HEAD")
        self.assertEqual(verify_pr_diff(self.root, self.base, candidate_head), [])
        git(self.root, "checkout", "--detach", "-q", self.base)
        actual = subprocess.run(
            ["git", "check-ignore", "-q", "--no-index", "--",
             "docs/candidate.txt"], cwd=self.root, check=False,
        )
        self.assertEqual(actual.returncode, 0)
        self.assertEqual(verify_pr_diff(self.root, self.base, candidate_head), [])

    def test_true_head_denied_path_stays_denied_with_permissive_worktree(self):
        candidate = self.root / "docs" / "candidate.txt"
        candidate.write_text("fictional forbidden content\n", encoding="utf-8")
        git(self.root, "add", "-f", "--", "docs/candidate.txt")
        git(self.root, "commit", "-qm", "unallowlisted introduction")
        denied_head = git(self.root, "rev-parse", "HEAD")
        (self.root / ".gitignore").write_text(
            "*\n!.gitignore\n!docs/\n!docs/ok.txt\n!docs/candidate.txt\n",
            encoding="utf-8",
        )
        git(self.root, "add", ".gitignore")
        git(self.root, "commit", "-qm", "late runner-only policy relaxation")
        current = subprocess.run(
            ["git", "check-ignore", "-q", "--no-index", "--",
             "docs/candidate.txt"], cwd=self.root, check=False,
        )
        self.assertEqual(current.returncode, 1)
        self.assertIn(
            "historical unallowlisted path",
            " ".join(verify_pr_diff(self.root, self.base, denied_head)),
        )

    def test_normal_multicommit_update_still_passes(self):
        self.assertEqual(self.commit(), [])
        (self.root / "docs" / "ok.txt").write_text(
            "allowed public update\n", encoding="utf-8"
        )
        git(self.root, "add", "docs/ok.txt")
        git(self.root, "commit", "-qm", "ordinary update")
        self.assertEqual(verify_pr_diff(self.root, self.base), [])


    def test_first_parent_merge_does_not_invent_old_base_deletions(self):
        # A feature commit may predate a harmless file added on the newer
        # base branch. Absence from the old feature tree is not a deletion.
        (self.root / ".gitignore").write_text(
            "*\n!.gitignore\n!docs/\n!docs/ok.txt\n!docs/peer.txt\n",
            encoding="utf-8",
        )
        git(self.root, "add", ".gitignore")
        git(self.root, "commit", "-qm", "shared policy base")
        common = git(self.root, "rev-parse", "HEAD")
        git(self.root, "checkout", "-qb", "feature")
        (self.root / "docs" / "ok.txt").write_text(
            "old feature fictional text\n", encoding="utf-8"
        )
        git(self.root, "add", "docs/ok.txt")
        git(self.root, "commit", "-qm", "feature predates peer")
        git(self.root, "checkout", "-qb", "upstream", common)
        (self.root / "docs").mkdir(exist_ok=True)
        (self.root / "docs" / "peer.txt").write_text(
            "new upstream fictional text\n", encoding="utf-8"
        )
        git(self.root, "add", "docs/peer.txt")
        git(self.root, "commit", "-qm", "upstream public addition")
        recent_base = git(self.root, "rev-parse", "HEAD")
        git(self.root, "checkout", "-q", "feature")
        git(self.root, "merge", "--no-ff", "-qm", "sync upstream", "upstream")
        self.assertEqual(verify_pr_diff(self.root, recent_base), [])


    def test_hidden_history_secret_is_not_hidden_by_later_deletion(self):
        # New public objects stay in Git even if the final PR tree no longer has them.
        historical = self.root / "docs" / "historical.txt"
        historical.write_text("-----BEGIN " + "PRIVATE KEY-----\nsynthetic\n", encoding="utf-8")
        git(self.root, "add", "-f", "docs/historical.txt")
        git(self.root, "commit", "-qm", "historical leak attempt")
        git(self.root, "rm", "docs/historical.txt")
        git(self.root, "commit", "-qm", "hide previous commit")
        issues = self.commit()
        self.assertIn("historical object contains secret marker", " ".join(issues))

    def test_hidden_history_binary_is_not_hidden_by_later_deletion(self):
        historical = self.root / "docs" / "historical.txt"
        historical.write_bytes(b"fictional\x00data")
        git(self.root, "add", "-f", "docs/historical.txt")
        git(self.root, "commit", "-qm", "historical binary")
        git(self.root, "rm", "docs/historical.txt")
        git(self.root, "commit", "-qm", "hide previous binary")
        self.assertIn("historical binary object", " ".join(self.commit()))

    def _transient_then_clean(self, path: str, content: bytes | str,
                              executable: bool = False, symlink: bool = False):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if symlink:
            try:
                os.symlink("../.gitignore", target)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unsupported on this runner")
        else:
            target.write_bytes(content if isinstance(content, bytes)
                               else content.encode("utf-8"))
        git(self.root, "add", "-f", path)
        if executable:
            git(self.root, "update-index", "--chmod=+x", path)
        git(self.root, "commit", "-qm", "transient object")
        git(self.root, "rm", "-f", path)
        git(self.root, "commit", "-qm", "delete transient object")
        return self.commit()

    def test_historical_symlink_cannot_be_hidden_in_clean_final_diff(self):
        issues = self._transient_then_clean("docs/transient.txt", "", symlink=True)
        self.assertIn("historical unsupported mode/type", " ".join(issues))

    def test_historical_executable_cannot_be_hidden_in_clean_final_diff(self):
        issues = self._transient_then_clean("docs/transient.txt", "synthetic", executable=True)
        self.assertIn("historical unsupported mode/type", " ".join(issues))

    def test_historical_unallowlisted_path_stays_disallowed(self):
        issues = self._transient_then_clean("docs/hidden.txt", "fictional")
        self.assertIn("historical unallowlisted path", " ".join(issues))




    def test_historical_nested_gitignore_cannot_amnesty_forced_file(self):
        # The public guard's policy is root-only, but Git also applies
        # a tracked nested .gitignore. A later nested exception cannot
        # retroactively authorize a file introduced while ignored.
        (self.root / ".gitignore").write_text(
            "*\n!.gitignore\n!docs/\n!docs/.gitignore\n"
            "!docs/ok.txt\n!docs/candidate.txt\n",
            encoding="utf-8",
        )
        nested = self.root / "docs" / ".gitignore"
        nested.write_text("candidate.txt\n", encoding="utf-8")
        git(self.root, "add", "--", ".gitignore", "docs/.gitignore")
        git(self.root, "commit", "-qm", "synthetic nested baseline")
        base = git(self.root, "rev-parse", "HEAD")
        candidate = self.root / "docs" / "candidate.txt"
        candidate.write_text("fictional text only\n", encoding="utf-8")
        denied = subprocess.run(
            ["git", "check-ignore", "-q", "--no-index", "--",
             "docs/candidate.txt"], cwd=self.root, check=False,
        )
        self.assertEqual(denied.returncode, 0)
        git(self.root, "add", "-f", "--", "docs/candidate.txt")
        git(self.root, "commit", "-qm", "historically ignored addition")
        nested.write_text("# candidate permitted later\n", encoding="utf-8")
        git(self.root, "add", "--", "docs/.gitignore")
        git(self.root, "commit", "-qm", "later nested exception")
        admitted = subprocess.run(
            ["git", "check-ignore", "-q", "--no-index", "--",
             "docs/candidate.txt"], cwd=self.root, check=False,
        )
        self.assertEqual(admitted.returncode, 1)
        self.assertIn(
            "nested .gitignore",
            " ".join(verify_pr_diff(self.root, base, "HEAD")),
        )

    def test_root_only_literal_allowlist_still_passes(self):
        # Ordinary atomic root allowlisting without nested ignore files
        # must remain a valid public contribution.
        (self.root / ".gitignore").write_text(
            "*\n!.gitignore\n!docs/\n!docs/ok.txt\n"
            "!docs/candidate.txt\n", encoding="utf-8",
        )
        git(self.root, "add", "--", ".gitignore")
        git(self.root, "commit", "-qm", "first permit fictional path")
        candidate = self.root / "docs" / "candidate.txt"
        candidate.write_text("independently invented public fixture\n",
                             encoding="utf-8")
        git(self.root, "add", "--", "docs/candidate.txt")
        git(self.root, "commit", "-qm", "valid subsequent public addition")
        self.assertEqual(verify_pr_diff(self.root, self.base, "HEAD"), [])

    def test_historical_forced_path_is_not_amnestied_by_later_exception(self):
        # A later .gitignore exception cannot retroactively authorize a file
        # that entered Git while the exact path was still denied.
        candidate = self.root / "docs" / "candidate.txt"
        candidate.write_text("fictional research text\n", encoding="utf-8")
        git(self.root, "add", "-f", "docs/candidate.txt")
        git(self.root, "commit", "-qm", "unsafe historical admission")
        prior = subprocess.run(
            ["git", "check-ignore", "-q", "--no-index", "--",
             "docs/candidate.txt"], cwd=self.root, check=False,
        )
        self.assertEqual(prior.returncode, 0)
        (self.root / ".gitignore").write_text(
            "*\n!.gitignore\n!docs/\n!docs/ok.txt\n!docs/candidate.txt\n",
            encoding="utf-8",
        )
        git(self.root, "add", "--", ".gitignore")
        git(self.root, "commit", "-qm", "late retroactive exception")
        current = subprocess.run(
            ["git", "check-ignore", "-q", "--no-index", "--",
             "docs/candidate.txt"], cwd=self.root, check=False,
        )
        self.assertEqual(current.returncode, 1)
        self.assertIn(
            "historical unallowlisted path",
            " ".join(verify_pr_diff(self.root, self.base, "HEAD")),
        )

    def test_historical_path_is_valid_when_exception_precedes_first_add(self):
        (self.root / ".gitignore").write_text(
            "*\n!.gitignore\n!docs/\n!docs/ok.txt\n!docs/candidate.txt\n",
            encoding="utf-8",
        )
        git(self.root, "add", "--", ".gitignore")
        git(self.root, "commit", "-qm", "valid prior exception")
        candidate = self.root / "docs" / "candidate.txt"
        candidate.write_text("fictional public evidence\n", encoding="utf-8")
        git(self.root, "add", "--", "docs/candidate.txt")
        git(self.root, "commit", "-qm", "allowlisted addition")
        self.assertEqual(verify_pr_diff(self.root, self.base, "HEAD"), [])

    def test_unicode_line_separator_cannot_forge_deny_all(self):
        # Python str.splitlines() recognizes U+2028 and U+0085, while Git
        # reads .gitignore records as physical lines. Never normalize them
        # into a synthetic valid '*' policy.
        for label, separator in (
            ("unicode-line-separator", "\u2028"),
            ("unicode-next-line", "\u0085"),
        ):
            with self.subTest(label=label):
                git(self.root, "reset", "--hard", self.base)
                (self.root / "docs").mkdir(exist_ok=True)
                malformed = "*" + separator + "!.gitignore\n!docs/\n!docs/ok.txt\n"
                (self.root / ".gitignore").write_text(malformed, encoding="utf-8")
                (self.root / "docs" / "private.txt").write_text(
                    "fictional review-only text\n", encoding="utf-8"
                )
                git_decision = subprocess.run(
                    ["git", "check-ignore", "-q", "--no-index", "--",
                     "docs/private.txt"], cwd=self.root, check=False,
                )
                self.assertEqual(git_decision.returncode, 1)
                git(self.root, "add", "--", ".gitignore", "docs/private.txt")
                git(self.root, "commit", "-qm", "synthetic Unicode separator")
                self.assertIn(
                    "whitespace",
                    " ".join(verify_pr_diff(self.root, self.base)),
                )

    def test_hidden_unicode_controls_cannot_enter_allowlist_or_path(self):
        """Git filenames and exact exceptions must reject invisible controls."""
        for label, ch in (
            ("zero width", chr(0x200B)),
            ("right-to-left override", chr(0x202E)),
            ("escape control", chr(0x1B)),
        ):
            with self.subTest(label=label):
                name = f"docs/f{ch}ile.txt"
                raw = (f"*\n!.gitignore\n!docs/\n!{name}\n").encode("utf-8")
                self.assertIn("Unicode control", " ".join(_exact_allowlist(raw)))
                self.assertFalse(_path_is_safe(name))
                self.assertFalse(_exact_path_admitted(raw, name))

    def test_visible_non_ascii_literal_filename_stays_admissible(self):
        """The guard rejects control categories, not ordinary international text."""
        name = "docs/café.txt"
        raw = (f"*\n!.gitignore\n!docs/\n!{name}\n").encode("utf-8")
        self.assertEqual(_exact_allowlist(raw), [])
        self.assertTrue(_path_is_safe(name))
        self.assertTrue(_exact_path_admitted(raw, name))

    def test_only_physical_newlines_define_ignore_rules(self):
        self.assertEqual(
            _exact_allowlist(b"*\n!.gitignore\n!docs/\n!docs/ok.txt\n"), []
        )
        self.assertEqual(
            _exact_allowlist(b"*\r\n!.gitignore\r\n!docs/\r\n!docs/ok.txt\r\n"), []
        )
        for separator in ("\u2028", "\u0085", "\v", "\f", "\r"):
            with self.subTest(separator=repr(separator)):
                malformed = ("*" + separator + "!.gitignore\n"
                             "!docs/\n!docs/ok.txt\n").encode("utf-8")
                self.assertIn("whitespace", " ".join(_exact_allowlist(malformed)))

    def test_leading_whitespace_cannot_defeat_deny_all(self):
        (self.root / ".gitignore").write_text(
            " *\n!.gitignore\n!docs/\n!docs/ok.txt\n", encoding="utf-8")
        (self.root / "docs" / "private.txt").write_text("fictional\n")
        git(self.root, "add", "-f", ".gitignore")
        git(self.root, "add", "--", "docs/private.txt")
        git(self.root, "commit", "-qm", "unsafe ignore whitespace")
        self.assertIn("noncanonical whitespace", " ".join(verify_pr_diff(self.root, self.base)))

    def test_historical_oversized_added_text_cannot_be_hidden_by_deletion(self):
        path = self.root / "docs" / "ok.txt"
        path.write_bytes(b"x" * 210_001)
        git(self.root, "add", "-f", "docs/ok.txt")
        git(self.root, "commit", "-qm", "historical oversized new object")
        git(self.root, "rm", "-f", "docs/ok.txt")
        git(self.root, "commit", "-qm", "remove oversized object")
        self.assertIn("historical added text exceeds", " ".join(self.commit()))

    def test_historical_weak_allowlist_is_rejected_even_if_restored(self):
        original = (self.root / ".gitignore").read_text(encoding="utf-8")
        (self.root / ".gitignore").write_text(
            " *\n!.gitignore\n!docs/\n!docs/ok.txt\n", encoding="utf-8")
        git(self.root, "add", "-f", ".gitignore")
        git(self.root, "commit", "-qm", "historical weakened denyall")
        (self.root / ".gitignore").write_text(original, encoding="utf-8")
        git(self.root, "add", "-f", ".gitignore")
        git(self.root, "commit", "-qm", "restore ignore rules")
        self.assertIn("historical ignore rule", " ".join(self.commit()))

    def test_deny_all_cannot_be_removed(self):
        self.assertIn("deny-all", " ".join(_exact_allowlist(b"!docs/\n")))

    def test_wildcard_exception_is_rejected(self):
        self.assertIn("non-exact", " ".join(_exact_allowlist(b"*\n!docs/\n!**/*.txt\n")))

    def test_path_traversal_exception_is_rejected(self):
        self.assertIn("non-exact", " ".join(_exact_allowlist(b"*\n!docs/../secret\n")))

    def test_tainted_changed_ignore_fails_pr_check(self):
        (self.root / ".gitignore").write_text("!**\n", encoding="utf-8")
        git(self.root, "add", "-f", ".gitignore")
        git(self.root, "commit", "-qm", "weaken-default")
        self.assertIn("deny-all", " ".join(verify_pr_diff(self.root, self.base)))


if __name__ == "__main__":
    unittest.main()
