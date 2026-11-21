/* Public-original, dependency-free offline synthetic observation explorer.
 * This module performs no network requests, storage, signing, or RPC operations.
 * All event IDs and sources below are fictional test fixtures.
 */
(function (root, factory) {
  "use strict";
  var api = factory();
  if (typeof module === "object" && module.exports) { module.exports = api; }
  if (root && root.document) {
    root.document.addEventListener("DOMContentLoaded", function () { api.mount(root.document); });
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  var NETWORKS = Object.freeze(["xrpl:synthetic", "xahau:synthetic", "eip155:synthetic"]);
  var COVERAGE = Object.freeze(["COMPLETE", "PARTIAL", "UNKNOWN", "STALE"]);
  var H = function (letter) { return letter.repeat(64); };
  var FIXTURES = [
    { id:"sim:evt-x1", network:"xrpl:synthetic", height:101, source_hash:H("A"),
      raw_digest:H("1"), observed_at:"2026-01-01T00:00:00Z", event_type:"Payment",
      asset:{kind:"XRPL_NATIVE",code:"XRP"}, coverage:"COMPLETE",
      expected_pages:2,received_pages:2,declared_stale:false },
    { id:"sim:evt-x2", network:"xrpl:synthetic", height:102, source_hash:H("B"),
      raw_digest:H("2"), observed_at:"2026-01-01T00:00:05Z", event_type:"OfferCreate",
      asset:{kind:"XRPL_ISSUED",currency:"WAVE",issuer:"sim:issuer-alpha"}, coverage:"PARTIAL",
      expected_pages:3,received_pages:2,declared_stale:false },
    { id:"sim:evt-h1", network:"xahau:synthetic", height:75, source_hash:H("C"),
      raw_digest:H("3"), observed_at:"2026-01-01T00:00:10Z", event_type:"Synthetic event",
      asset:{kind:"XAHAU_NATIVE",code:"XAH"}, coverage:"UNKNOWN",
      expected_pages:null,received_pages:1,declared_stale:false },
    { id:"sim:evt-e1", network:"eip155:synthetic", height:44, source_hash:H("D"),
      raw_digest:H("4"), observed_at:"2025-01-01T00:00:00Z", event_type:"Synthetic contract log",
      asset:{kind:"EVM_CONTRACT",chain_id:"eip155:synthetic",contract:"sim:contract-beta",symbol:"WAVE"},
      coverage:"STALE",expected_pages:1,received_pages:1,declared_stale:true },
    { id:"sim:evt-e2", network:"eip155:synthetic", height:45, source_hash:H("E"),
      raw_digest:H("5"), observed_at:"2026-01-01T00:00:15Z", event_type:"Synthetic contract log",
      asset:{kind:"EVM_CONTRACT",chain_id:"eip155:synthetic",contract:"sim:contract-gamma",symbol:"WAVE"},
      coverage:"COMPLETE",expected_pages:1,received_pages:1,declared_stale:false }
  ];
  var ROUTES = [
    {id:"sim:route-1",source_event:"sim:evt-x2",source_network:"xrpl:synthetic",
      destination_event:null,destination_network:"eip155:synthetic",
      method:"SIMULATED_BRIDGE_CLAIM"},
    {id:"sim:route-2",source_event:"sim:evt-x1",source_network:"xrpl:synthetic",
      destination_event:"sim:evt-e2",destination_network:"eip155:synthetic",
      method:"SIMULATED_TWO_SOURCE_CORRELATION"}
  ];

  function assert(condition, message) {
    if (!condition) { throw new Error(message); }
  }
  function own(obj, key) { return Object.prototype.hasOwnProperty.call(obj,key); }
  function syntheticId(value) {
    return typeof value === "string" && /^sim:[a-z][a-z0-9-]*$/.test(value);
  }
  function isRecord(value) { return value !== null && typeof value === "object" && !Array.isArray(value); }
  function assetIdentity(asset, network) {
    assert(isRecord(asset), "asset object required");
    switch (asset.kind) {
      case "XRPL_NATIVE":
        assert(network === "xrpl:synthetic" && asset.code === "XRP", "incorrect XRPL native identity");
        return network + "/native:XRP";
      case "XRPL_ISSUED":
        assert(network === "xrpl:synthetic" && typeof asset.currency === "string" &&
          /^[A-Za-z0-9]{3,20}$/.test(asset.currency) && syntheticId(asset.issuer),
          "issued asset must specify exact synthetic currency and issuer");
        return network + "/issued:" + asset.currency + "/" + asset.issuer;
      case "XAHAU_NATIVE":
        assert(network === "xahau:synthetic" && asset.code === "XAH", "incorrect Xahau native identity");
        return network + "/native:XAH";
      case "EVM_CONTRACT":
        assert(network === "eip155:synthetic" && asset.chain_id === network &&
          syntheticId(asset.contract) && typeof asset.symbol === "string",
          "EVM token requires explicit network and contract");
        return network + "/contract:" + asset.contract;
      default:
        throw new Error("unsupported asset kind");
    }
  }
  function validateObservation(observation) {
    assert(isRecord(observation), "observation object required");
    assert(syntheticId(observation.id), "fictional event identifier required");
    assert(NETWORKS.includes(observation.network), "unsupported or non-synthetic network");
    assert(Number.isSafeInteger(observation.height) && observation.height >= 0, "invalid source height");
    assert(typeof observation.source_hash === "string" &&
      /^[A-Fa-f0-9]{64}$/.test(observation.source_hash), "invalid fabricated source hash");
    assert(typeof observation.raw_digest === "string" &&
      /^[A-Fa-f0-9]{64}$/.test(observation.raw_digest), "invalid fabricated raw digest");
    assert(typeof observation.observed_at === "string" &&
      /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/.test(observation.observed_at) &&
      !Number.isNaN(Date.parse(observation.observed_at)), "invalid observed UTC");
    assert(typeof observation.event_type === "string" && observation.event_type.length > 0,
      "event type required");
    assert(COVERAGE.includes(observation.coverage), "unrecognized coverage classification");
    assert(Number.isSafeInteger(observation.received_pages) && observation.received_pages >= 0,
      "invalid received page count");
    assert(observation.expected_pages === null || (Number.isSafeInteger(observation.expected_pages) &&
      observation.expected_pages > 0), "invalid expected page count");
    if (observation.coverage === "COMPLETE") {
      assert(observation.expected_pages !== null &&
        observation.received_pages === observation.expected_pages &&
        observation.declared_stale === false, "false complete coverage");
    } else if (observation.coverage === "PARTIAL") {
      assert(observation.expected_pages !== null &&
        observation.received_pages < observation.expected_pages &&
        observation.declared_stale === false, "false partial coverage");
    } else if (observation.coverage === "UNKNOWN") {
      assert(observation.expected_pages === null && observation.declared_stale === false,
        "unknown coverage cannot assert expected completeness");
    } else {
      assert(observation.declared_stale === true, "staleness must be explicitly declared");
      assert(observation.expected_pages === null ||
        observation.received_pages <= observation.expected_pages, "invalid stale page totals");
    }
    assert(!own(observation,"validated") && !own(observation,"provider_verified") &&
      !own(observation,"live"), "synthetic fixtures cannot claim live finality");
    var asset_key = assetIdentity(observation.asset, observation.network);
    return Object.freeze({id:observation.id, network:observation.network, height:observation.height,
      source_hash:observation.source_hash,raw_digest:observation.raw_digest,
      observed_at:observation.observed_at,event_type:observation.event_type,
      coverage:observation.coverage,expected_pages:observation.expected_pages,
      received_pages:observation.received_pages,asset_key:asset_key,
      provenance_class:"SIMULATED",finality:"NOT_APPLICABLE"});
  }
  function validateDataset(fixtures) {
    assert(Array.isArray(fixtures), "fixture array required");
    var result = [], ids = new Set();
    for (var record of fixtures) {
      var item = validateObservation(record);
      assert(!ids.has(item.id), "duplicate synthetic event");
      ids.add(item.id);
      result.push(item);
    }
    return Object.freeze(result);
  }
  function assessRoute(route, observations) {
    assert(isRecord(route) && syntheticId(route.id), "invalid synthetic route");
    assert(Array.isArray(observations), "observation array required");
    assert(NETWORKS.includes(route.source_network) && NETWORKS.includes(route.destination_network) &&
      route.source_network !== route.destination_network, "cross-chain network identity required");
    var source = observations.find(function (x) { return x.id === route.source_event; });
    assert(source && source.network === route.source_network, "missing or mismatched source event");
    if (route.destination_event === null) { return "INCONCLUSIVE_SOURCE_ONLY"; }
    assert(syntheticId(route.destination_event), "invalid destination event");
    var destination = observations.find(function (x) { return x.id === route.destination_event; });
    if (!destination) { return "INCONCLUSIVE_DESTINATION_UNOBSERVED"; }
    assert(destination.network === route.destination_network, "destination network mismatch");
    // Two fictional observations cannot establish a real completed bridge transfer.
    return "SIMULATED_CORRELATION_ONLY";
  }
  function mount(doc) {
    var filter = doc.getElementById("network-filter");
    var rows = doc.getElementById("observation-rows");
    var detail = doc.getElementById("observation-detail");
    var counter = doc.getElementById("observation-count");
    var routes = doc.getElementById("route-results");
    if (!filter || !rows || !detail || !counter || !routes) { return; }
    var observations;
    try { observations = validateDataset(FIXTURES); }
    catch (error) { detail.textContent = "Fixture refused: " + error.message; return; }
    function add(tag, parent, value) {
      var item = doc.createElement(tag);
      item.textContent = String(value);
      parent.appendChild(item);
      return item;
    }
    function inspect(item) {
      detail.replaceChildren();
      add("h3",detail,item.id + " / " + item.event_type);
      var dl = add("dl",detail,"");
      [
        ["Evidence class",item.provenance_class],
        ["Network",item.network],
        ["Exact asset identity",item.asset_key],
        ["Fabricated height",item.height],
        ["Fabricated source hash",item.source_hash],
        ["Fabricated content digest",item.raw_digest],
        ["Source timestamp",item.observed_at],
        ["Coverage (fixture only)",item.coverage],
        ["Received / expected pages",item.received_pages + " / " +
          (item.expected_pages === null ? "UNKNOWN" : item.expected_pages)],
        ["Ledger finality",item.finality]
      ].forEach(function (pair) { add("dt",dl,pair[0]); add("dd",dl,pair[1]); });
    }
    function render() {
      rows.replaceChildren();
      var visible = observations.filter(function (item) {
        return filter.value === "all" || item.network === filter.value;
      });
      counter.textContent = visible.length + " / " + observations.length + " fictional observations";
      visible.forEach(function (item) {
        var tr = doc.createElement("tr");
        var th = doc.createElement("th");
        th.scope = "row";
        var button = add("button",th,item.id);
        button.type = "button";
        button.setAttribute("aria-label","Inspect " + item.id);
        button.addEventListener("click",function () { inspect(item); });
        tr.appendChild(th);
        add("td",tr,item.network);
        add("td",tr,item.event_type);
        add("td",tr,item.coverage);
        add("td",tr,item.provenance_class);
        rows.appendChild(tr);
      });
      if (visible.length) { inspect(visible[0]); }
      else { detail.textContent = "No fictional events in this selection."; }
    }
    filter.addEventListener("change",render);
    routes.replaceChildren();
    ROUTES.forEach(function (route) {
      var status;
      try { status = assessRoute(route,observations); }
      catch (error) { status = "REFUSED: " + error.message; }
      add("li",routes,route.id + " / " + route.method + " / " + status);
    });
    render();
  }
  return {NETWORKS:NETWORKS, FIXTURES:FIXTURES, ROUTES:ROUTES, assetIdentity:assetIdentity,
    validateObservation:validateObservation,validateDataset:validateDataset,
    assessRoute:assessRoute,mount:mount};
});
