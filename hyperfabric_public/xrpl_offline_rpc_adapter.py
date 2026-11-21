"""Strict offline, synthetic XRPL account_tx JSON-shape observation adapter.

This is an educational decoder for invented API-v2-like response bytes. It
does not communicate with a ledger, validate signatures/checksums or confirm
provider claims. A synthetic recorded result is never authenticated finality,
account ownership, a trading fill, or a financial authorization.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re

MAX_CAPTURE_BYTES = 128 * 1024
MAX_PAGE_ENTRIES = 32
_HEX64 = re.compile(r"[0-9A-Fa-f]{64}\Z")
_HEX48 = re.compile(r"[0-9A-Fa-f]{48}\Z")
_CURRENCY = re.compile(r"(?:[A-Z0-9]{3}|[0-9A-Fa-f]{40})\Z")
_DECIMAL_TEXT = re.compile(r"[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]{1,3})?\Z")
_SIM = re.compile(r"sim:[a-z][a-z0-9_-]{0,47}\Z")
_TEC = re.compile(r"tec[A-Z0-9_]+\Z")
_AMM_TYPES = frozenset({
    "AMMCreate", "AMMDelete", "AMMDeposit", "AMMWithdraw",
    "AMMVote", "AMMBid", "AMMClawback",
})


@dataclass(frozen=True)
class SyntheticCapture:
    """Caller-specified provenance, not a qualified live network identity."""
    network: str
    provider: str
    method: str
    account: str
    captured_utc: str


@dataclass(frozen=True)
class OfflineTransaction:
    transaction_hash: str | None
    ledger_hash: str | None
    ledger_index: int | None
    transaction_type: str | None
    transaction_result: str | None
    recorded_outcome: str
    effect_state: str
    reason: str
    asset_identity: str | None = None
    delivered_value: str | None = None
    provenance: str = "SYNTHETIC_PROVIDER_CLAIM_NOT_VERIFIED"


@dataclass(frozen=True)
class OfflinePage:
    disposition: str
    reason: str
    raw_content_sha256: str | None
    provider: str | None
    network: str | None
    rpc_method: str | None
    captured_utc: str | None
    ledger_index_min: int | None
    ledger_index_max: int | None
    pagination: str
    source_validated_claim: bool
    transactions: tuple[OfflineTransaction, ...]
    provenance: str = "SYNTHETIC_PROVIDER_CLAIM_NOT_VERIFIED"


def _utc(value: object) -> bool:
    if not isinstance(value, str) or len(value) > 45:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.utcoffset() == timedelta(0)
    except (ValueError, TypeError):
        return False


def _positive_decimal(value: object, *, integer: bool) -> bool:
    if not isinstance(value, str) or not 0 < len(value) <= 80:
        return False
    if integer and re.fullmatch(r"[0-9]+", value) is None:
        return False
    if not integer and _DECIMAL_TEXT.fullmatch(value) is None:
        return False
    try:
        number = Decimal(value)
    except InvalidOperation:
        return False
    if not number.is_finite() or number <= 0:
        return False
    if integer:
        return number == number.to_integral_value()
    digits = list(number.as_tuple().digits)
    while len(digits) > 1 and digits[-1] == 0:
        digits.pop()
    # Conservative public teaching subset; not canonical XRPL serialization.
    return len(digits) <= 16 and -96 <= number.adjusted() <= 80


def _delivered(value: object) -> tuple[str, str] | None:
    """Parse only metadata.delivered_amount, never requested DeliverMax/Amount."""
    if isinstance(value, str):
        if (_positive_decimal(value, integer=True)
                and int(value) <= 100_000_000_000_000_000):
            return ("xrpl:synthetic:native:XRP", value)
        return None
    if not isinstance(value, dict):
        return None
    if set(value) == {"currency", "issuer", "value"}:
        currency, issuer, amount = (
            value["currency"], value["issuer"], value["value"]
        )
        if (isinstance(currency, str) and _CURRENCY.fullmatch(currency)
                and currency != "XRP"
                and isinstance(issuer, str) and _SIM.fullmatch(issuer)
                and _positive_decimal(amount, integer=False)):
            return (f"xrpl:synthetic:issued:{currency}:{issuer}", amount)
        return None
    if set(value) == {"mpt_issuance_id", "value"}:
        issuance, amount = value["mpt_issuance_id"], value["value"]
        if (isinstance(issuance, str) and _HEX48.fullmatch(issuance)
                and _positive_decimal(amount, integer=True)
                and int(amount) <= (2**63 - 1)):
            return (f"xrpl:synthetic:mpt:{issuance.upper()}", amount)
    return None


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    obj = {}
    for name, value in pairs:
        if name in obj:
            raise ValueError("duplicate JSON key")
        obj[name] = value
    return obj


def _reject_constant(value: str):
    raise ValueError("nonstandard JSON constant")


def _tx(entry: object, *, min_index: int, max_index: int,
        page_validated: bool) -> OfflineTransaction:
    def incomplete(reason: str, *, outcome: str = "NOT_ESTABLISHED",
                   effect: str = "INCONCLUSIVE") -> OfflineTransaction:
        return OfflineTransaction(
            h if isinstance(h, str) else None,
            lh if isinstance(lh, str) else None,
            idx if type(idx) is int else None,
            typ if isinstance(typ, str) else None,
            result if isinstance(result, str) else None,
            outcome, effect, reason,
        )

    h, lh, idx, typ, result = None, None, None, None, None
    if not isinstance(entry, dict):
        return incomplete("MALFORMED_ENTRY", effect="REFUSE")
    h, lh, idx = entry.get("hash"), entry.get("ledger_hash"), entry.get("ledger_index")
    tx, meta = entry.get("tx_json"), entry.get("meta")
    typ = tx.get("TransactionType") if isinstance(tx, dict) else None
    result = meta.get("TransactionResult") if isinstance(meta, dict) else None
    if (not isinstance(h, str) or not _HEX64.fullmatch(h)
            or not isinstance(lh, str) or not _HEX64.fullmatch(lh)
            or type(idx) is not int or not min_index <= idx <= max_index
            or not isinstance(tx, dict) or not isinstance(meta, dict)
            or not isinstance(typ, str) or not typ
            or not isinstance(tx.get("Account"), str)
            or _SIM.fullmatch(tx["Account"]) is None
            or ("Destination" in tx and (
                not isinstance(tx["Destination"], str)
                or _SIM.fullmatch(tx["Destination"]) is None))
            or type(entry.get("validated")) is not bool
            or ("hash" in tx and tx["hash"] != h)
            or ("ledger_index" in tx and tx["ledger_index"] != idx)):
        return incomplete("INVALID_TRANSACTION_ANCHOR", effect="REFUSE")
    if "AffectedNodes" in meta and not isinstance(meta["AffectedNodes"], list):
        return incomplete("MALFORMED_AFFECTED_NODES", effect="REFUSE")
    if result != "tesSUCCESS" and (
        not isinstance(result, str) or not _TEC.fullmatch(result)
    ):
        return incomplete("INVALID_VALIDATED_RESULT", effect="REFUSE")
    if not (page_validated and entry["validated"]):
        return incomplete("SOURCE_NOT_VALIDATED")
    if result.startswith("tec"):
        return incomplete("VALIDATED_FAILURE_NO_INTENDED_EFFECT",
                          outcome="VALIDATED_FAILED",
                          effect="NO_INTENDED_EFFECT")
    outcome = "VALIDATED_SUCCESS"
    if typ == "Payment":
        parsed = _delivered(meta.get("delivered_amount"))
        if parsed is None:
            return incomplete("DELIVERED_AMOUNT_ABSENT_OR_UNQUALIFIED",
                              outcome=outcome)
        asset_key, amount = parsed
        return OfflineTransaction(
            h, lh, idx, typ, result, outcome,
            "SIMULATED_DELIVERY_METADATA_ONLY",
            "NO_ACCOUNT_OWNERSHIP_OR_PATH_PROOF",
            asset_key, amount,
        )
    if typ == "OfferCreate":
        effect, reason = "INCONCLUSIVE", "OFFER_CREATED_OR_REMOVED_NOT_FILL_PROOF"
    elif typ == "OfferCancel":
        effect, reason = "NO_FILL_CLAIM", "CANCELLATION_NOT_TRADE_PROOF"
    elif typ in _AMM_TYPES:
        effect, reason = "INCONCLUSIVE", "AMM_LEDGER_STATE_NOT_EXECUTION_PRICE"
    elif typ == "Batch":
        nested = tx.get("RawTransactions")
        if not isinstance(nested, list) or not 2 <= len(nested) <= 8:
            return incomplete("INVALID_BATCH_SHAPE", effect="REFUSE",
                              outcome=outcome)
        effect, reason = "INCONCLUSIVE", "BATCH_OUTER_SUCCESS_NOT_INNER_SUCCESS"
    elif typ in ("AccountSet", "TrustSet", "SetRegularKey"):
        effect, reason = "INCONCLUSIVE", "ISSUER_OR_ACCOUNT_FLAGS_NOT_DERIVED"
    else:
        effect, reason = "INCONCLUSIVE", "UNSUPPORTED_EFFECT_MAPPING"
    return OfflineTransaction(h, lh, idx, typ, result, outcome, effect, reason)


def assess_synthetic_account_tx(raw_bytes: bytes, capture: SyntheticCapture) -> OfflinePage:
    """Read a single fabricated account_tx response; never call network APIs.

    Even a valid API-shaped response remains an unauthenticated source claim.
    PAGE_END_ONLY is not proof of global account-history completeness.
    """
    provider = capture.provider if isinstance(capture, SyntheticCapture) else None
    network = capture.network if isinstance(capture, SyntheticCapture) else None
    method = capture.method if isinstance(capture, SyntheticCapture) else None
    observed = capture.captured_utc if isinstance(capture, SyntheticCapture) else None
    digest = (sha256(raw_bytes).hexdigest().upper()
              if isinstance(raw_bytes, bytes) else None)

    def report(state, reason, *, lmin=None, lmax=None, pagination="UNKNOWN",
               validated=False, txs=()):
        return OfflinePage(state, reason, digest, provider, network, method,
                           observed, lmin, lmax, pagination, validated, tuple(txs))

    if (not isinstance(capture, SyntheticCapture)
            or capture.network != "xrpl:synthetic"
            or capture.method != "account_tx"
            or not isinstance(capture.provider, str)
            or not _SIM.fullmatch(capture.provider)
            or not isinstance(capture.account, str)
            or not _SIM.fullmatch(capture.account)
            or not _utc(capture.captured_utc)):
        return report("REFUSE", "NON_SYNTHETIC_OR_MALFORMED_CAPTURE")
    if not isinstance(raw_bytes, bytes) or not 0 < len(raw_bytes) <= MAX_CAPTURE_BYTES:
        return report("REFUSE", "UNBOUNDED_OR_EMPTY_SOURCE_BYTES")
    try:
        page = json.loads(
            raw_bytes.decode("utf-8"), object_pairs_hook=_no_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, ValueError, TypeError, RecursionError):
        return report("REFUSE", "INVALID_OR_AMBIGUOUS_JSON")
    if not isinstance(page, dict) or not isinstance(page.get("result"), dict):
        return report("REFUSE", "MISSING_RESULT")
    result = page["result"]
    if result.get("error"):
        return report("INCONCLUSIVE", "PROVIDER_ERROR:" + str(result["error"])[:60])
    if result.get("status") != "success" or result.get("account") != capture.account:
        return report("REFUSE", "SOURCE_ACCOUNT_OR_STATUS_MISMATCH")
    lo, hi, txs = (
        result.get("ledger_index_min"), result.get("ledger_index_max"),
        result.get("transactions"),
    )
    if (type(lo) is not int or type(hi) is not int or lo <= 0 or hi < lo
            or type(result.get("validated")) is not bool
            or not isinstance(txs, list) or len(txs) > MAX_PAGE_ENTRIES):
        return report("REFUSE", "INVALID_RANGE_VALIDATION_OR_CAPACITY")
    marker = result.get("marker")
    if marker is not None and not (
        isinstance(marker, str) and 0 < len(marker) <= 512 or
        isinstance(marker, dict) and 0 < len(marker) <= 24
    ):
        return report("REFUSE", "INVALID_PAGINATION_MARKER")
    pagination = "MARKER_PRESENT_PARTIAL" if marker is not None else "PAGE_END_ONLY"
    assessments = tuple(
        _tx(item, min_index=lo, max_index=hi,
            page_validated=result["validated"]) for item in txs
    )
    hashes = [item.transaction_hash for item in assessments
              if item.transaction_hash is not None]
    if len(hashes) != len(set(hashes)):
        return report("INCONCLUSIVE", "DUPLICATED_TRANSACTION_ANCHOR",
                      lmin=lo, lmax=hi, pagination=pagination,
                      validated=result["validated"], txs=assessments)
    if any(item.effect_state == "REFUSE" for item in assessments):
        return report("INCONCLUSIVE", "ONE_OR_MORE_MALFORMED_TRANSACTION_RECORDS",
                      lmin=lo, lmax=hi, pagination=pagination,
                      validated=result["validated"], txs=assessments)
    if not result["validated"]:
        return report("INCONCLUSIVE", "PAGE_VALIDATION_NOT_ESTABLISHED",
                      lmin=lo, lmax=hi, pagination=pagination,
                      validated=False, txs=assessments)
    return report("SIMULATED_PAGE_OBSERVATION", "SOURCE_STATEMENTS_ONLY_NOT_CONSENSUS",
                  lmin=lo, lmax=hi, pagination=pagination,
                  validated=True, txs=assessments)


def compare_synthetic_page_sources(left: OfflinePage, right: OfflinePage) -> str:
    """Cross-check fabricated claims; matching sources are not consensus."""
    if not isinstance(left, OfflinePage) or not isinstance(right, OfflinePage):
        return "INCONCLUSIVE"
    if left.disposition != "SIMULATED_PAGE_OBSERVATION" or (
        right.disposition != "SIMULATED_PAGE_OBSERVATION"
    ):
        return "INCONCLUSIVE"
    if left.network != right.network or left.rpc_method != right.rpc_method:
        return "CONFLICT"
    lmap = {t.transaction_hash: t for t in left.transactions
            if t.transaction_hash and t.effect_state != "REFUSE"}
    rmap = {t.transaction_hash: t for t in right.transactions
            if t.transaction_hash and t.effect_state != "REFUSE"}
    shared = set(lmap) & set(rmap)
    if not shared:
        return "NO_SHARED_EVENT"
    if any((
        lmap[key].ledger_hash, lmap[key].ledger_index,
        lmap[key].transaction_type, lmap[key].transaction_result,
        lmap[key].asset_identity, lmap[key].delivered_value,
    ) != (
        rmap[key].ledger_hash, rmap[key].ledger_index,
        rmap[key].transaction_type, rmap[key].transaction_result,
        rmap[key].asset_identity, rmap[key].delivered_value,
    ) for key in shared):
        return "CONFLICT"
    if left.provider == right.provider:
        return "NOT_INDEPENDENT"
    return "MATCHING_SYNTHETIC_CLAIMS_NOT_ATTESTED"
