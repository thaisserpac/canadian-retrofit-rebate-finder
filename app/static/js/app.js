// ── State ────────────────────────────────────────────────
let allRetrofitTypes = [];
let currentResults = [];

// ── DOM References ──────────────────────────────────────
const provinceSelect = document.getElementById("province-select");
const retrofitTypesEl = document.getElementById("retrofit-types");
const activeOnlyCb = document.getElementById("active-only");
const incomeQualifiedCb = document.getElementById("income-qualified");
const searchBtn = document.getElementById("search-btn");

const summaryBar = document.getElementById("summary-bar");
const summaryCount = document.getElementById("summary-count");
const summarySavings = document.getElementById("summary-savings");
const summaryFinancing = document.getElementById("summary-financing");

const resultsSection = document.getElementById("results-section");
const rebateList = document.getElementById("rebate-list");
const rebatesHeading = document.getElementById("rebates-heading");

const financingSection = document.getElementById("financing-section");
const financingList = document.getElementById("financing-list");

const emptyState = document.getElementById("empty-state");
const welcomeState = document.getElementById("welcome-state");
const loadingState = document.getElementById("loading-state");

// ── Initialization ──────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
    await Promise.all([loadProvinces(), loadRetrofitTypes()]);
});

searchBtn.addEventListener("click", doSearch);

provinceSelect.addEventListener("change", () => {
    if (provinceSelect.value) {
        doSearch();
    }
});

// ── Load Provinces ──────────────────────────────────────
async function loadProvinces() {
    try {
        const res = await fetch("/api/rebates/provinces");
        const data = await res.json();
        data.provinces.forEach((p) => {
            const opt = document.createElement("option");
            opt.value = p.code;
            opt.textContent = `${p.name} (${p.program_count})`;
            provinceSelect.appendChild(opt);
        });
    } catch (err) {
        console.error("Failed to load provinces:", err);
    }
}

// ── Load Retrofit Types ─────────────────────────────────
async function loadRetrofitTypes() {
    try {
        const res = await fetch("/api/rebates/retrofit-types");
        const data = await res.json();
        allRetrofitTypes = data.types;
        renderRetrofitCheckboxes(data.types);
    } catch (err) {
        console.error("Failed to load retrofit types:", err);
    }
}

function renderRetrofitCheckboxes(types) {
    // Group by category
    const grouped = {};
    types.forEach((t) => {
        if (!grouped[t.category]) grouped[t.category] = [];
        grouped[t.category].push(t);
    });

    retrofitTypesEl.innerHTML = "";
    Object.values(grouped)
        .flat()
        .forEach((t) => {
            const label = document.createElement("label");
            label.className = "checkbox-label";
            label.innerHTML =
                `<input type="checkbox" value="${escapeAttr(t.name)}" data-type="retrofit">` +
                `<span>${escapeHtml(t.display_name)}</span>`;
            retrofitTypesEl.appendChild(label);
        });
}

// ── Search ──────────────────────────────────────────────
async function doSearch() {
    const province = provinceSelect.value;
    const activeOnly = activeOnlyCb.checked;
    const incomeOnly = incomeQualifiedCb.checked;

    // Get selected retrofit types
    const selectedTypes = [];
    retrofitTypesEl.querySelectorAll('input[data-type="retrofit"]:checked').forEach((cb) => {
        selectedTypes.push(cb.value);
    });

    showLoading();

    try {
        // Build query params
        const params = new URLSearchParams();
        if (province) params.set("province", province);
        params.set("active_only", activeOnly);

        let rebates;

        if (province && selectedTypes.length === 1) {
            // Use search endpoint for single retrofit type filter
            params.set("retrofit_type", selectedTypes[0]);
            const res = await fetch(`/api/rebates/search?${params}`);
            const data = await res.json();
            rebates = data.rebates;
        } else {
            // Use list endpoint
            const res = await fetch(`/api/rebates?${params}`);
            const data = await res.json();
            rebates = data.rebates;
        }

        // Client-side filtering for multiple retrofit types
        if (selectedTypes.length > 1) {
            rebates = rebates.filter((r) =>
                r.retrofit_types.some((rt) => selectedTypes.includes(rt.name))
            );
        }

        // Client-side income filter
        if (incomeOnly) {
            rebates = rebates.filter((r) => r.is_income_tested);
        }

        currentResults = rebates;
        renderResults(rebates);
    } catch (err) {
        console.error("Search failed:", err);
        hideAll();
        rebateList.innerHTML = '<div class="error-msg">Failed to load results. Is the server running?</div>';
        resultsSection.style.display = "";
    }
}

// ── Render Results ──────────────────────────────────────
function renderResults(rebates) {
    hideAll();

    if (rebates.length === 0) {
        emptyState.style.display = "";
        return;
    }

    // Separate financing from rebates
    const financingKeywords = ["loan", "financing", "interest", "lending", "credit"];
    const financingPrograms = [];
    const rebatePrograms = [];

    rebates.forEach((r) => {
        const desc = (r.amount_description || "").toLowerCase() + " " + (r.description || "").toLowerCase();
        const isFinancing = financingKeywords.some((kw) => desc.includes(kw));
        if (isFinancing) {
            financingPrograms.push(r);
        } else {
            rebatePrograms.push(r);
        }
    });

    // Update summary
    const totalSavings = rebates.reduce((sum, r) => sum + (r.max_amount || 0), 0);
    summaryCount.textContent = rebates.length;
    summarySavings.textContent = totalSavings > 0 ? `$${totalSavings.toLocaleString()}` : "Varies";
    summaryFinancing.textContent = financingPrograms.length;
    summaryBar.style.display = "";

    // Render rebate cards
    if (rebatePrograms.length > 0) {
        rebatesHeading.textContent = `Rebate Programs (${rebatePrograms.length})`;
        rebateList.innerHTML = "";
        rebatePrograms.forEach((r) => rebateList.appendChild(createRebateCard(r)));
        resultsSection.style.display = "";
    }

    // Render financing cards
    if (financingPrograms.length > 0) {
        financingList.innerHTML = "";
        financingPrograms.forEach((r) => financingList.appendChild(createRebateCard(r)));
        financingSection.style.display = "";
    }
}

// ── Create Rebate Card ──────────────────────────────────
function createRebateCard(rebate) {
    const card = document.createElement("div");
    card.className = "rebate-card";

    // Determine status
    const status = getStatus(rebate);

    // Header
    const header = document.createElement("div");
    header.className = "rebate-card-header";

    const titleArea = document.createElement("div");
    titleArea.className = "rebate-card-title-area";

    // Top row: badges
    const topRow = document.createElement("div");
    topRow.className = "rebate-card-top-row";

    const statusBadge = document.createElement("span");
    statusBadge.className = `status-badge ${status.class}`;
    statusBadge.textContent = status.label;
    topRow.appendChild(statusBadge);

    if (rebate.is_income_tested) {
        const incomeBadge = document.createElement("span");
        incomeBadge.className = "status-badge income-tested";
        incomeBadge.textContent = "Income Qualified";
        topRow.appendChild(incomeBadge);
    }

    titleArea.appendChild(topRow);

    // Name
    const name = document.createElement("div");
    name.className = "rebate-card-name";
    name.textContent = rebate.name;
    titleArea.appendChild(name);

    // Meta
    const meta = document.createElement("div");
    meta.className = "rebate-card-meta";

    const provName = rebate.province === "Federal" ? "Federal" : rebate.province;
    meta.innerHTML = `${escapeHtml(provName)} <span class="meta-separator">|</span> ${escapeHtml(rebate.provider)}`;

    if (rebate.end_date) {
        const endDate = new Date(rebate.end_date);
        meta.innerHTML += ` <span class="meta-separator">|</span> Ends: ${formatDate(endDate)}`;
    }

    titleArea.appendChild(meta);
    header.appendChild(titleArea);

    // Amount
    const amountEl = document.createElement("div");
    amountEl.className = "rebate-card-amount";

    if (rebate.max_amount) {
        amountEl.innerHTML =
            `<div class="amount-value">$${rebate.max_amount.toLocaleString()}</div>` +
            `<div class="amount-label">Up to</div>`;
    } else {
        amountEl.innerHTML =
            `<div class="amount-value">Varies</div>` +
            `<div class="amount-label">${escapeHtml(rebate.amount_description || "")}</div>`;
    }

    header.appendChild(amountEl);
    card.appendChild(header);

    // Retrofit type tags
    if (rebate.retrofit_types && rebate.retrofit_types.length > 0) {
        const tags = document.createElement("div");
        tags.className = "rebate-card-tags";
        rebate.retrofit_types.forEach((rt) => {
            const tag = document.createElement("span");
            tag.className = "retrofit-tag";
            tag.textContent = rt.display_name;
            tags.appendChild(tag);
        });
        card.appendChild(tags);
    }

    // Description
    if (rebate.description) {
        const body = document.createElement("div");
        body.className = "rebate-card-body";
        const desc = document.createElement("div");
        desc.className = "rebate-card-description";
        desc.textContent = rebate.description;
        body.appendChild(desc);
        card.appendChild(body);
    }

    // Collapsible details
    const details = document.createElement("div");
    details.className = "rebate-card-details";

    if (rebate.eligibility_summary) {
        details.appendChild(createDetailSection("Eligibility", rebate.eligibility_summary));
    }
    if (rebate.how_to_apply) {
        details.appendChild(createDetailSection("How to Apply", rebate.how_to_apply));
    }
    if (rebate.amount_description) {
        details.appendChild(createDetailSection("Amount Details", rebate.amount_description));
    }

    card.appendChild(details);

    // Actions bar
    const actions = document.createElement("div");
    actions.className = "rebate-card-actions";

    const hasDetails = rebate.eligibility_summary || rebate.how_to_apply || rebate.amount_description;

    if (hasDetails) {
        const toggleBtn = document.createElement("button");
        toggleBtn.className = "card-toggle-btn";
        toggleBtn.innerHTML =
            'More Details ' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">' +
            '<polyline points="6 9 12 15 18 9"></polyline>' +
            '</svg>';

        toggleBtn.addEventListener("click", () => {
            const isOpen = details.classList.toggle("open");
            toggleBtn.classList.toggle("open", isOpen);
            toggleBtn.innerHTML = (isOpen ? "Less Details " : "More Details ") +
                '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">' +
                '<polyline points="6 9 12 15 18 9"></polyline>' +
                '</svg>';
        });

        actions.appendChild(toggleBtn);
    } else {
        actions.appendChild(document.createElement("span"));
    }

    if (rebate.website_url) {
        const link = document.createElement("a");
        link.className = "card-website-btn";
        link.href = rebate.website_url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.innerHTML =
            'Visit Website ' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12">' +
            '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>' +
            '<polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line>' +
            '</svg>';
        actions.appendChild(link);
    }

    card.appendChild(actions);

    return card;
}

function createDetailSection(title, content) {
    const section = document.createElement("div");
    section.className = "detail-section";

    const titleEl = document.createElement("div");
    titleEl.className = "detail-section-title";
    titleEl.textContent = title;

    const contentEl = document.createElement("div");
    contentEl.className = "detail-section-content";
    contentEl.textContent = content;

    section.appendChild(titleEl);
    section.appendChild(contentEl);
    return section;
}

// ── Status Helpers ──────────────────────────────────────
function getStatus(rebate) {
    if (!rebate.is_active) {
        return { label: "Closed", class: "closed" };
    }

    if (rebate.end_date) {
        const endDate = new Date(rebate.end_date);
        const now = new Date();
        const sixMonths = new Date();
        sixMonths.setMonth(sixMonths.getMonth() + 6);

        if (endDate < now) {
            return { label: "Closed", class: "closed" };
        }
        if (endDate < sixMonths) {
            return { label: "Closing Soon", class: "closing-soon" };
        }
    }

    return { label: "Active", class: "active" };
}

function formatDate(date) {
    return date.toLocaleDateString("en-CA", { year: "numeric", month: "short", day: "numeric" });
}

// ── UI State Helpers ────────────────────────────────────
function showLoading() {
    welcomeState.style.display = "none";
    emptyState.style.display = "none";
    resultsSection.style.display = "none";
    financingSection.style.display = "none";
    summaryBar.style.display = "none";
    loadingState.style.display = "";
}

function hideAll() {
    loadingState.style.display = "none";
    welcomeState.style.display = "none";
    emptyState.style.display = "none";
    resultsSection.style.display = "none";
    financingSection.style.display = "none";
    summaryBar.style.display = "none";
}

// ── Escape Helpers ──────────────────────────────────────
function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function escapeAttr(text) {
    return text.replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}
