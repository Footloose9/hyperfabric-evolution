"""Offline, fictional Bitcoin UTXO evidence; NOT a ledger or ownership oracle.

Only models declared (txid, vout) outpoints, opaque scriptPubKey, satoshi
arithmetic, and explicitly synthetic block inclusion states. Neither a
shared input nor a possible change output establishes common human control.
No RPC, wallet, keys, signing, account graph, monitoring or broadcast.
"""
from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from math import isfinite
import json
import re
from typing import Any

SCHEMA_VERSION = "hf.bitcoin.synthetic_utxo.v1"
NETWORK = "bitcoin:synthetic"
PROVENANCE = "PUBLIC_SYNTHETIC"
MAX_MONEY_SATS = 21_000_000 * 100_000_000
MAX_FIXTURE_BYTES = 40_000
MAX_JSON_NESTING_DEPTH = 256
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_HEX = re.compile(r"[0-9a-f]*\Z")
_STATES = frozenset({"UNCONFIRMED", "CONFIRMED", "REORGED", "CONFLICTED"})


class SyntheticUTXOError(ValueError):
    """Invalid or insufficient fictional evidence; never accept by guessing."""


class MissingPrevoutError(SyntheticUTXOError):
    """Referenced prevout has no declared value and script evidence."""


class CompetingSpendError(SyntheticUTXOError):
    """Two candidate transactions spend the same declared outpoint."""


def _need(condition: bool, reason: str) -> None:
    if not condition:
        raise SyntheticUTXOError(reason)


def _object(raw: Any, fields: set[str], where: str) -> Mapping[str, Any]:
    _need(isinstance(raw, Mapping) and set(raw) == fields,
          f"{where}: unexpected, missing, or ownership/heuristic field")
    return raw


def _int(raw: Any, label: str, minimum: int, maximum: int) -> int:
    _need(type(raw) is int and minimum <= raw <= maximum,
          f"{label} must be an integer in [{minimum}, {maximum}]")
    return raw


def _txid(raw: Any, label: str) -> str:
    _need(type(raw) is str and _HEX64.fullmatch(raw) is not None,
          f"{label} must be a lowercase 64-hex synthetic identifier")
    return raw


def _script(raw: Any, label: str) -> str:
    _need(type(raw) is str and len(raw) % 2 == 0 and len(raw) <= 20_000
          and _HEX.fullmatch(raw) is not None,
          f"{label} must be opaque lowercase scriptPubKey hex (<=10000 bytes)")
    return raw


def _outpoint(txid: Any, vout: Any) -> tuple[str, int]:
    return (_txid(txid, "prevout.txid"),
            _int(vout, "prevout.vout", 0, 0xFFFFFFFF))


def _inclusion(raw: Any, own_txid: str) -> dict[str, Any]:
    v = _object(raw, {"status", "block_hash", "block_height",
                      "confirmations", "conflicting_txid"}, "inclusion")
    state = v["status"]
    _need(type(state) is str and state in _STATES,
          "unknown synthetic inclusion state")
    confirmations = _int(v["confirmations"], "confirmations", 0, 1_000_000)
    block_hash, block_height, conflict = (
        v["block_hash"], v["block_height"], v["conflicting_txid"])
    if state in {"CONFIRMED", "REORGED"}:
        block_hash = _txid(block_hash, "block_hash")
        block_height = _int(block_height, "block_height", 0, 100_000_000)
        _need(conflict is None, "confirmed/reorged status cannot include conflict id")
        _need((confirmations >= 1) if state == "CONFIRMED"
              else (confirmations == 0),
              "block state and reported confirmations disagree")
    else:
        _need(block_hash is None and block_height is None and confirmations == 0,
              "unconfirmed/conflicted state cannot claim current block inclusion")
        if state == "CONFLICTED":
            conflict = _txid(conflict, "conflicting_txid")
            _need(conflict != own_txid, "transaction cannot conflict with itself")
        else:
            _need(conflict is None, "unconfirmed state cannot contain conflict id")
    return {"status": state, "block_hash": block_hash,
            "block_height": block_height, "confirmations": confirmations,
            "conflicting_txid": conflict}


def _finite_json_float(raw: str) -> float:
    """JSON numeric exponents must not overflow into nonfinite float values."""
    value = float(raw)
    _need(isfinite(value), "nonfinite JSON number")
    return value


def _unique_json_members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _need(key not in result, "duplicate JSON member")
        result[key] = value
    return result


def _check_json_nesting(raw: bytes) -> None:
    """Limit container depth regardless of the host JSON decoder stack."""
    depth = 0
    quoted = False
    escaped = False
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 0x5C:  # backslash inside JSON string
                escaped = True
            elif byte == 0x22:  # terminating quote
                quoted = False
        elif byte == 0x22:
            quoted = True
        elif byte in (0x7B, 0x5B):  # { [
            depth += 1
            _need(depth <= MAX_JSON_NESTING_DEPTH,
                  "JSON nesting depth exceeded")
        elif byte in (0x7D, 0x5D):  # } ]
            depth -= 1
            _need(depth >= 0, "unexpected JSON container closure")


def parse_fixture_json(raw: bytes) -> dict[str, Any]:
    """Decode only bounded JSON and reject duplicate/nonfinite members."""
    _need(type(raw) is bytes and 0 < len(raw) <= MAX_FIXTURE_BYTES,
          "fixture JSON byte limit or source type invalid")
    _check_json_nesting(raw)
    try:
        data = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_unique_json_members,
            parse_float=_finite_json_float,
            parse_constant=lambda _: (_ for _ in ()).throw(
                SyntheticUTXOError("nonfinite JSON number")),
        )
    except SyntheticUTXOError:
        raise
    except RecursionError as exc:
        # The byte ceiling alone does not bound JSON array/object nesting.
        # Decoder depth failures must preserve the public typed refusal.
        raise SyntheticUTXOError("JSON nesting depth exceeded") from exc
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise SyntheticUTXOError("invalid JSON encoding or syntax") from exc
    _need(type(data) is dict, "fixture root must be an object")
    return data


def project_synthetic_utxos(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deterministic, typed, explicitly non-attributing evidence graph.

    Only a supplied list of fully resolved previous outputs is used. This
    is neither a Bitcoin consensus verifier nor proof of chain inclusion.
    """
    packet = _object(raw, {"schema", "network", "provenance",
                           "known_prevouts", "transactions"}, "fixture")
    _need(packet["schema"] == SCHEMA_VERSION
          and packet["network"] == NETWORK
          and packet["provenance"] == PROVENANCE,
          "unqualified schema, chain or synthetic provenance")
    prevouts = packet["known_prevouts"]
    txs = packet["transactions"]
    _need(type(prevouts) is list and 0 <= len(prevouts) <= 64,
          "bounded known_prevouts list required")
    _need(type(txs) is list and 1 <= len(txs) <= 16,
          "bounded transactions list required")
    # V1 intentionally models independent candidate transactions only.
    # Detect every declared txid before walking inputs, so an internally
    # linked outpoint cannot be accepted or rejected merely due to row order.
    candidate_ids: set[str] = set()
    for entry in txs:
        candidate = _object(entry, {"txid", "inputs", "outputs", "inclusion"},
                            "transaction")
        candidate_id = _txid(candidate["txid"], "transaction.txid")
        _need(candidate_id not in candidate_ids, "duplicate candidate transaction")
        candidate_ids.add(candidate_id)

    known: dict[tuple[str, int], dict[str, Any]] = {}
    for item in prevouts:
        p = _object(item, {"txid", "vout", "value_sats",
                           "script_pubkey_hex"}, "known_prevout")
        key = _outpoint(p["txid"], p["vout"])
        _need(key != ("0" * 64, 0xFFFFFFFF),
              "coinbase sentinel unsupported in normal-spend fixture")
        _need(key not in known, "duplicate known prevout")
        known[key] = {
            "value_sats": _int(p["value_sats"], "prevout.value_sats", 0,
                               MAX_MONEY_SATS),
            "script_pubkey_hex": _script(p["script_pubkey_hex"],
                                         "prevout.script_pubkey_hex"),
        }

    transaction_ids: set[str] = set()
    spent: set[tuple[str, int]] = set()
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    total_fee = 0
    def node(key: str, role: str, **attributes: Any) -> None:
        item = {"key": key, "role": role, "network": NETWORK,
                "provenance": PROVENANCE, **attributes}
        _need(key not in nodes or nodes[key] == item,
              "graph node identity or value collision")
        nodes[key] = item

    for entry in txs:
        t = _object(entry, {"txid", "inputs", "outputs", "inclusion"},
                    "transaction")
        txid = _txid(t["txid"], "transaction.txid")
        _need(txid not in transaction_ids, "duplicate candidate transaction")
        transaction_ids.add(txid)
        ins, outs = t["inputs"], t["outputs"]
        _need(type(ins) is list and 1 <= len(ins) <= 64,
              "noncoinbase transaction requires bounded inputs")
        _need(type(outs) is list and 1 <= len(outs) <= 64,
              "transaction requires bounded outputs")
        inclusion = _inclusion(t["inclusion"], txid)
        txkey = "tx:" + txid
        node(txkey, "TRANSACTION", inclusion=inclusion)
        input_total = 0
        for ref in ins:
            i = _object(ref, {"txid", "vout", "sequence"}, "transaction.input")
            key = _outpoint(i["txid"], i["vout"])
            _int(i["sequence"], "input.sequence", 0, 0xFFFFFFFF)
            _need(key != ("0" * 64, 0xFFFFFFFF),
                  "coinbase sentinel unsupported")
            _need(key[0] != txid, "self-spending synthetic transaction")
            _need(key[0] not in candidate_ids,
                  "intra-fixture linked transaction spends unsupported in v1")
            if key not in known:
                raise MissingPrevoutError("absent prevout: " + key[0] + ":" + str(key[1]))
            if key in spent:
                raise CompetingSpendError("ambiguous duplicate spend of " +
                                         key[0] + ":" + str(key[1]))
            spent.add(key)
            value = known[key]["value_sats"]
            input_total += value
            source_key = "outpoint:" + key[0] + ":" + str(key[1])
            node(source_key, "PREVIOUS_OUTPUT", outpoint_txid=key[0],
                 vout=key[1], value_sats=value,
                 script_pubkey_hex=known[key]["script_pubkey_hex"])
            edges.append({"from": source_key, "to": txkey,
                          "relation": "SPENDS_PREVOUT",
                          "evidence_txid": txid, "inclusion": inclusion["status"]})
        _need(input_total <= MAX_MONEY_SATS, "input sum outside satoshi bound")
        output_total = 0
        seen_output_indices: set[int] = set()
        for raw_output in outs:
            o = _object(raw_output, {"vout", "value_sats",
                                     "script_pubkey_hex"}, "transaction.output")
            idx = _int(o["vout"], "output.vout", 0, 0xFFFFFFFF)
            _need(idx not in seen_output_indices, "duplicate output index")
            seen_output_indices.add(idx)
            value = _int(o["value_sats"], "output.value_sats", 0, MAX_MONEY_SATS)
            script = _script(o["script_pubkey_hex"], "output.script_pubkey_hex")
            output_total += value
            child_key = "outpoint:" + txid + ":" + str(idx)
            node(child_key, "CREATED_OUTPUT", outpoint_txid=txid,
                 vout=idx, value_sats=value, script_pubkey_hex=script)
            edges.append({"from": txkey, "to": child_key,
                          "relation": "CREATES_OUTPUT",
                          "evidence_txid": txid, "inclusion": inclusion["status"]})
        _need(seen_output_indices == set(range(len(outs))),
              "output index must correspond to zero-based transaction ordering")
        _need(output_total <= input_total,
              "negative fee or minted value in noncoinbase transaction")
        fee = input_total - output_total
        total_fee += fee
        summaries.append({"txid": txid, "input_total_sats": input_total,
                          "output_total_sats": output_total, "fee_sats": fee,
                          "inclusion": inclusion, "source": PROVENANCE})
    _need(total_fee <= MAX_MONEY_SATS, "aggregate synthetic fee overflow")

    edges.sort(key=lambda e: (e["evidence_txid"], e["relation"],
                              e["from"], e["to"]))
    result = {
        "schema": SCHEMA_VERSION,
        "status": "PASS_SYNTHETIC_OUTPOINT_ARITHMETIC_NOT_CHAIN_VERIFICATION",
        "network": NETWORK, "provenance": PROVENANCE,
        "nodes": [nodes[key] for key in sorted(nodes)],
        "edges": edges, "transactions": sorted(summaries, key=lambda v: v["txid"]),
        "total_fee_sats": total_fee,
        "candidate_transaction_count": len(txs),
        "common_owner_inferred": False,
        "change_output_inferred": False,
        "transaction_to_account_transfer_inferred": False,
        "independent_consensus_or_finality_proven": False,
        "wallet_or_identity_attested": False,
        "source_completeness": "DECLARED_FIXTURE_ONLY",
    }
    # Deterministic digest prevents unnoticed fixture changes; a digest is
    # not an authentic Bitcoin source signature or block confirmation.
    body = json.dumps(result, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")
    result["canonical_projection_sha256"] = sha256(body).hexdigest().upper()
    return result
