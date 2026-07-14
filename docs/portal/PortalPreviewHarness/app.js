const sampleFeed = {
  title: "Biblion Portal Feed",
  panels: {
    main: {
      html: "<h1>Portal Landing Feed</h1><p>This primary panel is intended for the launcher landing page.</p>",
    },
    secondary: {
      html: "<h3>Project Status</h3><ul><li>OCR queue healthy</li><li>Trainer idle</li></ul>",
    },
    tertiary: {
      html: "<h3>Recent Activity</h3><p>Use this card for announcements, tasks, or community notices.</p>",
    },
  },
};

function setStatus(message, isError = false) {
  const statusLine = document.getElementById("status-line");
  statusLine.textContent = message;
  statusLine.style.color = isError ? "#8a1f11" : "";
}

function normalizeFeedPayload(payload) {
  if (payload && payload.panels && typeof payload.panels === "object") {
    return payload;
  }

  if (payload && typeof payload.html === "string") {
    return {
      title: payload.title || "Portal Feed",
      panels: {
        main: { html: payload.html },
      },
    };
  }

  throw new Error("Unsupported feed payload shape.");
}

function renderPanels(payload) {
  const normalized = normalizeFeedPayload(payload);
  const panels = normalized.panels || {};
  const panelMap = {
    main: document.getElementById("panel-main"),
    secondary: document.getElementById("panel-secondary"),
    tertiary: document.getElementById("panel-tertiary"),
  };

  Object.entries(panelMap).forEach(([key, element]) => {
    const html = panels[key] && typeof panels[key].html === "string"
      ? panels[key].html
      : `<p><em>No ${key} panel content.</em></p>`;
    element.innerHTML = html;
  });

  document.title = normalized.title || "Biblion Portal Preview Harness";
  document.getElementById("payload-output").textContent = JSON.stringify(normalized, null, 2);
}

async function loadFeedFromEndpoint() {
  const endpoint = document.getElementById("feed-endpoint").value.trim();
  if (!endpoint) {
    setStatus("Enter a Django feed endpoint before loading.", true);
    return;
  }

  setStatus(`Loading ${endpoint} ...`);

  try {
    const response = await fetch(endpoint, {
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const payload = await response.json();
    renderPanels(payload);
    setStatus(`Loaded portal feed from ${endpoint}.`);
  } catch (error) {
    setStatus(`Failed to load feed: ${error.message}`, true);
  }
}

function loadSampleFeed() {
  renderPanels(sampleFeed);
  setStatus("Loaded bundled sample feed.");
}

document.getElementById("load-feed").addEventListener("click", loadFeedFromEndpoint);
document.getElementById("load-sample").addEventListener("click", loadSampleFeed);

loadSampleFeed();