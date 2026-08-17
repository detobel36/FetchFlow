document.addEventListener("DOMContentLoaded", function () {
  let editor = null;
  let activeLineMarker = null;

  const defaultSampleConfig = {
    name: "e_commerce_catalog",
    version: "1.0",
    variables: {
      base_url: "https://store.example.com"
    },
    steps: [
      {
        id: "products",
        request: {
          method: "GET",
          url: "{{base_url}}/products"
        },
        extract: {
          selector: ".product-card",
          selector_type: "css"
        },
        fields: {
          id: {
            selector: ".product-id",
            selector_type: "css",
            type: "text",
            transform: ["trim"]
          },
          title: {
            selector: "h3.title",
            selector_type: "css",
            type: "text",
            transform: ["trim"]
          }
        }
      },
      {
        id: "details",
        for_each: {
          from: "products",
          field: "id"
        },
        request: {
          method: "GET",
          url: "{{base_url}}/product/{{id}}"
        },
        extract: {
          selector: "#product-detail",
          selector_type: "css"
        },
        fields: {
          price: {
            selector: ".price-value",
            selector_type: "css",
            type: "text",
            transform: ["trim"]
          }
        }
      }
    ]
  };

  function initEditor() {
    const textarea = document.getElementById("json-editor");
    editor = CodeMirror.fromTextArea(textarea, {
      mode: { name: "javascript", json: true },
      theme: "dracula",
      lineNumbers: true,
      autoCloseBrackets: true,
      matchBrackets: true,
      indentUnit: 2,
      tabSize: 2,
      lineWrapping: true
    });
    editor.setValue(JSON.stringify(defaultSampleConfig, null, 2));
  }

  function setupTabs() {
    const tabBtns = document.querySelectorAll(".tab-btn");
    tabBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        tabBtns.forEach(b => b.classList.remove("active"));
        document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

        btn.classList.add("active");
        const targetId = btn.getAttribute("data-tab");
        const pane = document.getElementById(targetId);
        if (pane) pane.classList.add("active");
      });
    });
  }

  async function apiCall(endpoint, data = null) {
    try {
      const options = {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      };
      if (data) options.body = JSON.stringify(data);
      const resp = await fetch(endpoint, options);
      return await resp.json();
    } catch (err) {
      console.error("API error:", err);
      return null;
    }
  }

  function updateStatus(statusText, type = "idle") {
    const badge = document.getElementById("session-status");
    badge.textContent = statusText;
    badge.className = "status-badge badge-" + type;
  }

  function updateValidationAlert(valResult) {
    const alertBox = document.getElementById("validation-alert");
    const alertTitle = document.getElementById("alert-title");
    const alertBody = document.getElementById("alert-body");

    if (!valResult || valResult.valid) {
      alertBox.classList.add("hidden");
      return;
    }

    alertBox.classList.remove("hidden");
    if (valResult.syntax_error) {
      alertTitle.textContent = "JSON Syntax Error";
      alertBody.textContent = valResult.syntax_error.message;
      if (valResult.syntax_error.line) {
        editor.setCursor({ line: valResult.syntax_error.line - 1, ch: 0 });
      }
    } else if (valResult.schema_errors && valResult.schema_errors.length > 0) {
      alertTitle.textContent = "Configuration Error";
      alertBody.textContent = valResult.schema_errors.map(e => e.message).join("\n");
    }
  }

  function highlightActiveStepLine(lineNumber) {
    if (activeLineMarker !== null) {
      editor.removeLineClass(activeLineMarker, "background", "active-step-line");
    }
    if (lineNumber && lineNumber > 0) {
      const lineIdx = lineNumber - 1;
      activeLineMarker = lineIdx;
      editor.addLineClass(lineIdx, "background", "active-step-line");
      editor.scrollIntoView({ line: lineIdx, ch: 0 }, 100);
    }
  }

  function renderKeyValueTable(containerId, obj) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";
    if (!obj || Object.keys(obj).length === 0) {
      container.innerHTML = '<span class="kv-val">None</span>';
      return;
    }
    for (const [k, v] of Object.entries(obj)) {
      const keyElem = document.createElement("div");
      keyElem.className = "kv-key";
      keyElem.textContent = k;

      const valElem = document.createElement("div");
      valElem.className = "kv-val";
      valElem.textContent = typeof v === "object" ? JSON.stringify(v) : String(v);

      container.appendChild(keyElem);
      container.appendChild(valElem);
    }
  }

  function renderState(state) {
    if (!state) return;

    updateValidationAlert(state.validation);

    if (state.validation && !state.validation.valid) {
      updateStatus("Invalid Config", "error");
      return;
    }

    updateStatus("Ready", "success");

    // Highlight active step line in CodeMirror
    highlightActiveStepLine(state.line_number);

    // Step indicators
    const currentStepNum = state.total_steps > 0 ? state.current_step_index + 1 : 0;
    document.getElementById("step-counter").textContent = `Step ${currentStepNum} / ${state.total_steps}`;
    document.getElementById("step-id-badge").textContent = state.step_id || "none";

    // Loop iteration indicators
    const iterControls = document.getElementById("iteration-controls");
    if (state.total_iterations > 1) {
      iterControls.classList.remove("hidden");
      document.getElementById("iter-counter").textContent = `${state.current_iteration_index + 1} / ${state.total_iterations}`;
      document.getElementById("loop-context-badge").textContent = "Context: " + JSON.stringify(state.loop_context || {});
    } else {
      iterControls.classList.add("hidden");
    }

    // HTML Selector info bar
    const ext = state.extract || {};
    document.getElementById("info-selector").textContent = ext.selector || "(root document)";
    document.getElementById("info-type").textContent = ext.selector_type || "css";
    document.getElementById("info-matches").textContent = ext.match_count !== undefined ? ext.match_count : "-";

    // HTML Preview iframe
    const iframe = document.getElementById("preview-iframe");
    iframe.src = "/api/preview-html?t=" + Date.now();

    // Extracted Data tab
    document.getElementById("data-results-view").textContent = JSON.stringify(state.results || [], null, 2);

    // Request tab
    const req = state.request || {};
    document.getElementById("req-method").textContent = req.method || "GET";
    document.getElementById("req-url").textContent = req.url || "-";
    renderKeyValueTable("req-headers-table", req.headers);
    renderKeyValueTable("req-params-table", req.params);

    // Response tab
    const resp = state.response || {};
    document.getElementById("resp-status").textContent = resp.status_code ? `${resp.status_code} OK` : "-";
    document.getElementById("resp-duration").textContent = resp.duration_ms ? `${resp.duration_ms} ms` : "-";
    document.getElementById("resp-size").textContent = resp.size_bytes ? `${resp.size_bytes} B` : "-";
    document.getElementById("resp-content-type").textContent = resp.content_type || "-";
    renderKeyValueTable("resp-headers-table", resp.headers);
    document.getElementById("resp-body-view").textContent = resp.text || "(empty body)";

    // Transforms tab
    const transformsContainer = document.getElementById("transforms-pipeline-view");
    transformsContainer.innerHTML = "";
    const fields = state.fields || {};
    if (Object.keys(fields).length === 0) {
      transformsContainer.innerHTML = "<p>No fields extracted for this step.</p>";
    } else {
      for (const [fname, ftrace] of Object.entries(fields)) {
        const fieldBox = document.createElement("div");
        fieldBox.className = "json-code-block";
        fieldBox.style.marginBottom = "10px";

        let html = `<strong>Field: ${fname}</strong> | Selector: <code>${ftrace.selector || "-"}</code> | Matches: ${ftrace.match_count}\n`;
        html += `Raw: ${JSON.stringify(ftrace.raw_values)}\n`;

        if (ftrace.transform_trace && ftrace.transform_trace.length > 0) {
          html += "Pipeline:\n";
          ftrace.transform_trace.forEach((step, i) => {
            html += `  [${i+1}] ${step.name} (${JSON.stringify(step.spec)}) -> ${JSON.stringify(step.output)}\n`;
          });
        }
        html += `Final Value: ${JSON.stringify(ftrace.final_value)}`;
        fieldBox.innerHTML = html;
        transformsContainer.appendChild(fieldBox);
      }
    }
  }

  // Event Listeners
  document.getElementById("btn-apply").addEventListener("click", async () => {
    const jsonStr = editor.getValue();
    const state = await apiCall("/api/session/load", { config_json: jsonStr });
    renderState(state);
  });

  document.getElementById("btn-run").addEventListener("click", async () => {
    const jsonStr = editor.getValue();
    const state = await apiCall("/api/session/load", { config_json: jsonStr });
    renderState(state);
  });

  document.getElementById("btn-rerun").addEventListener("click", async () => {
    const jsonStr = editor.getValue();
    const state = await apiCall("/api/session/rerun", { config_json: jsonStr });
    renderState(state);
  });

  document.getElementById("btn-restart").addEventListener("click", async () => {
    const state = await apiCall("/api/session/restart");
    renderState(state);
  });

  document.getElementById("btn-next-step").addEventListener("click", async () => {
    const state = await apiCall("/api/session/next");
    renderState(state);
  });

  document.getElementById("btn-prev-step").addEventListener("click", async () => {
    const state = await apiCall("/api/session/previous");
    renderState(state);
  });

  document.getElementById("btn-next-iter").addEventListener("click", async () => {
    const state = await apiCall("/api/session/next-iteration");
    renderState(state);
  });

  document.getElementById("btn-prev-iter").addEventListener("click", async () => {
    const state = await apiCall("/api/session/previous-iteration");
    renderState(state);
  });

  // Init
  initEditor();
  setupTabs();

  // Load initial session state on boot
  (async () => {
    const initialState = await apiCall("/api/session/load", { config_json: editor.getValue() });
    renderState(initialState);
  })();
});
