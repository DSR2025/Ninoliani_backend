document.addEventListener("DOMContentLoaded", () => {
  const banner = document.querySelector("[data-cookie-banner]");
  if (!banner) return;

  let consent = null;

  try {
    consent = localStorage.getItem("cookieConsent");
  } catch {
    banner.hidden = false;
  }

  if (consent === null) {
    banner.hidden = false;
  }

  banner.querySelectorAll("[data-cookie-consent]").forEach(button => {
    button.addEventListener("click", () => {
      try {
        localStorage.setItem("cookieConsent", button.dataset.cookieConsent);
      } catch {
        // The banner still closes for this page if storage is unavailable.
      }

      banner.hidden = true;
    });
  });
});
