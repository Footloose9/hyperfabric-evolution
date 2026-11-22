/* Hyperfabric Evolution public capability gallery — fabricated, offline cases only.
 * This is a viewer for invented claims, not a live ledger, agent, wallet, or authority.
 * No fetch, network connection, local storage, cookies, timers, or background requests.
 */
(function (root, factory) {
  "use strict";
  var api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  if (root && root.document) {
    if (root.document.readyState === "loading") {
      root.document.addEventListener("DOMContentLoaded", function () {
        api.mount(root.document);
      });
    } else {
      api.mount(root.document);
    }
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  /* These values are NOT XRPL account addresses, EVM contracts, hashes, or transactions. */
  var CASES = Object.freeze({
    different: {
      title: "Same ticker. Two issuers.",
      claim: "Can a shared currency label establish a single issued asset?",
      left: { network: "xrpl:synthetic", kind: "issued", currency: "WAVE", issuer: "sim:issuer_alpha" },
      right: { network: "xrpl:synthetic", kind: "issued", currency: "WAVE", issuer: "sim:issuer_beta" }
    },
    identical: {
      title: "Compare exact declared identity.",
      claim: "What if both synthetic records name the same currency and issuer?",
      left: { network: "xrpl:synthetic", kind: "issued", currency: "WAVE", issuer: "sim:issuer_alpha" },
      right: { network: "xrpl:synthetic", kind: "issued", currency: "WAVE", issuer: "sim:issuer_alpha" }
    },
    missing: {
      title: "Remove an essential issuer.",
      claim: "Should a ticker-only issued asset be silently accepted?",
      left: { network: "xrpl:synthetic", kind: "issued", currency: "WAVE", issuer: "sim:issuer_alpha" },
      right: { network: "xrpl:synthetic", kind: "issued", currency: "WAVE" }
    },
    crosschain: {
      title: "Challenge an invented bridge.",
      claim: "Does the same WAVE label establish a cross-chain asset or transfer?",
      left: { network: "xrpl:synthetic", kind: "issued", currency: "WAVE", issuer: "sim:issuer_alpha" },
      right: { network: "eip155:synthetic", kind: "contract", symbol: "WAVE", contract: "sim:contract_gamma" }
    },
    native: {
      title: "Give native XRP an issuer.",
      claim: "Should native XRP accept a fictional issued-asset issuer field?",
      left: { network: "xrpl:synthetic", kind: "native", currency: "XRP" },
      right: { network: "xrpl:synthetic", kind: "native", currency: "XRP", issuer: "sim:issuer_alpha" }
    }
  });

  var SYNTHETIC_ID = /^sim:[a-z][a-z0-9_]{0,63}$/;
  var CURRENCY = /^[A-Z0-9]{3,20}$/;
  var own = function (obj, key) {
    return Object.prototype.hasOwnProperty.call(obj, key);
  };
  function isObject(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
  }
  /* Reject undeclared own fields, including nonenumerable and symbol keys.
     This is a fictional record-shape check, not protocol authentication. */
  function hasExactOwnFields(record, required) {
    var actual = Reflect.ownKeys(record);
    return actual.length === required.length && required.every(function (field) {
      return own(record, field);
    });
  }
  function validate(record) {
    if (!isObject(record)) {
      return { ok: false, reason: "An input must be a declared synthetic record." };
    }
    if (record.network === "xrpl:synthetic") {
      if (record.kind === "native") {
        if (record.currency !== "XRP" || own(record, "issuer")) {
          return { ok: false, reason: "Native XRP is XRP without an issuer. An issuer field is invalid." };
        }
        if (!hasExactOwnFields(record, ["network", "kind", "currency"])) {
          return { ok: false, reason: "Native XRP fixtures must contain exactly network, kind and currency." };
        }
        return { ok: true, key: "xrpl:synthetic/native:XRP" };
      }
      if (record.kind !== "issued" || typeof record.currency !== "string" ||
          !CURRENCY.test(record.currency) ||
          typeof record.issuer !== "string" || !SYNTHETIC_ID.test(record.issuer)) {
        return {
          ok: false,
          reason: "An XRPL issued asset needs a valid synthetic currency and an explicit fictional issuer."
        };
      }
      if (!hasExactOwnFields(record, ["network", "kind", "currency", "issuer"])) {
        return { ok: false, reason: "XRPL issued-asset fixtures cannot carry undeclared identity or authority fields." };
      }
      return { ok: true, key: "xrpl:synthetic/issued:" + record.currency + "/" + record.issuer };
    }
    if (record.network === "eip155:synthetic") {
      if (record.kind !== "contract" || typeof record.symbol !== "string" ||
          !CURRENCY.test(record.symbol) ||
          typeof record.contract !== "string" || !SYNTHETIC_ID.test(record.contract)) {
        return {
          ok: false,
          reason: "An EVM synthetic contract requires its network, fictional contract and symbol."
        };
      }
      if (!hasExactOwnFields(record, ["network", "kind", "symbol", "contract"])) {
        return { ok: false, reason: "EVM synthetic contract fixtures cannot carry foreign or undeclared fields." };
      }
      return { ok: true, key: "eip155:synthetic/contract:" + record.contract };
    }
    return { ok: false, reason: "Only two explicitly synthetic test-network namespaces are supported." };
  }

  function makeResult(status, heading, explanation, rule, trace, leftKey, rightKey, missing) {
    return {
      status: status,
      heading: heading,
      explanation: explanation,
      rule: rule,
      trace: trace,
      leftKey: leftKey || "Unavailable",
      rightKey: rightKey || "Unavailable",
      missing: missing
    };
  }

  /* Pure, deterministic comparison of DECLARED identities; no RPC/source access. */
  function evaluatePair(left, right) {
    var a = validate(left);
    var b = validate(right);
    if (!a.ok || !b.ok) {
      return makeResult(
        "REFUSED",
        "Input rejected. No identity claim.",
        (a.ok ? "" : "Record A: " + a.reason + " ") +
          (b.ok ? "" : "Record B: " + b.reason),
        "Fail closed when a required native/issued/contract identity component is absent or invalid.",
        ["Validate each declared record.", "At least one record fails the synthetic identity contract.",
          "No ledger lookup, inferred issuer, or fabricated replacement is permitted."],
        a.key, b.key,
        "A valid full declared identity and any actual, independently sourced ledger evidence."
      );
    }
    if (left.network !== right.network) {
      return makeResult(
        "UNKNOWN",
        "Bridge claim unsupported.",
        "Matching display labels cannot establish a shared asset, a transfer, or a cross-chain route. " +
          "The two synthetic records have separate network-specific identifiers.",
        "Different protocols require independent verifiable source observations and linkage evidence.",
        ["Both synthetic declarations pass local shape validation.",
          "Network namespaces differ; there is no verified bridge event or consensus proof.",
          "Conclude UNKNOWN, not bridged, equivalent, successful, or fraudulent."],
        a.key, b.key,
        "A real source-pinned event from each network and authenticated linkage/finality criteria."
      );
    }
    if (a.key !== b.key) {
      return makeResult(
        "DISTINCT",
        "Two different declared assets.",
        "Even though a display label may match, the complete network-specific identifiers differ. " +
          "For XRPL issued assets, currency plus issuer identifies the asset.",
        "Compare kind, network, currency plus issuer (or the applicable chain-specific identity), never ticker alone.",
        ["Both fictional inputs pass local shape checks.",
          "Compare complete declared identity keys rather than symbols.",
          "Different keys mean distinct declarations; no real ledger existence was tested."],
        a.key, b.key,
        "Actual account/issuer existence, ledger state, balances, ownership or economic relationship."
      );
    }
    return makeResult(
      "MATCH",
      "Same declared identity key.",
      "Both fictional inputs declare the same exact chain-specific identity key. " +
        "This is equality of synthetic labels only, not proof of ledger existence or shared ownership.",
      "Match full canonical declared keys; never upgrade a local comparison into source verification.",
      ["Both synthetic declarations pass local shape validation.",
        "Complete declared identity keys compare equal.",
        "No independent consensus, source provenance, ownership, or balance was checked."],
      a.key, b.key,
      "An actual source-bound ledger observation and its independent verification."
    );
  }

  function getCase(id) {
    if (!own(CASES, id)) { return null; }
    var item = CASES[id];
    return {
      id: id,
      title: item.title,
      claim: item.claim,
      left: Object.assign({}, item.left),
      right: Object.assign({}, item.right)
    };
  }
  function listCases() {
    return Object.keys(CASES).map(function (id) {
      return { id: id, title: CASES[id].title };
    });
  }
  function mount(doc) {
    if (!doc || typeof doc.getElementById !== "function") { return false; }
    var ids = [
      "case-picker", "run-check", "reset-check", "case-title", "case-claim",
      "input-left", "input-right", "result-state", "result-title", "result-description",
      "result-rule", "result-left-key", "result-right-key", "result-missing",
      "trace-steps", "announce-status"
    ];
    var ui = {};
    ids.forEach(function (id) { ui[id] = doc.getElementById(id); });
    if (ids.some(function (id) { return !ui[id]; })) { return false; }
    function resetVerdict() {
      ui["result-state"].textContent = "NOT RUN";
      ui["result-state"].setAttribute("data-status", "UNRUN");
      ui["result-title"].textContent = "No conclusion yet.";
      ui["result-description"].textContent = "Run the local check to expose its rule and limitations.";
      ui["result-rule"].textContent = "No rule evaluated.";
      ui["result-left-key"].textContent = "Not evaluated";
      ui["result-right-key"].textContent = "Not evaluated";
      ui["result-missing"].textContent = "No independent ledger/source evidence in this demo.";
      ui["trace-steps"].replaceChildren();
      ui["announce-status"].textContent = "Ready. No case has been evaluated.";
    }
    function showCase() {
      var item = getCase(ui["case-picker"].value);
      if (!item) {
        ui["case-title"].textContent = "Unsupported case";
        ui["case-claim"].textContent = "Only predeclared fictional scenarios are accepted.";
        ui["input-left"].textContent = "No record";
        ui["input-right"].textContent = "No record";
        resetVerdict();
        return;
      }
      ui["case-title"].textContent = item.title;
      ui["case-claim"].textContent = item.claim;
      ui["input-left"].textContent = JSON.stringify(item.left, null, 2);
      ui["input-right"].textContent = JSON.stringify(item.right, null, 2);
      resetVerdict();
    }
    function runCheck() {
      var item = getCase(ui["case-picker"].value);
      var result = item ? evaluatePair(item.left, item.right) :
        makeResult("REFUSED", "Unsupported scenario", "No case was evaluated.",
          "Only fixed fictional scenarios are accepted.",
          ["Unknown scenario identifier refused."], null, null,
          "A defined synthetic scenario.");
      ui["result-state"].textContent = result.status;
      ui["result-state"].setAttribute("data-status", result.status);
      ui["result-title"].textContent = result.heading;
      ui["result-description"].textContent = result.explanation;
      ui["result-rule"].textContent = result.rule;
      ui["result-left-key"].textContent = result.leftKey;
      ui["result-right-key"].textContent = result.rightKey;
      ui["result-missing"].textContent = result.missing;
      ui["trace-steps"].replaceChildren();
      result.trace.forEach(function (line) {
        var li = doc.createElement("li");
        li.textContent = line;
        ui["trace-steps"].appendChild(li);
      });
      ui["announce-status"].textContent = result.status + ". " + result.heading;
    }
    ui["case-picker"].addEventListener("change", showCase);
    ui["run-check"].addEventListener("click", runCheck);
    ui["reset-check"].addEventListener("click", showCase);
    showCase(); /* only renders static fictional input; never evaluates or fetches */
    ui["case-picker"].disabled = false;
    ui["run-check"].disabled = false;
    ui["reset-check"].disabled = false;
    return true;
  }
  return {
    validate: validate,
    evaluatePair: evaluatePair,
    getCase: getCase,
    listCases: listCases,
    mount: mount
  };
});
