"""Offline Pages source contract and opt-in public deployment readback.

Default unittest discovery makes NO network requests. To perform three bounded
public GET requests intentionally, run this file with --probe and a commit SHA.
Byte identity is not proof that a whole commit has been deployed.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_BASE = "https://footloose9.github.io/hyperfabric-evolution/"
PUBLIC_API = "https://api.github.com/repos/Footloose9/hyperfabric-evolution/"
ASSETS = ("index.html", "site.css", "site.js")
MAX_BYTES = 512 * 1024
COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")


class LocalHTMLReferences(HTMLParser):
    """Reads only static HTML element attributes, with no script execution."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.fragments: set[str] = set()
        self.stylesheets: set[str] = set()
        self.scripts: set[str] = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "a" and a.get("href", "").startswith("#") and a["href"] != "#":
            self.fragments.add(a["href"][1:])
        if tag == "link" and a.get("rel") == "stylesheet":
            self.stylesheets.add(a.get("href", ""))
        if tag == "script" and a.get("src") is not None:
            self.scripts.add(a["src"])


def source_contract_errors(html: str, file_exists) -> list[str]:
    """Deterministic local checks; caller supplies filesystem predicate."""
    parser = LocalHTMLReferences()
    parser.feed(html)
    problems = []
    for required, present in (("site.css", parser.stylesheets),
                              ("site.js", parser.scripts)):
        if required not in present:
            problems.append("MISSING_REFERENCED_ASSET:" + required)
        elif not file_exists(required):
            problems.append("MISSING_ASSET_FILE:" + required)
    for anchor in sorted(parser.fragments - parser.ids):
        problems.append("BROKEN_LOCAL_ANCHOR:" + anchor)
    for src in sorted(parser.scripts | parser.stylesheets):
        if src.startswith(("http:", "https:", "//")):
            problems.append("EXTERNAL_EXECUTABLE_OR_STYLESHEET:" + src)
        elif not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", src):
            problems.append("UNBOUNDED_LOCAL_ASSET_PATH:" + src)
    return problems


def public_url(asset: str) -> str:
    if asset not in ASSETS:
        raise ValueError("ASSET_NOT_ALLOWLISTED")
    return PUBLIC_BASE + asset


def assess_readback(expected: bytes, received: bytes, *,
                    http_status: int, requested_url: str,
                    final_url: str) -> dict[str, str]:
    """Assesses published bytes without claiming whole-commit currentness."""
    if http_status != 200:
        return {"status": "HTTP_NOT_OK"}
    if final_url != requested_url:
        return {"status": "UNEXPECTED_REDIRECT"}
    if len(received) > MAX_BYTES:
        return {"status": "RESPONSE_SIZE_EXCEEDED"}
    if len(expected) > MAX_BYTES:
        return {"status": "EXPECTED_ASSET_TOO_LARGE"}
    if expected != received:
        return {"status": "ASSET_BYTES_MISMATCH"}
    return {"status": "ASSET_BYTES_MATCH", "sha256": sha256(received).hexdigest()}


def pinned_source_bytes(commit: str, asset: str) -> bytes:
    if not COMMIT_RE.fullmatch(commit):
        raise ValueError("INVALID_COMMIT_SHA")
    public_url(asset)
    process = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{commit}:docs/{asset}"],
        capture_output=True, timeout=8, check=False,
    )
    if process.returncode != 0:
        raise ValueError("SOURCE_COMMIT_OR_ASSET_NOT_FOUND")
    if len(process.stdout) > MAX_BYTES:
        raise ValueError("EXPECTED_ASSET_TOO_LARGE")
    return process.stdout


class NoRedirect(HTTPRedirectHandler):
    """Prevent a public verifier GET from following another URL."""

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def live_asset_bytes(url: str) -> tuple[int, str, bytes]:
    # Called only from explicit --probe, never from import or unittest discovery.
    request = Request(
        url, headers={"User-Agent": "Hyperfabric-Public-Pages-Readback/1.0",
                      "Cache-Control": "no-cache", "Pragma": "no-cache"},
        method="GET",
    )
    with build_opener(NoRedirect()).open(request, timeout=8) as response:
        return (response.status, response.geturl(), response.read(MAX_BYTES + 1))


def assess_public_deployment(commit: str, deployments: object, statuses: object,
                             workflow: object) -> dict:
    """GitHub-reported exact source/deployment match, not cryptographic attestation."""
    def hold(reason: str) -> dict:
        return {"status": reason, "source_commit_attributed": False}

    if not isinstance(deployments, list) or not deployments:
        return hold("NO_PUBLIC_DEPLOYMENT")
    latest = deployments[0]
    if not isinstance(latest, dict):
        return hold("MALFORMED_DEPLOYMENT_RECORD")
    if latest.get("environment") != "github-pages" or latest.get("ref") != "main":
        return hold("WRONG_DEPLOYMENT_ENVIRONMENT")
    if latest.get("sha") != commit:
        return hold("LATEST_DEPLOYMENT_DIFFERENT_SOURCE")
    if type(latest.get("id")) is not int or latest["id"] <= 0:
        return hold("INVALID_DEPLOYMENT_ID")
    if not isinstance(statuses, list) or not statuses or not isinstance(statuses[0], dict):
        return hold("MISSING_DEPLOYMENT_STATUS")
    current = statuses[0]
    if (current.get("state") != "success" or
            current.get("environment") != "github-pages" or
            current.get("environment_url") != PUBLIC_BASE):
        return hold("DEPLOYMENT_NOT_SUCCESSFUL")
    if not isinstance(workflow, dict):
        return hold("MISSING_BUILD_RUN")
    if (workflow.get("head_sha") != commit or
            workflow.get("status") != "completed" or
            workflow.get("conclusion") != "success" or
            workflow.get("name") != "pages build and deployment"):
        return hold("BUILD_COMMIT_OR_RESULT_MISMATCH")
    log_url = current.get("log_url")
    if not isinstance(log_url, str):
        return hold("NO_ASSOCIATED_PAGES_WORKFLOW")
    match = re.fullmatch(
        r"https://github[.]com/Footloose9/hyperfabric-evolution/"
        r"actions/runs/([1-9][0-9]*)/job/[1-9][0-9]*", log_url)
    if match is None or workflow.get("id") != int(match.group(1)):
        return hold("STATUS_WORKFLOW_NOT_CORRELATED")
    return {"status": "GITHUB_PAGES_SOURCE_MATCH",
            "source_commit_attributed": True,
            "deployment_id": latest["id"], "workflow_id": workflow["id"]}


def github_public_json(relative: str):
    """Fixed, bounded, public-only API paths; called only by --probe."""
    allowed = (
        r"deployments[?]environment=github-pages&per_page=10",
        r"deployments/[1-9][0-9]*/statuses[?]per_page=10",
        r"actions/runs/[1-9][0-9]*",
    )
    if not any(re.fullmatch(pattern, relative) for pattern in allowed):
        raise ValueError("UNEXPECTED_GITHUB_API_PATH")
    url = PUBLIC_API + relative
    request = Request(
        url, headers={"User-Agent": "Hyperfabric-Public-Pages-Readback/1.0",
                      "Accept": "application/vnd.github+json"},
        method="GET",
    )
    with build_opener(NoRedirect()).open(request, timeout=8) as response:
        if response.status != 200 or response.geturl() != url:
            raise ValueError("PUBLIC_GITHUB_API_NOT_OK")
        payload = response.read(MAX_BYTES + 1)
        if len(payload) > MAX_BYTES:
            raise ValueError("PUBLIC_GITHUB_API_TOO_LARGE")
    return json.loads(payload)


def live_public_deployment(commit: str) -> dict:
    """Never executes during default unit tests or on import."""
    try:
        deployments = github_public_json(
            "deployments?environment=github-pages&per_page=10")
        if not isinstance(deployments, list) or not deployments:
            return {"status": "NO_PUBLIC_DEPLOYMENT",
                    "source_commit_attributed": False}
        latest = deployments[0]
        if not isinstance(latest, dict) or type(latest.get("id")) is not int:
            return {"status": "MALFORMED_DEPLOYMENT_RECORD",
                    "source_commit_attributed": False}
        if (latest.get("sha") != commit or
                latest.get("ref") != "main" or
                latest.get("environment") != "github-pages"):
            return {"status": "LATEST_DEPLOYMENT_DIFFERENT_SOURCE",
                    "source_commit_attributed": False}
        statuses = github_public_json(
            f"deployments/{latest['id']}/statuses?per_page=10")
        if not isinstance(statuses, list) or not statuses or not isinstance(statuses[0], dict):
            return {"status": "MISSING_DEPLOYMENT_STATUS",
                    "source_commit_attributed": False}
        log_url = statuses[0].get("log_url")
        if not isinstance(log_url, str):
            return {"status": "NO_ASSOCIATED_PAGES_WORKFLOW",
                    "source_commit_attributed": False}
        m = re.fullmatch(
            r"https://github[.]com/Footloose9/hyperfabric-evolution/"
            r"actions/runs/([1-9][0-9]*)/job/[1-9][0-9]*", log_url)
        if not m:
            return {"status": "NO_ASSOCIATED_PAGES_WORKFLOW",
                    "source_commit_attributed": False}
        workflow = github_public_json(f"actions/runs/{m.group(1)}")
        return assess_public_deployment(commit, deployments, statuses, workflow)
    except (HTTPError, URLError, OSError, TimeoutError, ValueError,
            json.JSONDecodeError):
        return {"status": "GITHUB_PAGES_EVIDENCE_UNAVAILABLE",
                "source_commit_attributed": False}


def run_opt_in_probe(commit: str) -> dict:
    if not COMMIT_RE.fullmatch(commit):
        raise ValueError("INVALID_COMMIT_SHA")
    items = []
    for asset in ASSETS:
        expected = pinned_source_bytes(commit, asset)
        url = public_url(asset)
        http_status = None
        try:
            http_status, final_url, received = live_asset_bytes(url)
            verdict = assess_readback(
                expected, received, http_status=http_status,
                requested_url=url, final_url=final_url,
            )
        except HTTPError as error:
            http_status = error.code
            verdict = {"status": "HTTP_NOT_OK"}
        except (URLError, OSError, TimeoutError):
            verdict = {"status": "PUBLIC_SOURCE_UNAVAILABLE"}
        items.append({"asset": asset, "url": url,
                      "http_status": http_status, **verdict})
    all_assets_matched = all(x["status"] == "ASSET_BYTES_MATCH" for x in items)
    pages = live_public_deployment(commit)
    return {
        "expected_source_commit": commit,
        "site": PUBLIC_BASE,
        "assets": items,
        "all_assets_matched": all_assets_matched,
        "github_pages": pages,
        "source_release_readback_passed": (
            all_assets_matched and pages["source_commit_attributed"]),
        "evidence_limit": ("GitHub's public API attributes a successful Pages build and "
                           "deployment to this exact source commit; the CDN serves "
                           "matching selected assets. This does not independently "
                           "attest the entire commit, browser behavior or RPC service."),
    }


class SitePublishContractTests(unittest.TestCase):
    def test_current_site_static_sources_are_present_and_linked(self):
        html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(source_contract_errors(
            html, lambda rel: (ROOT / "docs" / rel).is_file()), [])

    def test_broken_fragment_is_detected(self):
        html = '<html><a href="#missing">x</a><script src="site.js"></script><link rel="stylesheet" href="site.css"></html>'
        self.assertIn("BROKEN_LOCAL_ANCHOR:missing",
                      source_contract_errors(html, lambda _: True))

    def test_missing_site_asset_fails(self):
        html = '<html><script src="site.js"></script><link href="site.css" rel="stylesheet"></html>'
        self.assertIn("MISSING_ASSET_FILE:site.js",
                      source_contract_errors(html, lambda rel: rel != "site.js"))

    def test_untrusted_external_script_is_rejected(self):
        html = '<link rel="stylesheet" href="site.css"><script src="site.js"></script><script src="https://elsewhere.test/code.js"></script>'
        self.assertTrue(any("EXTERNAL_EXECUTABLE" in item for item in
                            source_contract_errors(html, lambda _: True)))

    def test_external_and_parent_paths_not_requestable(self):
        for path in ("../../secret", "https://elsewhere.test/x", "xrpl-live.js", ""):
            with self.subTest(path=path), self.assertRaisesRegex(
                    ValueError, "ASSET_NOT_ALLOWLISTED"):
                public_url(path)

    def test_bad_commit_ref_refused_before_git_or_network(self):
        for ref in ("main", "0" * 39, "a" * 39 + ";", "A" * 40):
            with self.subTest(ref=ref), self.assertRaisesRegex(
                    ValueError, "INVALID_COMMIT_SHA"):
                pinned_source_bytes(ref, "index.html")

    def test_matching_asset_is_not_deployment_commit_proof(self):
        url = public_url("index.html")
        self.assertEqual(assess_readback(
            b"same", b"same", http_status=200,
            requested_url=url, final_url=url)["status"], "ASSET_BYTES_MATCH")

    def test_stale_source_bytes_detected(self):
        url = public_url("site.js")
        self.assertEqual(assess_readback(
            b"new", b"old", http_status=200,
            requested_url=url, final_url=url)["status"], "ASSET_BYTES_MISMATCH")

    def test_missing_asset_http_error_is_not_success(self):
        url = public_url("site.js")
        self.assertEqual(assess_readback(
            b"new", b"new", http_status=404,
            requested_url=url, final_url=url)["status"], "HTTP_NOT_OK")

    def test_external_redirect_refused_even_with_matching_bytes(self):
        url = public_url("site.js")
        self.assertEqual(assess_readback(
            b"same", b"same", http_status=200,
            requested_url=url, final_url="https://elsewhere.test/site.js"
        )["status"], "UNEXPECTED_REDIRECT")

    @staticmethod
    def public_deployment_fixtures():
        sha = "a" * 40
        deployment = {"id": 7957949435, "sha": sha, "ref": "main",
                      "environment": "github-pages"}
        statuses = [{"state": "success", "environment": "github-pages",
                     "environment_url": PUBLIC_BASE,
                     "log_url": ("https://github.com/Footloose9/hyperfabric-evolution/"
                                 "actions/runs/44861712556/job/136716454612")}]
        workflow = {"id": 44861712556, "head_sha": sha, "status": "completed",
                    "conclusion": "success", "name": "pages build and deployment"}
        return sha, [deployment], statuses, workflow

    def test_public_deployment_status_and_sha_match(self):
        sha, deployments, statuses, workflow = self.public_deployment_fixtures()
        result = assess_public_deployment(sha, deployments, statuses, workflow)
        self.assertTrue(result["source_commit_attributed"])
        self.assertEqual(result["status"], "GITHUB_PAGES_SOURCE_MATCH")

    def test_newer_deployment_to_different_sha_is_not_ignored(self):
        sha, deployments, statuses, workflow = self.public_deployment_fixtures()
        newer = {**deployments[0], "id": 7957949436, "sha": "b" * 40}
        result = assess_public_deployment(sha, [newer, *deployments],
                                          statuses, workflow)
        self.assertEqual(result["status"], "LATEST_DEPLOYMENT_DIFFERENT_SOURCE")

    def test_failed_deployment_status_refused(self):
        sha, deployments, statuses, workflow = self.public_deployment_fixtures()
        statuses[0] = {**statuses[0], "state": "failure"}
        self.assertFalse(assess_public_deployment(
            sha, deployments, statuses, workflow)["source_commit_attributed"])

    def test_pages_workflow_wrong_commit_refused(self):
        sha, deployments, statuses, workflow = self.public_deployment_fixtures()
        workflow["head_sha"] = "b" * 40
        self.assertEqual(assess_public_deployment(
            sha, deployments, statuses, workflow)["status"],
            "BUILD_COMMIT_OR_RESULT_MISMATCH")

    def test_wrong_workflow_correlation_refused(self):
        sha, deployments, statuses, workflow = self.public_deployment_fixtures()
        workflow["id"] += 1
        self.assertEqual(assess_public_deployment(
            sha, deployments, statuses, workflow)["status"],
            "STATUS_WORKFLOW_NOT_CORRELATED")

    def test_github_api_paths_are_strictly_allowlisted(self):
        for path in ("https://elsewhere.test/", "deployments/../../../secrets",
                     "actions/runs/0", "users/me", "deployments?per_page=100"):
            with self.subTest(path=path), self.assertRaisesRegex(
                    ValueError, "UNEXPECTED_GITHUB_API_PATH"):
                github_public_json(path)

    def test_remote_redirect_is_not_followed(self):
        self.assertIsNone(NoRedirect().redirect_request(
            object(), None, 302, "Redirect", {}, "https://elsewhere.test/fake"))

    def test_oversized_response_fails_closed(self):
        url = public_url("site.js")
        self.assertEqual(assess_readback(
            b"same", b"x" * (MAX_BYTES + 1), http_status=200,
            requested_url=url, final_url=url)["status"],
            "RESPONSE_SIZE_EXCEEDED")

    def test_source_size_bound_is_enforced(self):
        url = public_url("site.js")
        self.assertEqual(assess_readback(
            b"x" * (MAX_BYTES + 1), b"same", http_status=200,
            requested_url=url, final_url=url)["status"],
            "EXPECTED_ASSET_TOO_LARGE")


if __name__ == "__main__":
    if "--probe" in sys.argv:
        argp = argparse.ArgumentParser(
            description="Explicit read-only Pages asset/commit comparison; does not prove whole deployment.")
        argp.add_argument("--probe", action="store_true", required=True)
        argp.add_argument("--expected-commit", required=True)
        args = argp.parse_args()
        try:
            output = run_opt_in_probe(args.expected_commit)
            print(json.dumps(output, sort_keys=True))
            sys.exit(0 if output["source_release_readback_passed"] else 1)
        except ValueError as error:
            print(json.dumps({"status": str(error)}))
            sys.exit(2)
    unittest.main()
