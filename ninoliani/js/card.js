// =========================
// BURGER MENU
// =========================

const menuBtn = document.querySelector(".header_list_item_custom");
const sideMenu = document.querySelector(".side_menu");
const overlay = document.querySelector(".menu_overlay");

if (menuBtn && sideMenu && overlay) {
    menuBtn.addEventListener("click", (e) => {
        e.preventDefault();
        sideMenu.classList.add("active");
        overlay.classList.add("active");
    });

    overlay.addEventListener("click", () => {
        sideMenu.classList.remove("active");
        overlay.classList.remove("active");
    });
}


// =========================
// GALLERY
// =========================

const imgs = document.querySelectorAll(".main_card_img");

const modal = document.querySelector(".gallery_modal");
const backdrop = document.querySelector(".gallery_backdrop");
const img = document.querySelector(".gallery_img");

const nextBtn = document.querySelector(".gallery_next");
const prevBtn = document.querySelector(".gallery_prev");
const closeBtn = document.querySelector(".gallery_close");

let index = 0;
const hasGallery = imgs.length && modal && backdrop && img && nextBtn && prevBtn && closeBtn;

/* =========================
   STATE
========================= */

let state = {
    scale: 1,
    targetScale: 1,
    x: 0,
    y: 0,
    tx: 0,
    ty: 0,
    dragging: false,
    vx: 0,
    vy: 0,
    lastX: 0,
    lastY: 0
};

/* =========================
   OPEN / CLOSE
========================= */

function open(i) {
    if (!hasGallery) return;
    index = i;
    modal.classList.add("active");
    document.body.style.overflow = "hidden";
    load();
    reset();
}

function close() {
    if (!hasGallery) return;
    modal.classList.remove("active");
    document.body.style.overflow = "";
    reset();
}

function reset() {
    state.scale = state.targetScale = 1;
    state.x = state.y = state.tx = state.ty = 0;
    apply();
}

/* =========================
   IMAGE LOAD + PRELOAD
========================= */

function load() {
    const source = imgs[index].src;

    const preload = new Image();
    preload.src = source;

    preload.onload = () => {
        img.src = source;
        img.style.opacity = 1;
    };

    preloadNext();
    preloadPrev();
}

function preloadNext() {
    const next = (index + 1) % imgs.length;
    new Image().src = imgs[next].src;
}

function preloadPrev() {
    const prev = (index - 1 + imgs.length) % imgs.length;
    new Image().src = imgs[prev].src;
}

/* =========================
   NAV
========================= */

function next() {
    index = (index + 1) % imgs.length;
    load();
    reset();
}

function prev() {
    index = (index - 1 + imgs.length) % imgs.length;
    load();
    reset();
}

/* =========================
   APPLY TRANSFORM
========================= */

function apply() {
    if (!img) return;
    img.style.transform =
        `translate(${state.x}px, ${state.y}px) scale(${state.scale})`;
}

/* =========================
   ANIMATION LOOP (smooth physics)
========================= */

function loop() {
    state.scale += (state.targetScale - state.scale) * 0.14;

    state.x += (state.tx - state.x) * 0.14;
    state.y += (state.ty - state.y) * 0.14;

    apply();
    requestAnimationFrame(loop);
}
loop();

/* =========================
   OPEN EVENTS
========================= */

imgs.forEach((el, i) => {
    el.addEventListener("click", () => open(i));
});

closeBtn?.addEventListener("click", close);
backdrop?.addEventListener("click", close);
nextBtn?.addEventListener("click", next);
prevBtn?.addEventListener("click", prev);

/* =========================
   CLICK ZOOM (CENTER SMART)
========================= */

img?.addEventListener("click", (e) => {
    if (state.targetScale === 1) {
        const rect = img.getBoundingClientRect();

        const dx = e.clientX - rect.left - rect.width / 2;
        const dy = e.clientY - rect.top - rect.height / 2;

        state.targetScale = 2.4;
        state.tx = -dx;
        state.ty = -dy;
    } else {
        state.targetScale = 1;
        state.tx = 0;
        state.ty = 0;
    }
});

/* =========================
   WHEEL ZOOM (cursor focus)
========================= */

img?.addEventListener("wheel", (e) => {
    e.preventDefault();

    const zoom = -e.deltaY * 0.002;
    state.targetScale = Math.min(4, Math.max(1, state.targetScale + zoom));
}, { passive: false });

/* =========================
   DRAG (with inertia)
========================= */

img?.addEventListener("mousedown", (e) => {
    if (state.targetScale <= 1) return;

    state.dragging = true;
    state.lastX = e.clientX;
    state.lastY = e.clientY;
});

window.addEventListener("mousemove", (e) => {
    if (!state.dragging) return;

    const dx = e.clientX - state.lastX;
    const dy = e.clientY - state.lastY;

    state.tx += dx;
    state.ty += dy;

    state.vx = dx;
    state.vy = dy;

    state.lastX = e.clientX;
    state.lastY = e.clientY;
});

window.addEventListener("mouseup", () => {
    state.dragging = false;

    // inertia (momentum)
    state.tx += state.vx * 12;
    state.ty += state.vy * 12;
});

/* =========================
   TOUCH (pinch + swipe ready)
========================= */

let touchDist = null;

img?.addEventListener("touchstart", (e) => {
    if (e.touches.length === 2) {
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        touchDist = Math.hypot(dx, dy);
    }
});

img?.addEventListener("touchmove", (e) => {
    if (e.touches.length === 2 && touchDist) {
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;

        const newDist = Math.hypot(dx, dy);
        const delta = (newDist - touchDist) * 0.01;

        state.targetScale = Math.min(4, Math.max(1, state.targetScale + delta));

        touchDist = newDist;
    }
});

/* =========================
   KEYBOARD
========================= */

document.addEventListener("keydown", (e) => {
    if (!modal.classList.contains("active")) return;

    if (e.key === "Escape") close();
    if (e.key === "ArrowRight") next();
    if (e.key === "ArrowLeft") prev();
});

// =========================
// ACCORDION
// =========================

document.querySelectorAll(".main_card_description_wrapper").forEach((wrapper) => {
    const btn = wrapper.querySelector(".main_card_descr_btn");

    if (!btn) return;

    btn.addEventListener("click", () => {
        wrapper.classList.toggle("active");
    });
});


// =========================
// SIZE GUIDE TABLE SWITCH
// =========================

document.querySelectorAll(".main_card_description_wrapper").forEach((wrapper) => {
    const inchesBtn = wrapper.querySelectorAll(".table_btn")[0];
    const cmBtn = wrapper.querySelectorAll(".table_btn")[1];

    const inchesTable = wrapper.querySelector(".inches");
    const cmTable = wrapper.querySelector(".sm");

    if (!inchesBtn || !cmBtn || !inchesTable || !cmTable) return;

    function setMode(isInches) {
        if (isInches) {
            inchesTable.classList.add("active");
            cmTable.classList.remove("active");

            inchesBtn.classList.add("active");
            cmBtn.classList.remove("active");
        } else {
            cmTable.classList.add("active");
            inchesTable.classList.remove("active");

            cmBtn.classList.add("active");
            inchesBtn.classList.remove("active");
        }
    }

    inchesBtn.addEventListener("click", () => setMode(true));
    cmBtn.addEventListener("click", () => setMode(false));

    // Set default mode
    setMode(false);
});

const wrapper = document.querySelector(".main_card_gallery");
const images = imgs;

const lens = document.querySelector(".zoom_lens");
const lensImg = document.querySelector(".zoom_lens_img");

let activeImg = null;

/* Cursor state */
let mouse = { x: 0, y: 0 };
let smooth = { x: 0, y: 0 };

/* Image position inside lens */
let bgX = 50;
let bgY = 50;
let smoothBgX = 50;
let smoothBgY = 50;

const LENS_SIZE = 300;
const ZOOM = 4;

/* ========================= */
/* IMAGE ENTER
/* ========================= */

if (wrapper && lens && lensImg) {
images.forEach(img => {
    img.addEventListener("mouseenter", () => {
        activeImg = img;

        lens.classList.add("active");

        lensImg.style.backgroundImage = `url(${img.src})`;
        lensImg.style.backgroundSize = `${ZOOM * 100}%`;
    });

    img.addEventListener("mouseleave", () => {
        activeImg = null;
        lens.classList.remove("active");
    });
});
}

/* ========================= */
/* MOVE TRACKING
/* ========================= */

wrapper?.addEventListener("mousemove", (e) => {
    if (!activeImg) return;

    const rect = activeImg.getBoundingClientRect();

    /* Position inside image (0..1) */
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;

    /* Clamp values */
    const cx = Math.max(0, Math.min(1, x));
    const cy = Math.max(0, Math.min(1, y));

    /* Convert to zoom background coordinates */
    bgX = cx * 100;
    bgY = cy * 100;

    mouse.x = e.clientX;
    mouse.y = e.clientY;
});

/* ========================= */
/* ANIMATION LOOP
/* ========================= */

function animate() {

    /* Smooth cursor follow */
    smooth.x += (mouse.x - smooth.x) * 0.18;
    smooth.y += (mouse.y - smooth.y) * 0.18;

    /* Smooth zoom movement */
    smoothBgX += (bgX - smoothBgX) * 0.22;
    smoothBgY += (bgY - smoothBgY) * 0.22;

    if (activeImg) {

        /* Lens follows cursor position */
        lens.style.left = (smooth.x - LENS_SIZE / 2) + "px";
        lens.style.top = (smooth.y - LENS_SIZE / 2) + "px";

        /* Use percentage-based background positioning for precise movement */
        lensImg.style.backgroundPosition =
            `${smoothBgX}% ${smoothBgY}%`;
    }

    requestAnimationFrame(animate);
}

animate();
