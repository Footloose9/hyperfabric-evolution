/* Original, self-contained, synthetic-only graph. No wallet, RPC, fetch or storage. */
(function () {
  "use strict";
  var NS = "http://www.w3.org/2000/svg";
  var relations = {
    funded: {color:"#71e0c5", label:"funded"},
    transferred: {color:"#6bbcf5", label:"transferred"},
    fee_sponsored: {color:"#f2c77d", label:"fee sponsored"},
    used_venue: {color:"#afafff", label:"used venue"},
    submitted: {color:"#afafff", label:"submitted"}
  };
  var views = {
    flows: ["funded", "transferred"],
    roles: ["fee_sponsored", "used_venue", "submitted"],
    all: Object.keys(relations)
  };
  /* These are invented, never actual accounts, ledgers, or assets. */
  var data = {
    nodes: [
      {id:"sim:alpha", network:"xrpl:synthetic", role:"account", label:"Alpha", x:115, y:118},
      {id:"sim:beta", network:"xrpl:synthetic", role:"account", label:"Beta", x:415, y:106},
      {id:"sim:gamma", network:"xrpl:synthetic", role:"account", label:"Gamma", x:730, y:127},
      {id:"sim:venue", network:"xrpl:synthetic", role:"amm", label:"Pool A", x:275, y:288},
      {id:"sim:batch", network:"xrpl:synthetic", role:"transaction", label:"Event T", x:690, y:288},
      {id:"sim:delta", network:"eip155:synthetic", role:"account", label:"Delta", x:185, y:135},
      {id:"sim:epsilon", network:"eip155:synthetic", role:"account", label:"Epsilon", x:495, y:130},
      {id:"sim:evmvenue", network:"eip155:synthetic", role:"amm", label:"Venue B", x:660, y:295}
    ],
    events: [
      {id:"sim:x1",network:"xrpl:synthetic",height:10},
      {id:"sim:x2",network:"xrpl:synthetic",height:11},
      {id:"sim:x3",network:"xrpl:synthetic",height:12},
      {id:"sim:v1",network:"eip155:synthetic",height:8},
      {id:"sim:v2",network:"eip155:synthetic",height:9}
    ],
    edges: [
      {source:"sim:alpha",target:"sim:beta",relation:"funded",event:"sim:x1"},
      {source:"sim:beta",target:"sim:gamma",relation:"transferred",event:"sim:x2"},
      {source:"sim:alpha",target:"sim:gamma",relation:"fee_sponsored",event:"sim:x3"},
      {source:"sim:alpha",target:"sim:venue",relation:"used_venue",event:"sim:x3"},
      {source:"sim:gamma",target:"sim:batch",relation:"submitted",event:"sim:x3"},
      {source:"sim:delta",target:"sim:epsilon",relation:"transferred",event:"sim:v1"},
      {source:"sim:epsilon",target:"sim:evmvenue",relation:"used_venue",event:"sim:v2"}
    ]
  };
  var chart = document.getElementById("evidence-graph");
  var picker = document.getElementById("network-picker");
  var title = document.getElementById("inspector-title");
  var summary = document.getElementById("inspector-summary");
  var nodeCount = document.getElementById("node-count");
  var edgeCount = document.getElementById("edge-count");
  var list = document.getElementById("edge-list");
  var buttons = Array.from(document.querySelectorAll(".filter-button"));
  if (!chart || !picker || !title || !summary || !nodeCount || !edgeCount ||
      !list || buttons.length !== 3) { return; }

  function validateFixture(fixture) {
    var nodes = new Map(), events = new Map();
    for (var node of fixture.nodes) {
      if (!/^sim:[a-z][a-z0-9_-]*$/.test(node.id) || nodes.has(node.id) ||
          !["account","amm","transaction"].includes(node.role)) { return false; }
      nodes.set(node.id,node);
    }
    for (var event of fixture.events) {
      if (!/^sim:[a-z][a-z0-9_-]*$/.test(event.id) || events.has(event.id) ||
          !Number.isSafeInteger(event.height) || event.height < 0) { return false; }
      events.set(event.id,event);
    }
    for (var edge of fixture.edges) {
      var a = nodes.get(edge.source), b = nodes.get(edge.target), e = events.get(edge.event);
      if (!a || !b || !e || !Object.prototype.hasOwnProperty.call(relations,edge.relation) ||
          a.network !== b.network || a.network !== e.network) { return false; }
      if (["funded","transferred","fee_sponsored"].includes(edge.relation) &&
          (a.role !== "account" || b.role !== "account")) { return false; }
      if (edge.relation === "used_venue" &&
          (a.role !== "account" || b.role !== "amm")) { return false; }
      if (edge.relation === "submitted" &&
          (a.role !== "account" || b.role !== "transaction")) { return false; }
    }
    return true;
  }
  if (!validateFixture(data)) {
    title.textContent = "Fixture validation refused";
    summary.textContent = "Inconsistent synthetic source relationships. Nothing was rendered.";
    return;
  }

  function svg(tag, attrs, value) {
    var element = document.createElementNS(NS,tag);
    for (var name of Object.keys(attrs || {})) {
      element.setAttribute(name,String(attrs[name]));
    }
    if (typeof value === "string") { element.textContent = value; }
    return element;
  }
  var mode = "flows";
  var selected = null;

  function inspect(id) {
    var node = data.nodes.find(function (entry) { return entry.id === id; });
    if (!node) { return; }
    selected = id;
    title.textContent = node.label + " · " + node.role;
    summary.textContent = node.id + " is a fictional " + node.role +
      " on " + node.network + ". No real ownership, misconduct or ledger activity is inferred.";
    for (var el of chart.querySelectorAll(".node")) {
      el.classList.toggle("selected",el.getAttribute("data-id") === id);
    }
  }

  function render() {
    for (var old of chart.querySelectorAll('[data-generated="true"]')) { old.remove(); }
    var nodes = data.nodes.filter(function (node) { return node.network === picker.value; });
    var lookup = new Map(nodes.map(function (node) { return [node.id,node]; }));
    var edges = data.edges.filter(function (edge) {
      return views[mode].includes(edge.relation) &&
        lookup.has(edge.source) && lookup.has(edge.target);
    });
    var defs = svg("defs",{"data-generated":"true"});
    for (var key of Object.keys(relations)) {
      var marker = svg("marker",{
        id:"arrow-"+key,viewBox:"0 0 10 10",refX:8,refY:5,
        markerWidth:6,markerHeight:6,orient:"auto-start-reverse"
      });
      marker.appendChild(svg("path",{d:"M 0 0 L 10 5 L 0 10 z",fill:relations[key].color}));
      defs.appendChild(marker);
    }
    chart.appendChild(defs);
    var edgeLayer = svg("g",{"data-generated":"true"});
    for (var edge of edges) {
      var from=lookup.get(edge.source), to=lookup.get(edge.target);
      var dx=to.x-from.x, dy=to.y-from.y, length=Math.hypot(dx,dy)||1;
      var x1=from.x+dx*35/length, y1=from.y+dy*35/length;
      var x2=to.x-dx*42/length, y2=to.y-dy*42/length;
      var group=svg("g",{"class":"edge-group"});
      group.appendChild(svg("line",{
        x1:x1,y1:y1,x2:x2,y2:y2,
        "class":"edge edge--"+edge.relation,
        "marker-end":"url(#arrow-"+edge.relation+")"
      }));
      group.appendChild(svg("text",{
        x:(x1+x2)/2,y:(y1+y2)/2-9,
        "class":"edge-label","text-anchor":"middle"
      },relations[edge.relation].label));
      group.appendChild(svg("title",{},edge.source+" to "+edge.target+
        ": "+relations[edge.relation].label+"; source "+edge.event+" (synthetic)"));
      edgeLayer.appendChild(group);
    }
    chart.appendChild(edgeLayer);
    var nodeLayer=svg("g",{"data-generated":"true"});
    for (var node of nodes) {
      var group=svg("g",{
        "class":"node node--"+node.role,
        "data-id":node.id,tabindex:0,role:"button",
        "aria-label":"Inspect fictional "+node.role+" "+node.label
      });
      group.appendChild(svg("circle",{
        cx:node.x,cy:node.y,r:30,"class":"node-circle"
      }));
      group.appendChild(svg("text",{
        x:node.x,y:node.y+53,"class":"node-label"
      },node.label));
      group.appendChild(svg("text",{
        x:node.x,y:node.y+70,"class":"node-role"
      },node.role.toUpperCase()));
      group.appendChild(svg("title",{},"Entirely fictional "+node.network+" entity"));
      (function (id) {
        group.addEventListener("click",function () { inspect(id); });
        group.addEventListener("keydown",function (ev) {
          if (ev.key === "Enter" || ev.key === " ") {
            ev.preventDefault();
            inspect(id);
          }
        });
      })(node.id);
      nodeLayer.appendChild(group);
    }
    chart.appendChild(nodeLayer);

    nodeCount.textContent=String(nodes.length);
    edgeCount.textContent=String(edges.length);
    list.replaceChildren();
    if (!edges.length) {
      var none=document.createElement("li");
      none.textContent="No directed relationships in this filter.";
      list.appendChild(none);
    }
    for (var e of edges) {
      var li=document.createElement("li");
      var a=document.createElement("code"), b=document.createElement("code");
      a.textContent=e.source.replace("sim:","");
      b.textContent=e.target.replace("sim:","");
      var relation=document.createTextNode(" → "+relations[e.relation].label+" → ");
      var source=document.createElement("span");
      source.textContent=" · "+e.event;
      li.append(a,relation,b,source);
      list.appendChild(li);
    }
    selected=null;
    title.textContent=picker.options[picker.selectedIndex].text+" evidence";
    summary.textContent="Showing "+edges.length+
      " fabricated directed relationships. Select a node to inspect a simulated role.";
  }
  picker.addEventListener("change",render);
  for (var button of buttons) {
    button.addEventListener("click",function () {
      var next=button.getAttribute("data-mode");
      if (!Object.prototype.hasOwnProperty.call(views,next)) { return; }
      mode=next;
      for (var other of buttons) {
        var active=(other===button);
        other.classList.toggle("is-active",active);
        other.setAttribute("aria-pressed",String(active));
      }
      render();
    });
  }
  render();
})();
