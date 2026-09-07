const BASE_PATH = window.BASE_PATH || "/";

let assets = [];
let index = 0;
let showDesc = false;
let editing = false;
let mode = "grid";
let canEdit = false;

let autoDescTimer = null;
let descDelayTimer = null;
let autoPlayTimer = null;
let autoPlayPaused = false;
let toastTimer = null;

const AUTO_PLAY_DELAY = 5000;
const DESC_DELAY = 700;
const DESC_BASE_DURATION = 1500;
const BASE_SLIDE_DELAY = 5000;
const DESC_MS_PER_CHAR = 35;
const DESC_MAX_DURATION = 8000;

const imageEl = document.getElementById("image");
const descEl = document.getElementById("desc");
const editorEl = document.getElementById("editor");
const editTextEl = document.getElementById("editText");
const counterEl = document.getElementById("counter");
const albumNameEl = document.getElementById("albumName");
const loadingEl = document.getElementById("loading");
const errorEl = document.getElementById("error");
const gridEl = document.getElementById("grid");

function showToast(message) {
  let toastEl = document.getElementById("toast");

  if (!toastEl) {
    toastEl = document.createElement("div");
    toastEl.id = "toast";
    document.body.appendChild(toastEl);
  }

  toastEl.textContent = message;
  toastEl.classList.remove("hidden");

  if (toastTimer) clearTimeout(toastTimer);

  toastTimer = setTimeout(() => {
    toastEl.classList.add("hidden");
  }, 2500);
}

function currentSlideDelay() {
  const asset = currentAsset();
  const text = (asset?.description || "").trim();

  if (!text) return BASE_SLIDE_DELAY;

  const extra = Math.min(DESC_MAX_DURATION, text.length * DESC_MS_PER_CHAR);
  return BASE_SLIDE_DELAY + extra;
}

function currentDescriptionDuration() {
  const asset = currentAsset();
  const text = (asset?.description || "").trim();

  if (!text) return 0;

  return Math.min(
    DESC_MAX_DURATION,
    DESC_BASE_DURATION + text.length * DESC_MS_PER_CHAR
  );
}

function apiUrl(path) {
  return `${BASE_PATH}api${path}${window.location.search || ""}`;
}

function currentAsset() {
  return assets[index];
}

function clearAutoDescriptionTimers() {
  if (autoDescTimer) clearTimeout(autoDescTimer);
  if (descDelayTimer) clearTimeout(descDelayTimer);
  autoDescTimer = null;
  descDelayTimer = null;
}

function clearAutoPlayTimer() {
  if (autoPlayTimer) clearTimeout(autoPlayTimer);
  autoPlayTimer = null;
}

function scheduleAutoPlay() {
  clearAutoPlayTimer();

  if (mode !== "slideshow") return;
  if (editing) return;
  if (autoPlayPaused) return;
  if (!assets.length) return;

  autoPlayTimer = setTimeout(() => {
    nextImage();
  }, currentSlideDelay());
}

function updateCounter() {
  const pauseMark = autoPlayPaused ? " — pause" : "";
  counterEl.textContent = assets.length ? `${index + 1} / ${assets.length}${pauseMark}` : "";
}

function updateDescription() {
  const asset = currentAsset();
  if (!asset) {
    descEl.textContent = "";
    descEl.classList.add("hidden");
    return;
  }

  descEl.textContent = asset.description || "";
  if (showDesc && asset.description && mode === "slideshow") {
    descEl.classList.remove("hidden");
  } else {
    descEl.classList.add("hidden");
  }
}

function showTemporaryDescription() {
  const asset = currentAsset();

  clearAutoDescriptionTimers();

  if (!asset) return;
  if (mode !== "slideshow") return;
  if (showDesc) return;
  if (!asset.description) return;

  descDelayTimer = setTimeout(() => {
    descEl.textContent = asset.description;
    descEl.classList.remove("hidden");

    autoDescTimer = setTimeout(() => {
      if (!showDesc) {
        descEl.classList.add("hidden");
      }
    }, currentDescriptionDuration());
  }, DESC_DELAY);
}

function showImage() {
  const asset = currentAsset();
  if (!asset) return;

  imageEl.src = apiUrl(`/assets/${asset.id}/image`);
  updateCounter();
  updateDescription();
  highlightCurrentThumb();
  showTemporaryDescription();
  scheduleAutoPlay();
}

function nextImage() {
  if (mode !== "slideshow") return;
  if (!assets.length) return;
  index = (index + 1) % assets.length;
  showImage();
}

function prevImage() {
  if (mode !== "slideshow") return;
  if (!assets.length) return;
  index = (index - 1 + assets.length) % assets.length;
  showImage();
}

function toggleDescription() {
  if (mode !== "slideshow") return;
  clearAutoDescriptionTimers();
  showDesc = !showDesc;
  updateDescription();
}

function toggleAutoPlayPause() {
  if (mode !== "slideshow") return;

  if (autoPlayPaused) {
    autoPlayPaused = false;
    updateCounter();
    nextImage();
  } else {
    autoPlayPaused = true;
    updateCounter();
    clearAutoPlayTimer();
  }
}

function startEdit() {
  if (mode !== "slideshow") return;

  if (!canEdit) {
    showToast("Mode visiteur : édition des descriptions non autorisée");
    return;
  }

  const asset = currentAsset();
  if (!asset) return;

  clearAutoDescriptionTimers();
  clearAutoPlayTimer();

  editing = true;
  editTextEl.value = asset.description || "";
  editorEl.classList.remove("hidden");
  editTextEl.focus();
  editTextEl.select();
}

function cancelEdit() {
  editing = false;
  editorEl.classList.add("hidden");
  showTemporaryDescription();
  scheduleAutoPlay();
}

async function saveEdit() {
  const asset = currentAsset();
  if (!asset) return;

  const newDesc = editTextEl.value;

  const res = await fetch(apiUrl(`/assets/${asset.id}/description`), {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description: newDesc }),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || "Erreur d'enregistrement");
  }

  asset.description = newDesc;
  editing = false;
  editorEl.classList.add("hidden");
  updateDescription();
  showTemporaryDescription();
  scheduleAutoPlay();
}

function renderGrid() {
  gridEl.innerHTML = "";

  assets.forEach((asset, i) => {
    const div = document.createElement("div");
    div.className = "thumb";
    div.dataset.index = i;

    const img = document.createElement("img");
    img.src = apiUrl(`/assets/${asset.id}/thumbnail`);
    img.alt = asset.originalFileName || `Photo ${i + 1}`;

    div.appendChild(img);

    div.addEventListener("click", () => {
      index = i;
      mode = "slideshow";
      updateView();
    });

    gridEl.appendChild(div);
  });

  highlightCurrentThumb();
}

function highlightCurrentThumb() {
  const thumbs = gridEl.querySelectorAll(".thumb");
  thumbs.forEach((thumb, i) => {
    if (i === index) {
      thumb.classList.add("active");
    } else {
      thumb.classList.remove("active");
    }
  });
}

function updateView() {
  if (mode === "grid") {
    clearAutoDescriptionTimers();
    clearAutoPlayTimer();

    gridEl.classList.remove("hidden");
    imageEl.classList.add("hidden");
    descEl.classList.add("hidden");
  } else {
    gridEl.classList.add("hidden");
    imageEl.classList.remove("hidden");
    showImage();
  }
}

async function loadAssets() {
  const res = await fetch(apiUrl("/assets"));
  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.error || "Erreur de chargement");
  }

  assets = data.assets || [];
  canEdit = !!data.canEdit;
  albumNameEl.textContent = data.albumName || "";

  loadingEl.classList.add("hidden");

  if (!assets.length) {
    throw new Error("Aucune image trouvée dans l'album.");
  }

  renderGrid();
  mode = "grid";
  updateView();
}

document.addEventListener("keydown", async (e) => {
  if (editing) {
    if (e.key === "Escape") {
      e.preventDefault();
      cancelEdit();
      return;
    }

    if (e.ctrlKey && (e.key === "e" || e.key === "E")) {
      e.preventDefault();
      try {
        await saveEdit();
      } catch (err) {
        alert(err.message);
      }
      return;
    }

    return;
  }

  if (e.key === " ") {
    e.preventDefault();
    toggleAutoPlayPause();
    return;
  }

  if (e.key === "t" || e.key === "T") {
    e.preventDefault();
    mode = mode === "grid" ? "slideshow" : "grid";
    updateView();
    return;
  }

  if (e.key === "ArrowRight") {
    e.preventDefault();
    nextImage();
  } else if (e.key === "ArrowLeft") {
    e.preventDefault();
    prevImage();
  } else if (e.key === "d" || e.key === "D") {
    e.preventDefault();
    toggleDescription();
  } else if (e.key === "e" || e.key === "E") {
    e.preventDefault();
    startEdit();
  } else if (e.key === "Escape") {
    if (mode === "slideshow") {
      e.preventDefault();
      mode = "grid";
      updateView();
    }
  }
});

loadAssets().catch((err) => {
  loadingEl.classList.add("hidden");
  errorEl.textContent = err.message;
  errorEl.classList.remove("hidden");
});
