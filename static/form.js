/* Wizard multi-langkah + validasi sisi-klien untuk form kuesioner. */
(function () {
  "use strict";

  var form = document.getElementById("kuesioner");
  if (!form) return;

  var steps = Array.prototype.slice.call(form.querySelectorAll(".form-step"));
  var pills = Array.prototype.slice.call(document.querySelectorAll(".step-pill"));
  var current = 0;

  function showStep(i) {
    current = i;
    steps.forEach(function (s, idx) { s.classList.toggle("is-hidden", idx !== i); });
    pills.forEach(function (p, idx) {
      p.classList.toggle("active", idx === i);
      p.classList.toggle("done", idx < i);
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  /* Cari kontainer untuk ditandai error. */
  function containerOf(input) {
    return input.closest(".matrix-row, .dass-row, .field");
  }

  /* Validasi satu langkah. Kembalikan elemen invalid pertama (atau null). */
  function validateStep(stepEl, markErrors) {
    var firstInvalid = null;
    var seenRadioGroups = {};
    var required = stepEl.querySelectorAll("[data-required]");

    required.forEach(function (input) {
      var invalid = false;
      if (input.type === "radio") {
        if (seenRadioGroups[input.name]) return;
        seenRadioGroups[input.name] = true;
        invalid = !stepEl.querySelector('input[name="' + input.name + '"]:checked');
      } else {
        invalid = !input.value.trim();
      }
      var box = containerOf(input);
      if (markErrors && box) box.classList.toggle("has-error", invalid);
      if (invalid && !firstInvalid) firstInvalid = box || input;
    });
    return firstInvalid;
  }

  /* Bersihkan tanda error pada kontainer saat pengguna mengisi. */
  form.addEventListener("change", function (e) {
    var box = containerOf(e.target);
    if (box && box.classList.contains("has-error")) {
      // cek ulang ringan
      var stillBad = false;
      var req = box.querySelectorAll("[data-required]");
      req.forEach(function (input) {
        if (input.type === "radio") {
          if (!box.querySelector('input[name="' + input.name + '"]:checked')) stillBad = true;
        } else if (!input.value.trim()) stillBad = true;
      });
      box.classList.toggle("has-error", stillBad);
    }
  });

  /* Navigasi tombol. */
  form.addEventListener("click", function (e) {
    if (e.target.matches("[data-next]")) {
      var invalid = validateStep(steps[current], true);
      if (invalid) {
        invalid.scrollIntoView({ behavior: "smooth", block: "center" });
        flashHint("Mohon lengkapi isian yang ditandai sebelum melanjutkan.");
        return;
      }
      if (current < steps.length - 1) showStep(current + 1);
    } else if (e.target.matches("[data-prev]")) {
      if (current > 0) showStep(current - 1);
    }
  });

  /* Klik pada pill untuk pindah (hanya mundur atau setelah valid). */
  pills.forEach(function (p, idx) {
    p.addEventListener("click", function () {
      if (idx <= current) { showStep(idx); return; }
      // maju: validasi langkah-langkah di antaranya
      for (var s = current; s < idx; s++) {
        var inv = validateStep(steps[s], true);
        if (inv) { showStep(s); inv.scrollIntoView({ behavior: "smooth", block: "center" }); return; }
      }
      showStep(idx);
    });
  });

  /* Validasi akhir saat submit. */
  form.addEventListener("submit", function (e) {
    for (var i = 0; i < steps.length; i++) {
      var invalid = validateStep(steps[i], true);
      if (invalid) {
        e.preventDefault();
        showStep(i);
        invalid.scrollIntoView({ behavior: "smooth", block: "center" });
        flashHint("Masih ada isian wajib yang kosong pada bagian ini.");
        return;
      }
    }
  });

  /* Toggle kotak "lainnya" (mis. tindakan intervensi = Ya). */
  var otherBoxes = Array.prototype.slice.call(document.querySelectorAll("[data-show-when]"));
  otherBoxes.forEach(function (box) {
    var spec = box.getAttribute("data-show-when").split("=");
    var name = spec[0], val = spec[1];
    function sync() {
      var checked = form.querySelector('input[name="' + name + '"]:checked');
      box.style.display = (checked && checked.value === val) ? "" : "none";
    }
    form.addEventListener("change", function (e) {
      if (e.target.name === name) sync();
    });
    sync();
  });

  /* Hint sementara. */
  var hintEl = null, hintTimer = null;
  function flashHint(msg) {
    if (!hintEl) {
      hintEl = document.createElement("div");
      hintEl.className = "flash flash-error";
      hintEl.style.position = "sticky";
      hintEl.style.top = "70px";
      hintEl.style.zIndex = "40";
      form.prepend(hintEl);
    }
    hintEl.textContent = msg;
    hintEl.style.display = "";
    clearTimeout(hintTimer);
    hintTimer = setTimeout(function () { if (hintEl) hintEl.style.display = "none"; }, 4000);
  }

  showStep(0);
})();
