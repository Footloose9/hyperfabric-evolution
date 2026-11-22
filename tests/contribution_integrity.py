"""Public PR changed-file guard; not a rights, identity, or security approval.

Standard-library only. This checks Git objects, not self-reported PR claims.
On GitHub Actions it should run using the version from the protected base
commit, not a changeable copy supplied by the pull request.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess

MAX_TEXT_BYTES = 512_000
MAX_NEW_FILE_BYTES = 200_000
SECRET_MARKERS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(rb"\bghp_[A-Za-z0-9]{30,}\b"),
    re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{25,}\b"),
)


def _git(root: Path, *args: str, allowed=(0,)) -> subprocess.CompletedProcess[bytes]:
    proc = subprocess.run(
        ["git", *args], cwd=root, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if proc.returncode not in allowed:
        raise RuntimeError(f"git {' '.join(args[:2])} failed: {proc.stderr[:180]!r}")
    return proc


def _exact_allowlist(raw: bytes) -> list[str]:
    """Reject changed allowlists that disable the deny-all staging default."""
    try:
        # Git separates ignore rules at LF (optionally CRLF), not at
        # Unicode line/paragraph separators or Python's vertical controls.
        # str.splitlines() can fabricate a valid '*' rule Git never saw.
        lines = raw.decode("utf-8").split("\n")
    except UnicodeError:
        return [".gitignore is not UTF-8"]
    errors: list[str] = []
    rules: list[str] = []
    for i, v in enumerate(lines):
        if i < len(lines) - 1 and v.endswith("\r"):
            v = v[:-1]  # normalize CRLF only, never lone CR or Unicode NL
        if not v:
            continue
        if v.startswith("#"):
            continue
        # Git does not normalize leading blanks like Python str.strip().
        # A rule " *" is not the global deny rule "*"; rejecting instead
        # of trimming is essential for a fail-closed allowlist.
        if v != v.strip() or any(ch.isspace() for ch in v):
            errors.append("noncanonical whitespace in .gitignore rule")
            continue
        rules.append(v)
    if not rules or rules[0] != "*":
        errors.append(".gitignore must start with a deny-all '*' rule")
    for v in rules[1:]:
        if not v.startswith("!"):
            errors.append(f"unexpected ignore rule: {v[:70]}")
            continue
        path = v[1:]
        bits = path.rstrip("/").split("/")
        if (not path or path.startswith("/") or "\\" in path
                or any(c in path for c in "*?[]")
                or any(p in ("", ".", "..") for p in bits)):
            errors.append(f"non-exact staging exception: {v[:70]}")
    return errors



def _exact_path_admitted(raw_ignore: bytes, path: str) -> bool:
    """Conservatively require each historical file and ancestor to be named.

    The public staging policy is restricted to a top-level deny-all '*' and
    literal '!' exceptions. Unlike git check-ignore in the current worktree,
    this predicate evaluates the exact historical root .gitignore blob.
    """
    if _exact_allowlist(raw_ignore) or not _path_is_safe(path):
        return False
    active = set()
    for raw_line in raw_ignore.decode("utf-8").split("\n"):
        line = raw_line[:-1] if raw_line.endswith("\r") else raw_line
        if line.startswith("!"):
            active.add(line[1:])
    parts = path.split("/")
    if path not in active:
        return False
    return all("/".join(parts[:i]) + "/" in active
               for i in range(1, len(parts)))

def _path_is_safe(path: str) -> bool:
    segments = path.split("/")
    return bool(path and not path.startswith("/") and "\\" not in path
                and all(part not in ("", ".", "..", ".git") for part in segments))


def _tree_entries(root: Path, revision: str) -> dict[str, tuple[bytes, bytes, bytes]]:
    """Read a Git commit's complete tree; do not trust a clean final diff."""
    tree: dict[str, tuple[bytes, bytes, bytes]] = {}
    for row in _git(root, "ls-tree", "-r", "-z", revision).stdout.split(b"\0"):
        if not row:
            continue
        metadata, sep, raw_path = row.partition(b"\t")
        parts = metadata.split()
        if not sep or len(parts) != 3:
            raise RuntimeError("malformed historical Git tree entry")
        try:
            path = raw_path.decode("utf-8")
        except UnicodeError as exc:
            raise RuntimeError("non-UTF8 historical Git path") from exc
        if not _path_is_safe(path):
            raise RuntimeError("unsafe historical Git path")
        if path in tree:
            raise RuntimeError("duplicated historical Git tree entry")
        tree[path] = (parts[0], parts[1], parts[2])
        if len(tree) > 4096:
            raise RuntimeError("historical Git tree exceeds 4096-entry audit budget")
    return tree


def verify_pr_diff(root: Path, base: str, head: str = "HEAD") -> list[str]:
    """Inspect actual Git diff and tree objects; fail closed on uncertain types."""
    root = Path(root).resolve()
    _git(root, "rev-parse", "--verify", "--end-of-options", base)
    _git(root, "rev-parse", "--verify", "--end-of-options", head)
    raw = _git(root, "diff", "--no-renames", "--name-status", "-z", base, head).stdout
    fields = raw.rstrip(b"\0").split(b"\0") if raw else []
    if not fields:
        return ["empty PR diff: no demonstrable changed paths"]
    if len(fields) % 2:
        return ["malformed Git name-status output"]
    errors: list[str] = []
    changed_ignore = False
    for i in range(0, len(fields), 2):
        status = fields[i].decode("ascii", "replace")
        try:
            path = fields[i + 1].decode("utf-8")
        except UnicodeError:
            errors.append("non-UTF8 changed path")
            continue
        if not _path_is_safe(path):
            errors.append(f"unsafe changed path: {path!r}")
            continue
        if path == ".gitignore":
            changed_ignore = True
        if status.startswith("D"):
            errors.append(f"deletion requires explicit bounded exception: {path}")
            continue
        if status[0] not in ("A", "M", "T"):
            errors.append(f"unsupported change kind {status}: {path}")
            continue
        row = _git(root, "ls-tree", "-z", head, "--", path).stdout
        if not row or row.count(b"\0") != 1:
            errors.append(f"missing/ambiguous tree entry: {path}")
            continue
        meta = row.split(b"\t", 1)[0].split()
        if len(meta) != 3 or meta[0] != b"100644" or meta[1] != b"blob":
            errors.append(f"unsupported file mode/type (symlink, executable, submodule): {path}")
            continue
        size = int(_git(root, "cat-file", "-s", meta[2].decode("ascii")).stdout)
        limit = MAX_NEW_FILE_BYTES if status.startswith("A") else MAX_TEXT_BYTES
        if size > limit:
            errors.append(f"changed text exceeds {limit} bytes: {path}")
            continue
        content = _git(root, "cat-file", "blob", meta[2].decode("ascii")).stdout
        if b"\0" in content:
            errors.append(f"NUL/binary content: {path}")
        try:
            content.decode("utf-8")
        except UnicodeError:
            errors.append(f"invalid UTF-8 content: {path}")
        if any(pattern.search(content) for pattern in SECRET_MARKERS):
            errors.append(f"high-confidence secret marker: {path}")
        if status.startswith("A"):
            ignore = _git(root, "check-ignore", "-q", "--no-index", "--", path,
                          allowed=(0, 1))
            if ignore.returncode == 0:
                errors.append(f"new path excluded by public .gitignore: {path}")
    if changed_ignore:
        raw_ignore = _git(root, "show", f"{head}:.gitignore").stdout
        errors.extend(_exact_allowlist(raw_ignore))
    # A final-tree diff cannot see a secret briefly committed and later removed.
    # Scan every newly reachable Git blob, including discarded historical blobs.
    history = _git(root, "rev-list", "--objects", f"{base}..{head}").stdout.splitlines()
    if len(history) > 1024:
        errors.append("PR history exceeds bounded 1024-object audit budget")
        return errors
    seen: set[str] = set()
    for row in history:
        object_id, _, raw_path = row.partition(b" ")
        sha = object_id.decode("ascii")
        if sha in seen:
            continue
        seen.add(sha)
        kind = _git(root, "cat-file", "-t", sha).stdout.strip()
        if kind == b"commit":
            # Commit-message content is public too; inspect high-confidence markers.
            commit = _git(root, "cat-file", "commit", sha).stdout
            if any(pattern.search(commit) for pattern in SECRET_MARKERS):
                errors.append(f"historical commit contains secret marker: {sha[:12]}")
            continue
        if kind != b"blob":
            continue
        name = raw_path.decode("utf-8", "replace")[:110] or "unnamed blob"
        size = int(_git(root, "cat-file", "-s", sha).stdout)
        if size > MAX_TEXT_BYTES:
            errors.append(f"historical object exceeds text limit: {name} ({sha[:12]})")
            continue
        content = _git(root, "cat-file", "blob", sha).stdout
        if b"\0" in content:
            errors.append(f"historical binary object: {name} ({sha[:12]})")
        try:
            content.decode("utf-8")
        except UnicodeError:
            errors.append(f"historical invalid UTF-8 object: {name} ({sha[:12]})")
        if any(pattern.search(content) for pattern in SECRET_MARKERS):
            errors.append(f"historical object contains secret marker: {name} ({sha[:12]})")
    # A clean end-state cannot prove intermediate commits lacked links,
    # executable objects or non-public filenames. Examine each new commit's
    # *tree entry modes and paths*, not only blobs/commit messages.
    commit_ids = _git(root, "rev-list", f"{base}..{head}").stdout.splitlines()
    if len(commit_ids) > 64:
        errors.append("PR exceeds bounded 64-commit historical tree audit")
        return errors
    base_tree = _tree_entries(root, base)
    # Bind each historical new path to the *same commit's* root policy.
    # Cache by blob identity to keep the bounded history audit efficient.
    policy_by_blob: dict[bytes, bytes] = {}
    for raw_commit in commit_ids:
        commit_sha = raw_commit.decode("ascii")
        current_tree = _tree_entries(root, commit_sha)
        ignore_entry = current_tree.get(".gitignore")
        if ignore_entry is None or ignore_entry[1] != b"blob":
            errors.append(f"historical missing .gitignore: {commit_sha[:12]}")
            continue
        ignore_blob = ignore_entry[2]
        if ignore_blob not in policy_by_blob:
            policy_by_blob[ignore_blob] = _git(
                root, "cat-file", "blob", ignore_blob.decode("ascii")
            ).stdout
        raw_ignore = policy_by_blob[ignore_blob]
        if base_tree.get(".gitignore") != ignore_entry:
            for issue in _exact_allowlist(raw_ignore):
                errors.append(f"historical ignore rule: {issue} ({commit_sha[:12]})")
        for path, entry in current_tree.items():
            if base_tree.get(path) == entry:
                continue
            if entry[0] != b"100644" or entry[1] != b"blob":
                errors.append(f"historical unsupported mode/type: {path} ({commit_sha[:12]})")
            if path not in base_tree:
                if entry[1] == b"blob":
                    size = int(_git(root, "cat-file", "-s", entry[2].decode("ascii")).stdout)
                    if size > MAX_NEW_FILE_BYTES:
                        errors.append(f"historical added text exceeds {MAX_NEW_FILE_BYTES} bytes: {path} ({commit_sha[:12]})")
                if not _exact_path_admitted(raw_ignore, path):
                    errors.append(f"historical unallowlisted path: {path} ({commit_sha[:12]})")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Limited public-only PR diff check")
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--repo", default=".")
    args = parser.parse_args()
    try:
        issues = verify_pr_diff(Path(args.repo), args.base, args.head)
    except (RuntimeError, ValueError) as exc:
        print(f"HOLD: unable to inspect exact Git objects: {exc}")
        return 1
    if issues:
        for issue in issues:
            print("HOLD:", issue)
        return 1
    print("PASS: Git object/path hygiene only. NOT provenance, rights, human review, or release clearance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
