"""Independent falsifiers for the limited PR changed-object integrity guard."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contribution_integrity import verify_pr_diff, _exact_allowlist  # noqa: E402


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
        secret = "-----BEGIN " + "PRIVATE KEY-----\nfictional\n"
        self.assertIn("secret marker", " ".join(self.commit(content=secret)))

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
