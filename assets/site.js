const petGrid = document.querySelector("#pet-grid");
const behaviorRail = document.querySelector("#behavior-rail");
const eventMap = document.querySelector("#event-map");

async function loadJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load ${path}`);
  }
  return response.json();
}

function renderPetCard(entry, pet) {
  const card = document.createElement("article");
  card.className = "pet-card";
  const tags = (entry.tags || pet.tags || []).slice(0, 5);
  card.innerHTML = `
    <img src="${entry.preview}" alt="${entry.displayName} animation preview">
    <div>
      <h3>${entry.displayName}</h3>
      <p>${entry.description}</p>
      <div class="tags">${tags.map((tag) => `<span>${tag}</span>`).join("")}</div>
    </div>
  `;
  petGrid.appendChild(card);
}

function formatTrigger(trigger) {
  if (!trigger) return "runtime";
  const metric = trigger.metric.replace(/([A-Z])/g, " $1").toLowerCase();
  const value = trigger.metric.includes("Fraction") ? `${Math.round(trigger.value * 100)}%` : `${trigger.value}m`;
  return `${metric} ${trigger.operator} ${value}`;
}

function renderBehavior(pet) {
  const rules = pet.behavior?.rules || [];
  behaviorRail.innerHTML = rules.map((rule) => `
    <article class="behavior-rule">
      <div class="trigger">${formatTrigger(rule.trigger)}</div>
      <div>
        <h3>${rule.label}</h3>
        <p>${rule.message}</p>
      </div>
      <div class="mode ${rule.mode}">${rule.mode}</div>
    </article>
  `).join("");
}

function renderEvents(pet) {
  const entries = Object.entries(pet.events || {});
  eventMap.innerHTML = entries.map(([name, event]) => `
    <article class="event-row">
      <div class="event-name">${name}</div>
      <div class="event-animation">${event.animation}</div>
      <div class="tone ${event.tone}">${event.tone}</div>
    </article>
  `).join("");
}

async function boot() {
  try {
    const manifest = await loadJson("manifest.json");
    const pets = await Promise.all(manifest.pets.map(async (entry) => {
      const pet = await loadJson(entry.manifest);
      return { entry, pet };
    }));
    pets.forEach(({ entry, pet }) => renderPetCard(entry, pet));
    const xiaochai = pets.find(({ pet }) => pet.id === "xiaochai") || pets[0];
    if (xiaochai) {
      renderBehavior(xiaochai.pet);
      renderEvents(xiaochai.pet);
    }
  } catch (error) {
    petGrid.innerHTML = `<p>${error.message}</p>`;
    behaviorRail.innerHTML = `<p>${error.message}</p>`;
    eventMap.innerHTML = `<p>${error.message}</p>`;
  }
}

document.querySelectorAll("[data-copy]").forEach((button) => {
  button.addEventListener("click", async () => {
    const text = button.getAttribute("data-copy");
    await navigator.clipboard.writeText(text);
    const original = button.textContent;
    button.textContent = "Copied";
    window.setTimeout(() => {
      button.textContent = original;
    }, 1200);
  });
});

boot();
