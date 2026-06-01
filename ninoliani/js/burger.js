// =========================
// BURGER MENU
// =========================

const menuBtn = document.querySelector(".header_list_item_custom");
const sideMenu = document.querySelector(".side_menu");
const overlay = document.querySelector(".menu_overlay");

const closeMenu = () => {
    sideMenu?.classList.remove("active");
    overlay?.classList.remove("active");
};

// Open menu
menuBtn?.addEventListener("click", (e) => {
    e.preventDefault();

    sideMenu?.classList.add("active");
    overlay?.classList.add("active");
});

// Close on overlay click
overlay?.addEventListener("click", closeMenu);

// Close on Escape
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {

        sideMenu?.classList.remove("active");
        overlay?.classList.remove("active");

        // Close filter
        filterDropdown?.classList.remove("active");
        filterBtn?.classList.remove("active");

        // Close sort
        sortDropdown?.classList.remove("active");
        sortToggle?.classList.remove("active");
    }
});


// =========================
// CATALOG MENUS (CLICK ONLY)
// =========================

const catalogMenu = document.querySelector(".catalog_menu");

const collectionsPanel = document.querySelector(".nav_catalog_collections_panel");
const dressesPanel = document.querySelector(".nav_catalog_dresses_panel");

const navLinks = [...document.querySelectorAll(".catalog_nav_list .header_link")];

const collectionsLink = navLinks.find(
    link => link.textContent.trim().toUpperCase() === "COLLECTIONS"
);

const dressesLink = navLinks.find(
    link => link.textContent.trim().toUpperCase() === "DRESSES"
);

if (catalogMenu) {

    const closeAllMenus = () => {
        collectionsPanel?.classList.remove("active");
        dressesPanel?.classList.remove("active");
    };

    // =========================
    // COLLECTIONS
    // =========================

    if (collectionsLink && collectionsPanel) {

        collectionsLink.addEventListener("click", (e) => {
            e.preventDefault();

            const isOpen = collectionsPanel.classList.contains("active");

            closeAllMenus();

            if (!isOpen) {
                collectionsPanel.classList.add("active");
            }
        });
    }

    // =========================
    // DRESSES
    // =========================

    if (dressesLink && dressesPanel) {

        dressesLink.addEventListener("click", (e) => {
            e.preventDefault();

            const isOpen = dressesPanel.classList.contains("active");

            closeAllMenus();

            if (!isOpen) {
                dressesPanel.classList.add("active");
            }
        });
    }

    // =========================
    // CLOSE ON OUTSIDE CLICK
    // =========================

    document.addEventListener("click", (e) => {

        const clickedInside = catalogMenu.contains(e.target);

        if (!clickedInside) {
            closeAllMenus();
        }
    });
}

// =========================
// FILTER
// =========================

const filterBtn = document.querySelector(".filter_toggle");
const filterDropdown = document.querySelector(".filter_dropdown");

filterBtn?.addEventListener("click", (e) => {

    e.stopPropagation();

    filterDropdown.classList.toggle("active");
    filterBtn.classList.toggle("active");

    // Close sort if it is open
    sortDropdown?.classList.remove("active");
    sortToggle?.classList.remove("active");
});

// =========================
// SORT
// =========================

const sortToggle = document.querySelector(".sort_toggle");
const sortDropdown = document.querySelector(".sort_dropdown");
const sortOptions = document.querySelectorAll(".sort_option");

sortToggle?.addEventListener("click", (e) => {

    e.stopPropagation();

    sortDropdown.classList.toggle("active");
    sortToggle.classList.toggle("active");

    // Close filter if it is open
    filterDropdown?.classList.remove("active");
    filterBtn?.classList.remove("active");
});

// =========================
// SORT OPTION SELECT
// =========================

sortOptions.forEach(option => {

    option.addEventListener("click", () => {
        window.location.href = option.dataset.url;
    });

});

// =========================
// CLOSE DROPDOWNS ON OUTSIDE CLICK
// =========================

document.addEventListener("click", (e) => {

    // FILTER
    if (!e.target.closest(".filter_wrapper")) {

        filterDropdown?.classList.remove("active");
        filterBtn?.classList.remove("active");
    }

    // SORT
    if (!e.target.closest(".sort_wrapper")) {

        sortDropdown?.classList.remove("active");
        sortToggle?.classList.remove("active");
    }

});

// =========================
// CATALOG LOAD MORE
// =========================

const loadMoreBtn = document.querySelector(".load_btn");
const catalogCardsWrapper = document.querySelector(".catalog_cards_wrapper");
const currentPageLabel = document.querySelector(".first_page");
const paginationLeft = document.querySelector(".pagination_left");
const paginationRight = document.querySelector(".pagination_right");

const updateCatalogPagination = (data) => {
    if (currentPageLabel) {
        currentPageLabel.textContent = String(data.current_page).padStart(2, "0");
    }

    if (paginationLeft) {
        paginationLeft.href = data.previous_page_url || "#";
        paginationLeft.querySelector("path")?.setAttribute(
            "fill",
            data.has_previous ? "#161616" : "#C0C0C0",
        );
    }

    if (paginationRight) {
        paginationRight.href = data.next_page_url || "#";
        paginationRight.querySelector("path")?.setAttribute(
            "fill",
            data.has_next ? "#161616" : "#C0C0C0",
        );
    }

    if (loadMoreBtn) {
        loadMoreBtn.dataset.nextUrl = data.next_page_url;
        loadMoreBtn.hidden = !data.has_next;
        loadMoreBtn.disabled = !data.has_next;
    }
};

const loadNextCatalogPage = async () => {
    const nextUrl = loadMoreBtn?.dataset.nextUrl;

    if (!nextUrl || !loadMoreBtn || !catalogCardsWrapper) {
        return null;
    }

    loadMoreBtn.disabled = true;

    const response = await fetch(nextUrl, {
        headers: {
            "X-Requested-With": "XMLHttpRequest",
        },
    });

    if (!response.ok) {
        throw new Error(`Load more failed: ${response.status}`);
    }

    const data = await response.json();

    catalogCardsWrapper.insertAdjacentHTML("beforeend", data.html);
    bindCatalogCardScrollLinks(catalogCardsWrapper);
    updateCatalogPagination(data);

    return data;
};

const bindCatalogCardScrollLinks = (container = document) => {
    container.querySelectorAll(".catalog_cards_wrapper .card > a, .card > a").forEach(link => {
        if (link.dataset.scrollRestoreBound) {
            return;
        }

        link.dataset.scrollRestoreBound = "true";
        link.addEventListener("click", () => {
            sessionStorage.setItem("catalogScrollY", String(window.scrollY));
            sessionStorage.setItem("catalogUrl", window.location.href);
            sessionStorage.setItem(
                "catalogLoadedPage",
                currentPageLabel?.textContent || "1",
            );
        });
    });
};

bindCatalogCardScrollLinks();

// =========================
// CATALOG SCROLL RESTORE
// =========================

const clearCatalogRestoreState = () => {
    sessionStorage.removeItem("catalogScrollY");
    sessionStorage.removeItem("catalogUrl");
    sessionStorage.removeItem("catalogLoadedPage");
};

window.addEventListener("pageshow", async () => {
    const savedCatalogUrl = sessionStorage.getItem("catalogUrl");
    const savedCatalogScrollY = sessionStorage.getItem("catalogScrollY");

    if (savedCatalogUrl && savedCatalogUrl !== window.location.href) {
        clearCatalogRestoreState();
        return;
    }

    if (savedCatalogScrollY === null) {
        return;
    }

    const savedLoadedPage = Number(
        sessionStorage.getItem("catalogLoadedPage") || "1",
    );
    let renderedPage = Number(currentPageLabel?.textContent || "1");

    try {
        while (renderedPage < savedLoadedPage && loadMoreBtn?.dataset.nextUrl) {
            const data = await loadNextCatalogPage();

            if (!data) {
                break;
            }

            renderedPage = data.current_page;
        }
    } catch (error) {
        console.error(error);
    }

    requestAnimationFrame(() => {
        window.scrollTo(0, Number(savedCatalogScrollY));
        clearCatalogRestoreState();
    });
});

loadMoreBtn?.addEventListener("click", async (e) => {
    e.preventDefault();

    if (loadMoreBtn.disabled) {
        return;
    }

    try {
        await loadNextCatalogPage();
    } catch (error) {
        loadMoreBtn.disabled = false;
        console.error(error);
    }
});
