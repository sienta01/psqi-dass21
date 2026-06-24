/* Wizard multi-langkah + validasi sisi-klien untuk form kuesioner. */
(function () {
  "use strict";

  var form = document.getElementById("kuesioner");
  if (!form) return;

  var steps = Array.prototype.slice.call(form.querySelectorAll(".form-step"));
  var pills = Array.prototype.slice.call(document.querySelectorAll(".step-pill"));
  var current = 0;

  /* Cegah tombol Enter pada input satu baris men-submit form lebih awal
     (form ini bertahap; submit hanya lewat tombol di langkah terakhir). */
  form.addEventListener("keydown", function (e) {
    if (e.key !== "Enter") return;
    var t = e.target;
    if (t.tagName === "INPUT" && t.type !== "submit" && t.type !== "button") {
      e.preventDefault();
    }
  });

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


/* Autolengkap "Nama Responden": pilih pasien yang ada -> mode pengukuran akhir.
   Hanya aktif untuk admin (atribut data-can-search). */
(function () {
  "use strict";
  var form = document.getElementById("kuesioner");
  if (!form || form.getAttribute("data-can-search") !== "1") return;

  var input = document.getElementById("nama");
  var list = document.getElementById("nama-ac-list");
  var parentInput = document.getElementById("parent_id");
  var banner = document.getElementById("akhir-pilih-banner");
  var bannerNama = document.getElementById("akhir-pilih-nama");
  var batal = document.getElementById("akhir-pilih-batal");
  var cariUrl = form.getAttribute("data-cari-url");
  var pasienTmpl = form.getAttribute("data-pasien-tmpl"); // .../0/data
  if (!input || !list || !parentInput) return;

  var timer = null;
  var currentItems = [];
  var activeIndex = -1;
  var lastQuery = "";

  function setParent(id) {
    parentInput.value = id || "";
    if (banner) banner.hidden = !id;
  }

  function hideList() {
    list.hidden = true; list.innerHTML = "";
    currentItems = []; activeIndex = -1;
    input.setAttribute("aria-expanded", "false");
  }

  function setActive(i) {
    activeIndex = i;
    var els = list.querySelectorAll(".ac-item");
    els.forEach(function (el, idx) {
      var on = idx === i;
      el.classList.toggle("active", on);
      if (on) el.scrollIntoView({ block: "nearest" });
    });
  }

  input.addEventListener("input", function () {
    setParent("");                 // mengetik ulang membatalkan pilihan
    var q = input.value.trim();
    clearTimeout(timer);
    if (q.length < 2) { hideList(); return; }
    timer = setTimeout(function () {
      fetchMatches(q).then(function (items) { renderList(items, q); });
    }, 250);
  });

  // Navigasi keyboard: panah untuk memilih, Enter memilih / lanjut, Esc tutup.
  input.addEventListener("keydown", function (e) {
    if (e.key === "ArrowDown") {
      if (!list.hidden && currentItems.length) {
        e.preventDefault(); setActive(Math.min(activeIndex + 1, currentItems.length - 1));
      }
    } else if (e.key === "ArrowUp") {
      if (!list.hidden && currentItems.length) {
        e.preventDefault(); setActive(Math.max(activeIndex - 1, 0));
      }
    } else if (e.key === "Enter") {
      e.preventDefault();
      handleEnter();
    } else if (e.key === "Escape") {
      hideList();
    }
  });

  function fetchMatches(q) {
    return fetch(cariUrl + "?q=" + encodeURIComponent(q))
      .then(function (r) { return r.ok ? r.json() : []; })
      .catch(function () { return []; });
  }

  /* Enter:
     - pasien sudah dipilih  -> maju ke langkah berikutnya
     - ada pasien cocok       -> pilih & muat datanya (tetap di langkah 1 untuk
                                 diperiksa)
     - tidak ada yang cocok   -> lanjut sebagai pasien baru */
  function handleEnter() {
    if (parentInput.value) { goNext(); return; }   // sudah memilih pasien
    var q = input.value.trim();
    if (!list.hidden && currentItems.length && lastQuery === q) {
      pilih(currentItems[activeIndex >= 0 ? activeIndex : 0]);
      return;
    }
    if (q.length < 2) { proceedNew(); return; }
    clearTimeout(timer);
    fetchMatches(q).then(function (items) {
      if (items && items.length) { pilih(items[0]); }
      else { proceedNew(); }
    });
  }

  function goNext() {
    hideList();
    var nextBtn = form.querySelector('.form-step[data-step="0"] [data-next]');
    if (nextBtn) nextBtn.click();
  }

  function proceedNew() { setParent(""); goNext(); }

  function renderList(items, q) {
    currentItems = items || [];
    lastQuery = q || input.value.trim();
    list.innerHTML = "";
    if (!currentItems.length) { hideList(); return; }
    currentItems.forEach(function (it, idx) {
      var el = document.createElement("div");
      el.className = "ac-item";
      el.setAttribute("role", "option");
      var nama = document.createElement("span");
      nama.className = "ac-nama";
      nama.textContent = it.nama || "(tanpa nama)";
      var meta = document.createElement("span");
      meta.className = "ac-meta";
      meta.textContent = [it.no_rm ? "RM " + it.no_rm : "",
                          it.tanggal ? "awal " + it.tanggal : ""]
                         .filter(Boolean).join(" • ");
      el.appendChild(nama); el.appendChild(meta);
      el.addEventListener("mousedown", function (e) { e.preventDefault(); pilih(it); });
      el.addEventListener("mousemove", function () { setActive(idx); });
      list.appendChild(el);
    });
    list.hidden = false;
    setActive(0);   // sorot item pertama agar Enter langsung memilihnya
    input.setAttribute("aria-expanded", "true");
  }

  function pilih(it) {
    hideList();
    input.value = it.nama || input.value;
    setParent(it.id);
    if (bannerNama) bannerNama.textContent = it.nama || "";
    var url = pasienTmpl.replace("/0/", "/" + it.id + "/");
    fetch(url)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { if (d && d.demografi) fillDemografi(d.demografi); });
  }

  function fillDemografi(demo) {
    Object.keys(demo).forEach(function (name) {
      if (name === "tanggal" || name === "nama") return; // tanggal akhir = hari ini
      var val = demo[name];
      var radios = form.querySelectorAll('input[type="radio"][name="' + name + '"]');
      if (radios.length) {
        radios.forEach(function (r) { r.checked = (r.value === val); });
        return;
      }
      var f = form.querySelector('[name="' + name + '"]');
      if (!f) return;
      if (f.type === "checkbox") {
        f.checked = ["1", "on", "true", "Ya"].indexOf(String(val)) !== -1;
      } else {
        f.value = val || "";
      }
    });
    // Sinkronkan kotak "lainnya" (mis. keterangan intervensi).
    form.querySelectorAll("[data-show-when]").forEach(function (box) {
      var spec = box.getAttribute("data-show-when").split("=");
      var checked = form.querySelector('input[name="' + spec[0] + '"]:checked');
      box.style.display = (checked && checked.value === spec[1]) ? "" : "none";
    });
  }

  /* Batal pilihan: lepas tautan akhir + kosongkan data yang tadi tersalin,
     kembali ke kondisi pasien baru. */
  function cancelSelection() {
    setParent("");
    hideList();
    var step0 = form.querySelector('.form-step[data-step="0"]');
    if (step0) {
      step0.querySelectorAll("input").forEach(function (el) {
        if (el.type === "radio" || el.type === "checkbox") el.checked = false;
        else if (el.type !== "hidden") el.value = "";
      });
      step0.querySelectorAll(".has-error").forEach(function (el) {
        el.classList.remove("has-error");
      });
    }
    var tgl = form.querySelector('[name="tanggal"]');
    if (tgl) {
      // Tanggal hari ini di UTC+8 (lepas dari zona waktu browser).
      var d = new Date(Date.now() + 8 * 3600 * 1000);
      tgl.value = d.getUTCFullYear() + "-" +
        String(d.getUTCMonth() + 1).padStart(2, "0") + "-" +
        String(d.getUTCDate()).padStart(2, "0");
    }
    form.querySelectorAll("[data-show-when]").forEach(function (box) {
      box.style.display = "none";
    });
    input.focus();
  }

  if (batal) batal.addEventListener("click", function (e) {
    e.preventDefault(); cancelSelection();
  });
  document.addEventListener("click", function (e) {
    if (!e.target.closest("#nama-autocomplete")) hideList();
  });
})();
