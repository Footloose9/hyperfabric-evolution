/* Public-only, manual XRPL mainnet read-only observations.
 * Source: public JSON-RPC. Never requests or stores keys. No transactions.
 * A provider's validated claim is NOT independent consensus verification.
 */
(function (root) {
  "use strict";
  var ENDPOINT = "https://xrplcluster.com/";
  var ADDRESS_SHAPE = /^r[A-Za-z0-9]{24,34}$/;
  var HASH_SHAPE = /^[0-9A-Fa-f]{64}$/;
  var INTEGER_SHAPE = /^(0|[1-9][0-9]*)$/;

  function refuse(reason) { throw new Error(reason); }
  function isObject(x) { return x !== null && typeof x === "object" && !Array.isArray(x); }
  function ledgerIndex(value) {
    var str = String(value);
    if (!INTEGER_SHAPE.test(str)) { refuse("Missing or invalid ledger index. Observation refused."); }
    var n = Number(str);
    if (!Number.isSafeInteger(n) || n < 1) { refuse("Unusable ledger index. Observation refused."); }
    return n;
  }
  function validHash(value) {
    if (typeof value !== "string" || !HASH_SHAPE.test(value)) {
      refuse("Missing or invalid ledger hash. Observation refused.");
    }
    return value.toUpperCase();
  }
  function getResult(payload) {
    if (!isObject(payload) || !isObject(payload.result)) {
      refuse("Malformed JSON-RPC response. Observation unavailable.");
    }
    return payload.result;
  }
  function ensureValidated(result) {
    if (result.status !== "success" || result.validated !== true) {
      refuse("Provider did not supply a successful validated-ledger observation.");
    }
  }
  function parseLedger(payload) {
    var r = getResult(payload);
    ensureValidated(r);
    var l = isObject(r.ledger) ? r.ledger : {};
    var index = ledgerIndex(r.ledger_index !== undefined ? r.ledger_index : l.ledger_index);
    var hash = validHash(r.ledger_hash || l.ledger_hash);
    if (r.ledger_hash && l.ledger_hash && r.ledger_hash.toUpperCase() !== l.ledger_hash.toUpperCase()) {
      refuse("Inconsistent ledger hashes. Observation refused.");
    }
    if (r.ledger_index !== undefined && l.ledger_index !== undefined &&
        ledgerIndex(r.ledger_index) !== ledgerIndex(l.ledger_index)) {
      refuse("Inconsistent ledger indices. Observation refused.");
    }
    // Ripple Epoch is 2000-01-01 UTC (946684800 UNIX seconds).
    // A provider-validated claim alone does not establish freshness.
    var closeTime = l.close_time;
    if (!Number.isSafeInteger(closeTime) || closeTime < 1 || closeTime > 4294967295) {
      refuse("Missing or invalid ledger close time. Observation refused.");
    }
    var closeMillis = (closeTime + 946684800) * 1000;
    if (l.close_time_iso !== undefined &&
        (typeof l.close_time_iso !== "string" || Date.parse(l.close_time_iso) !== closeMillis)) {
      refuse("Inconsistent ledger close time. Observation refused.");
    }
    return Object.freeze({
      network: "XRPL Mainnet", ledger_index: index, ledger_hash: hash,
      ledger_close_time_utc: new Date(closeMillis).toISOString(),
      source: ENDPOINT, provider_reports_validated: true
    });
  }
  function checkAddressShape(account) {
    if (typeof account !== "string" || !ADDRESS_SHAPE.test(account)) {
      refuse("Enter an XRPL classic address (r...); the server checks its validity.");
    }
    return account;
  }
  function formatDrops(drops) {
    if (typeof drops !== "string" || drops.length > 40 || !INTEGER_SHAPE.test(drops)) {
      refuse("Invalid XRP drops value; no balance displayed.");
    }
    var n = BigInt(drops);
    var whole = n / 1000000n;
    var frac = (n % 1000000n).toString().padStart(6, "0");
    return whole.toString() + "." + frac;
  }
  function parseAccount(payload, requestedAddress) {
    var account = checkAddressShape(requestedAddress);
    var r = getResult(payload);
    if (r.error === "actNotFound") {
      refuse("Account is not present in this validated ledger. This is not a zero balance.");
    }
    ensureValidated(r);
    if (!isObject(r.account_data) || r.account_data.Account !== account) {
      refuse("Provider account identity mismatch or missing account data.");
    }
    var index = ledgerIndex(r.ledger_index);
    var hash = validHash(r.ledger_hash);
    var balance = formatDrops(r.account_data.Balance);
    return Object.freeze({
      network: "XRPL Mainnet", account: account, xrp: balance,
      ledger_index: index, ledger_hash: hash,
      source: ENDPOINT, provider_reports_validated: true,
      scope: "Native XRP balance only; excludes trust-line tokens and MPTs."
    });
  }
  async function request(method, args, fetcher) {
    if (method !== "ledger" && method !== "account_info") {
      refuse("This public view supports read-only ledger and account_info only.");
    }
    var f = fetcher || (typeof root.fetch === "function" ? root.fetch.bind(root) : null);
    if (!f) { refuse("Browser fetch is unavailable."); }
    var controller = typeof AbortController === "function" ? new AbortController() : null;
    var timeout = controller ? setTimeout(function () { controller.abort(); }, 10000) : null;
    try {
      var response = await f(ENDPOINT, {
        method: "POST", mode: "cors", credentials: "omit", cache: "no-store",
        referrerPolicy: "no-referrer",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({method: method, params: [args]}),
        signal: controller ? controller.signal : undefined
      });
      if (!response || response.ok !== true || typeof response.json !== "function") {
        refuse("The public XRPL provider did not return HTTP success.");
      }
      return await response.json();
    } finally {
      if (timeout !== null) { clearTimeout(timeout); }
    }
  }
  function requireRecentLedger(ledger) {
    // Device time is a bounded freshness heuristic, not cryptographic proof.
    // Refuse stale or future observations; do not silently label them current.
    var now = Date.now();
    var closed = Date.parse(ledger.ledger_close_time_utc);
    if (!Number.isFinite(now) || !Number.isFinite(closed) ||
        now - closed > 120000 || closed - now > 30000) {
      refuse("Ledger appears stale, in the future, or device time is incorrect. No current observation.");
    }
    return ledger;
  }
  async function readLedger(fetcher) {
    return requireRecentLedger(parseLedger(await request("ledger", {
      ledger_index: "validated", transactions: false, expand: false
    }, fetcher)));
  }
  async function readAccount(address, fetcher) {
    checkAddressShape(address);
    // Account observation is pinned to one provider-reported validated ledger.
    var ledger = await readLedger(fetcher);
    var account = parseAccount(await request("account_info", {
      account: address, ledger_hash: ledger.ledger_hash
    }, fetcher), address);
    if (account.ledger_index !== ledger.ledger_index ||
        account.ledger_hash !== ledger.ledger_hash) {
      refuse("Account response disagrees with the pinned validated ledger.");
    }
    return Object.freeze(Object.assign({}, account, {
      ledger_close_time_utc: ledger.ledger_close_time_utc,
      pinned_to_observed_ledger: true
    }));
  }
  var api = Object.freeze({
    endpoint: ENDPOINT, checkAddressShape: checkAddressShape, formatDrops: formatDrops,
    parseLedger: parseLedger, parseAccount: parseAccount,
    readLedger: readLedger, readAccount: readAccount, request: request
  });
  if (typeof module !== "undefined" && module.exports) { module.exports = api; }
  root.HyperfabricXRPLReadOnly = api;
  if (typeof document === "undefined") { return; }

  function setText(id, text) {
    var element = document.getElementById(id);
    if (element) { element.textContent = text; }
  }
  function busy(flag) {
    for (var id of ["read-ledger", "read-account"]) {
      var element = document.getElementById(id);
      if (element) { element.disabled = flag; }
    }
  }
  async function showLedger() {
    busy(true);
    setText("ledger-result", "Querying a public provider (manual read only)...");
    try {
      var ledger = await readLedger();
      setText("ledger-result",
        "Provider reports validated mainnet ledger " + ledger.ledger_index +
        " | Hash: " + ledger.ledger_hash +
        " | Closed (reported UTC): " + ledger.ledger_close_time_utc +
        " | Source: " + ledger.source +
        " | One provider; freshness and consensus not independently cross-checked.");
    } catch (error) {
      setText("ledger-result", "UNAVAILABLE — " + error.message);
    } finally { busy(false); }
  }
  async function showAccount() {
    busy(true);
    setText("account-result", "Preparing public account observation...");
    try {
      var element = document.getElementById("public-address");
      var address = element ? element.value.trim() : "";
      var account = await readAccount(address);
      setText("account-result",
        "Provider reports validated XRPL Mainnet ledger " + account.ledger_index +
        ": " + account.account + " holds " + account.xrp +
        " native XRP. Pinned ledger hash: " + account.ledger_hash +
        " | Reported close: " + account.ledger_close_time_utc +
        ". Excludes issued tokens and MPTs. Source: " +
        account.source + ". One provider; freshness and consensus not independently cross-checked.");
    } catch (error) {
      setText("account-result", "UNAVAILABLE — " + error.message);
    } finally { busy(false); }
  }
  document.addEventListener("DOMContentLoaded", function () {
    var ledger = document.getElementById("read-ledger");
    var account = document.getElementById("read-account");
    if (ledger) { ledger.addEventListener("click", showLedger); }
    if (account) { account.addEventListener("click", showAccount); }
  });
})(typeof globalThis !== "undefined" ? globalThis : this);
