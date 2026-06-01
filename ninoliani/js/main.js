// =========================
// PORTFOLIO GALLERY
// =========================

const gallery = document.querySelector(".portfolio_gallery");
const leftBtn = document.querySelector(".arrow_left");
const rightBtn = document.querySelector(".arrow_right");

// =========================
// INFINITE SCROLLING TRACK
// =========================

let position = 0;
let speed = 0;
const reducedMotionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");

// Clone items for infinite scrolling
const originals = Array.from(gallery.children);
originals.forEach(el => {
  gallery.appendChild(el.cloneNode(true));
});

function halfWidth() {
  return gallery.scrollWidth / 2;
}

function renderTrackPosition() {
  const half = halfWidth();

  if (position <= -half) position += half;
  if (position > 0) position -= half;

  gallery.style.transform = `translateX(${position}px)`;
}

function animate() {
  if (speed !== 0) {
    position += speed;
    renderTrackPosition();
  }
  requestAnimationFrame(animate);
}

if (!reducedMotionQuery.matches) animate();

// =========================
// ARROW CONTROLS
// =========================

function start(dir) {
  speed = dir;
}

function stop() {
  speed = 0;
}

leftBtn.addEventListener("mousedown", () => start(6));
rightBtn.addEventListener("mousedown", () => start(-6));
document.addEventListener("mouseup", stop);

leftBtn.addEventListener("touchstart", () => start(6));
rightBtn.addEventListener("touchstart", () => start(-6));
document.addEventListener("touchend", stop);

// =========================
// TRACK SWIPE
// =========================

let startX = 0;
let isDragging = false;

gallery.addEventListener("touchstart", (e) => {
  startX = e.touches[0].clientX;
  isDragging = true;
  speed = 0;
});

gallery.addEventListener("touchmove", (e) => {
  if (!isDragging) return;

  const x = e.touches[0].clientX;
  const diff = x - startX;

  position += diff * 0.8;
  startX = x;
  if (!reducedMotionQuery.matches) renderTrackPosition();
});

gallery.addEventListener("touchend", () => {
  isDragging = false;
});

// =========================
// LIGHTBOX
// =========================

const images = originals;
let currentIndex = 0;

const lightbox = document.createElement("div");
lightbox.classList.add("lightbox");

lightbox.innerHTML = `
  <span class="lb_prev">‹</span>
  <img src="">
  <span class="lb_next">›</span>
`;

document.body.appendChild(lightbox);

const lightboxImg = lightbox.querySelector("img");
const prevBtn = lightbox.querySelector(".lb_prev");
const nextBtn = lightbox.querySelector(".lb_next");

function openLightbox(index) {
  currentIndex = index;
  lightboxImg.src = images[currentIndex].src;
  lightbox.style.display = "flex";
}

function closeLightbox() {
  lightbox.style.display = "none";
}

function nextImage() {
  currentIndex = (currentIndex + 1) % images.length;
  lightboxImg.src = images[currentIndex].src;
}

function prevImage() {
  currentIndex = (currentIndex - 1 + images.length) % images.length;
  lightboxImg.src = images[currentIndex].src;
}

gallery.addEventListener("click", (e) => {
  const img = e.target.closest(".portfolio_img");
  if (!img) return;

  const sourceIndex = images.findIndex(item => item.dataset.i === img.dataset.i);
  openLightbox(sourceIndex === -1 ? 0 : sourceIndex);
});

nextBtn.addEventListener("click", nextImage);
prevBtn.addEventListener("click", prevImage);

lightbox.addEventListener("click", (e) => {
  if (e.target === lightbox) closeLightbox();
});

document.addEventListener("keydown", (e) => {
  if (lightbox.style.display !== "flex") return;

  if (e.key === "ArrowRight") nextImage();
  if (e.key === "ArrowLeft") prevImage();
  if (e.key === "Escape") closeLightbox();
});

// =========================
// LIGHTBOX SWIPE
// =========================

let lbStartX = 0;

lightbox.addEventListener("touchstart", (e) => {
  lbStartX = e.touches[0].clientX;
});

lightbox.addEventListener("touchend", (e) => {
  const endX = e.changedTouches[0].clientX;
  const diff = endX - lbStartX;

  if (Math.abs(diff) > 50) {
    if (diff < 0) nextImage();
    else prevImage();
  }
});

// =========================
// FORM VALIDATION
// =========================

document.addEventListener("DOMContentLoaded", () => {

  const inputs = document.querySelectorAll(".connections_form_input");

  const validators = {
    text: (v) => v.trim().length >= 2,
    tel: (v) => v.trim().length >= 6,
    email: (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)
  };

  function validateInput(input) {
    const container = input.closest(".input_container");
    if (!container) return;

    let isValid = false;

    if (input.type === "email") {
      isValid = validators.email(input.value);
    } else if (input.type === "tel") {
      isValid = validators.tel(input.value);
    } else {
      isValid = validators.text(input.value);
    }

    input.classList.remove("error", "valid");
    container.classList.remove("success");

    if (input.value.trim() === "") return;

    if (isValid) {
      input.classList.add("valid");
      container.classList.add("success");
    } else {
      input.classList.add("error");
    }
  }

  inputs.forEach(input => {
    input.addEventListener("input", () => validateInput(input));
    input.addEventListener("blur", () => validateInput(input));
  });

});

// =========================
// MODAL
// =========================

const modal = document.getElementById("successModal");
const modalClose = document.querySelector(".modal_close");

function openModal() {
  if (!modal) return;
  modal.classList.add("active");
}

function closeModal() {
  if (!modal) return;
  modal.classList.remove("active");
}

modalClose?.addEventListener("click", closeModal);

modal?.addEventListener("click", (e) => {
  if (e.target === modal) closeModal();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeModal();
});

// =========================
// FORM SUBMIT
// =========================

const form = document.querySelector(".connections_form");

form?.addEventListener("submit", async (e) => {
  e.preventDefault();

  const checkbox = document.getElementById("checkbox");

  if (!checkbox.checked) {
    alert("Accept terms");
    return;
  }

  const formData = new FormData(form);

  try {
    const res = await fetch("send.php", {
      method: "POST",
      body: formData
    });

    const data = await res.json();

    if (data.status === "success") {
      openModal(); // Show success modal
      form.reset();
    } else {
      alert("Error ❌: " + (data.message || "unknown error"));
      console.log("SERVER ERROR:", data);
    }

  } catch (err) {
    alert("Network error ❌");
    console.log("FETCH ERROR:", err);
  }
});

const menuBtn = document.querySelector(".header_list_item_custom");
const sideMenu = document.querySelector(".side_menu");
const overlay = document.querySelector(".menu_overlay");

function closeMenu() {
  sideMenu?.classList.remove("active");
  overlay?.classList.remove("active");
}

// Open menu
menuBtn?.addEventListener("click", (e) => {
  e.preventDefault();
  sideMenu?.classList.add("active");
  overlay?.classList.add("active");
});

// Close menu on overlay click
overlay?.addEventListener("click", closeMenu);

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeMenu();
});

sideMenu?.querySelectorAll("a").forEach(link => {
  link.addEventListener("click", closeMenu);
});

// =========================
// SCROLL REVEAL
// =========================

const reduceMotion = reducedMotionQuery.matches;
const revealGroups = [
  [".hero_main_top", "image", 0],
  [".hero_main_bottom", "image", 80],
  [".about_title", "text", 0],
  [".about_content_left", "image", 80],
  [".about_content_right", "", 160],
  [".portfolio_title", "text", 0],
  [".portfolio_viewport", "image", 80],
  [".portfolio_gallery_btn_wrapper", "", 140],
  [".collections_left_wrapper", "", 0],
  [".collections_right_wrapper", "image", 100],
  [".connections_content", "", 0],
  [".footer_main_wrapper", "", 0]
];

const revealItems = revealGroups.flatMap(([selector, variant, delay]) =>
  Array.from(document.querySelectorAll(selector), element => {
    element.classList.add("motion-reveal");
    if (variant) element.classList.add(`motion-reveal--${variant}`);
    element.style.setProperty("--reveal-delay", `${delay}ms`);
    return element;
  })
);

if (reduceMotion || !("IntersectionObserver" in window)) {
  revealItems.forEach(element => element.classList.add("is-visible"));
} else {
  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      observer.unobserve(entry.target);
    });
  }, {
    threshold: 0.14,
    rootMargin: "0px 0px -8% 0px"
  });

  revealItems.forEach(element => revealObserver.observe(element));
}
