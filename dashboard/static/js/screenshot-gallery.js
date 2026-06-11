(function () {
  function updateGallery(gallery, index) {
    const cards = Array.from(gallery.querySelectorAll("[data-screenshot-card]"));
    const panel = gallery.closest(".screenshot-gallery");
    const counter = panel.querySelector("[data-screenshot-counter]");
    const previous = panel.querySelector("[data-screenshot-prev]");
    const next = panel.querySelector("[data-screenshot-next]");
    const caption = panel.querySelector("[data-screenshot-caption]");

    cards.forEach((card, cardIndex) => {
      card.hidden = cardIndex !== index;
    });
    caption.textContent = cards[index].dataset.screenshotCaptionText || "";
    counter.textContent = `${index + 1} / ${cards.length}`;
    previous.disabled = cards.length <= 1;
    next.disabled = cards.length <= 1;
    gallery.dataset.screenshotIndex = String(index);
    sessionStorage.setItem(galleryKey(gallery), String(index));
  }

  function galleryKey(gallery) {
    return `psynetsk:screenshot-gallery:${window.location.pathname}`;
  }

  function stepGallery(gallery, step) {
    const cards = gallery.querySelectorAll("[data-screenshot-card]");
    if (cards.length === 0) return;
    const current = Number(gallery.dataset.screenshotIndex || 0);
    const next = (current + step + cards.length) % cards.length;
    updateGallery(gallery, next);
  }

  function setupGallery(gallery) {
    const panel = gallery.closest(".screenshot-gallery");
    const previous = panel.querySelector("[data-screenshot-prev]");
    const next = panel.querySelector("[data-screenshot-next]");
    const cards = gallery.querySelectorAll("[data-screenshot-card]");
    const stored = Number(sessionStorage.getItem(galleryKey(gallery)) || 0);
    const initial =
      Number.isInteger(stored) && stored >= 0 && stored < cards.length
        ? stored
        : 0;

    updateGallery(gallery, initial);
    previous.addEventListener("click", () => stepGallery(gallery, -1));
    next.addEventListener("click", () => stepGallery(gallery, 1));
    gallery.addEventListener("keydown", (event) => {
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        stepGallery(gallery, -1);
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        stepGallery(gallery, 1);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-screenshot-gallery]").forEach(setupGallery);
  });
})();
