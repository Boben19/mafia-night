/* Mafia Night front-end. No libraries. */
(function () {
  "use strict";
  var calm = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

  function store(key, val) {
    try {
      if (val === undefined) return sessionStorage.getItem(key);
      sessionStorage.setItem(key, val);
    } catch (e) { return null; }
  }

  /* ---------- the hat's eyes follow your finger or cursor ---------- */
  var hats = [].slice.call(document.querySelectorAll(".hat"));
  function look(x, y) {
    hats.forEach(function (h) {
      var r = h.getBoundingClientRect();
      if (!r.width) return;
      var dx = x - (r.left + r.width / 2), dy = y - (r.top + r.height * 0.72);
      var d = Math.max(Math.hypot(dx, dy), 1), k = Math.min(d / 160, 1) * 3;
      var tx = (dx / d) * k, ty = (dy / d) * k;
      [].forEach.call(h.querySelectorAll(".pupil"), function (p) {
        p.style.transform = "translate(" + tx.toFixed(2) + "px," + ty.toFixed(2) + "px)";
      });
    });
  }
  if (hats.length) {
    addEventListener("pointermove", function (e) { look(e.clientX, e.clientY); }, { passive: true });
  }

  /* ---------- spotlight on the home hero ---------- */
  var hero = document.querySelector(".hero");
  if (hero) {
    var move = function (e) {
      var r = hero.getBoundingClientRect();
      hero.style.setProperty("--mx", (e.clientX - r.left) + "px");
      hero.style.setProperty("--my", (e.clientY - r.top) + "px");
    };
    addEventListener("pointermove", move, { passive: true });
  }

  /* ---------- avatar colors come from the name ---------- */
  [].forEach.call(document.querySelectorAll(".avatar[data-name]"), function (a) {
    var s = a.dataset.name, h = 0;
    for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 360;
    a.style.setProperty("--h", h);
  });

  /* ---------- messages fade away on their own ---------- */
  [].forEach.call(document.querySelectorAll(".toast"), function (t, i) {
    var bye = function () { t.classList.add("leaving"); setTimeout(function () { t.remove(); }, 400); };
    t.addEventListener("click", bye);
    setTimeout(bye, 5200 + i * 600);
  });

  /* ---------- copy the room code ---------- */
  var code = document.getElementById("copycode");
  if (code) {
    code.addEventListener("click", function () {
      var txt = code.dataset.code, note = document.getElementById("copied");
      var done = function () { if (note) { note.textContent = "Code copied. Send it to your crew."; setTimeout(function () { note.textContent = ""; }, 2500); } };
      if (navigator.clipboard) navigator.clipboard.writeText(txt).then(done, done); else done();
    });
  }

  /* ---------- the secret card ---------- */
  var card = document.getElementById("rolecard");
  if (card) {
    var timer;
    var setOpen = function (open) {
      card.classList.toggle("open", open);
      card.setAttribute("aria-pressed", open ? "true" : "false");
      var front = card.querySelector(".front"), back = card.querySelector(".back");
      if (front) front.setAttribute("aria-hidden", open ? "false" : "true");
      if (back) back.setAttribute("aria-hidden", open ? "true" : "false");
      clearTimeout(timer);
      if (open) timer = setTimeout(function () { setOpen(false); }, 10000); // nosy neighbours
    };
    card.addEventListener("click", function () { setOpen(!card.classList.contains("open")); });
    card.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setOpen(!card.classList.contains("open")); }
    });
  }

  /* ---------- role pickers for the MC ---------- */
  var deal = document.getElementById("dealform");
  if (deal) {
    var inputs = [].slice.call(deal.querySelectorAll(".stepper input"));
    var players = +deal.dataset.players || 0;
    var sum = document.getElementById("picked"), left = document.getElementById("leftover"), tally = deal.querySelector(".tally");
    var refresh = function () {
      var n = 0;
      inputs.forEach(function (i) {
        var v = Math.max(0, Math.min(9, parseInt(i.value, 10) || 0));
        i.value = v; n += v;
        i.closest(".pick").classList.toggle("on", v > 0);
      });
      sum.textContent = n;
      var diff = players - n;
      left.textContent = diff >= 0 ? diff + " will be plain Citizens." : "That's " + (-diff) + " too many roles for this table.";
      tally.classList.toggle("bad", diff < 0 || players < 4);
    };
    deal.addEventListener("click", function (e) {
      var b = e.target.closest("[data-step]");
      if (!b) return;
      var i = b.parentNode.querySelector("input");
      i.value = (parseInt(i.value, 10) || 0) + (+b.dataset.step);
      refresh();
    });
    deal.addEventListener("input", refresh);
    var byName = function (n) { return inputs.filter(function (i) { return i.dataset.name === n; })[0]; };
    var clear = function () { inputs.forEach(function (i) { i.value = 0; }); };
    var suggest = document.getElementById("suggest");
    if (suggest) suggest.addEventListener("click", function () {
      clear();
      var m = byName("Mafia"), d = byName("Detective"), doc = byName("Doctor");
      if (m) m.value = Math.max(1, Math.round(players / 4));
      if (players >= 5 && d) d.value = 1;
      if (players >= 6 && doc) doc.value = 1;
      refresh();
    });
    var wipe = document.getElementById("wipe");
    if (wipe) wipe.addEventListener("click", function () { clear(); refresh(); });
    refresh();
  }

  /* ---------- room: curtain on phase change, confetti, live refresh ---------- */
  var room = document.getElementById("room");
  if (room) {
    var phase = room.dataset.phase, code4 = room.dataset.code;
    var key = "phase_" + code4, before = store(key);
    store(key, phase);

    var curtain = document.getElementById("curtain");
    if (curtain && !calm && before && before !== phase) {
      var icon = { night: "i-moon", day: "i-sun", over: "i-trophy", lobby: "i-hat" }[phase] || "i-moon";
      curtain.querySelector("use").setAttribute("href", "#" + icon);
      curtain.querySelector("span").textContent = room.dataset.label;
      curtain.classList.add("on");
      void curtain.offsetWidth;
      setTimeout(function () { curtain.classList.add("open"); }, 750);
      setTimeout(function () { curtain.classList.remove("on", "open"); }, 2000);
    }

    if (phase === "over" && !calm && store("won_" + code4 + room.dataset.winner) === null) {
      store("won_" + code4 + room.dataset.winner, "1");
      setTimeout(confetti, before && before !== phase ? 1500 : 200);
    }

    var sig = room.dataset.sig, url = room.dataset.ping, busy = false;
    setInterval(function () {
      if (busy || document.hidden) return;
      var el = document.activeElement;
      if (el && ["INPUT", "TEXTAREA", "SELECT"].indexOf(el.tagName) > -1) return;
      var picking = [].some.call(document.querySelectorAll("#dealform input[type=number]"), function (i) { return +i.value > 0; });
      if (picking) return;
      busy = true;
      fetch(url, { cache: "no-store" })
        .then(function (r) { return r.text(); })
        .then(function (s) { busy = false; if (s !== sig) location.reload(); })
        .catch(function () { busy = false; });
    }, 3000);
  }

  function confetti() {
    var c = document.createElement("canvas");
    c.id = "confetti";
    document.body.appendChild(c);
    var x = c.getContext("2d"), W = c.width = innerWidth, H = c.height = innerHeight;
    var cols = ["#e3b04b", "#f3c866", "#c0273a", "#efe4d3", "#8a6be0"];
    var bits = [];
    for (var i = 0; i < 140; i++) bits.push({
      x: Math.random() * W, y: -20 - Math.random() * H * 0.6, w: 6 + Math.random() * 6, h: 8 + Math.random() * 8,
      vy: 2 + Math.random() * 3, vx: -1 + Math.random() * 2, a: Math.random() * 6, va: -.15 + Math.random() * .3,
      c: cols[i % cols.length]
    });
    var t0 = performance.now();
    (function frame(t) {
      x.clearRect(0, 0, W, H);
      bits.forEach(function (b) {
        b.x += b.vx; b.y += b.vy; b.a += b.va;
        x.save(); x.translate(b.x, b.y); x.rotate(b.a);
        x.fillStyle = b.c; x.fillRect(-b.w / 2, -b.h / 2, b.w, b.h); x.restore();
      });
      if (t - t0 < 5200) requestAnimationFrame(frame); else c.remove();
    })(t0);
  }
})();
