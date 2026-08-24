let editor = null;

document.addEventListener("DOMContentLoaded", function () {
  let activeLineMarker = null;
  let currentConfigPath = null;

  const LOCAL_STORAGE_KEY = "scraper_config_draft";

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
            extract: {
              selector: ".product-id",
              selector_type: "css"
            },
            type: "text",
            transform: ["trim"]
          },
          title: {
            extract: {
              selector: "h3.title",
              selector_type: "css"
            },
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
            extract: {
              selector: ".price-value",
              selector_type: "css"
            },
            type: "text",
            transform: ["trim"]
          }
        }
      }
    ]
  };

  function getAvailableVariables(cm) {
    const vars = new Set(["loop_index", "loop_item"]);
    try {
      const text = cm.getValue();
      const config = JSON.parse(text);
      if (config.variables && typeof config.variables === "object") {
        Object.keys(config.variables).forEach(v => vars.add(v));
      }
      if (Array.isArray(config.steps)) {
        config.steps.forEach(step => {
          if (step.id) vars.add(step.id);
          if (step.fields && typeof step.fields === "object") {
            Object.keys(step.fields).forEach(f => vars.add(f));
          }
          if (step.for_each) {
            if (step.for_each.field) vars.add(step.for_each.field);
            if (step.for_each.sub_field) vars.add(step.for_each.sub_field);
          }
        });
      }
    } catch (e) {
      const text = cm.getValue();
      const varMatch = text.match(/"variables"\s*:\s*\{([^}]*)\}/);
      if (varMatch) {
        const keyMatches = varMatch[1].matchAll(/"([a-zA-Z0-9_]+)"\s*:/g);
        for (const m of keyMatches) vars.add(m[1]);
      }
      const stepIdMatches = text.matchAll(/"id"\s*:\s*"([a-zA-Z0-9_]+)"/g);
      for (const m of stepIdMatches) vars.add(m[1]);
    }
    return Array.from(vars);
  }

  function customHintProvider(cm) {
    const cur = cm.getCursor();
    const lineText = cm.getLine(cur.line);
    const textBefore = lineText.slice(0, cur.ch);

    let suggestions = [];
    let fromCh = cur.ch;
    let toCh = cur.ch;

    // 1. Template variable interpolation {{ ...
    const varMatch = textBefore.match(/\{\{([a-zA-Z0-9_]*)$/);
    if (varMatch) {
      const prefix = varMatch[1];
      fromCh = cur.ch - prefix.length;
      const availableVars = getAvailableVariables(cm);
      suggestions = availableVars.filter(v => v.toLowerCase().startsWith(prefix.toLowerCase()));
      return {
        list: suggestions,
        from: CodeMirror.Pos(cur.line, fromCh),
        to: CodeMirror.Pos(cur.line, toCh)
      };
    }

    // 2. Specific key values, e.g. "method": "GE|
    const valueMatch = textBefore.match(/"([a-zA-Z0-9_]+)"\s*:\s*"([a-zA-Z0-9_-]*)$/);
    if (valueMatch) {
      const key = valueMatch[1];
      const prefix = valueMatch[2];
      fromCh = cur.ch - prefix.length;

      if (key === "method") {
        const methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"];
        suggestions = methods.filter(m => m.toLowerCase().startsWith(prefix.toLowerCase()));
      } else if (key === "selector_type") {
        const types = ["css", "xpath", "jsonpath", "json"];
        suggestions = types.filter(t => t.toLowerCase().startsWith(prefix.toLowerCase()));
      } else if (key === "type") {
        const types = ["text", "attribute"];
        suggestions = types.filter(t => t.toLowerCase().startsWith(prefix.toLowerCase()));
      } else if (key === "Content-Type" || key === "Accept") {
        const mimeTypes = ["application/json", "text/html", "application/x-www-form-urlencoded", "multipart/form-data", "text/plain"];
        suggestions = mimeTypes.filter(m => m.toLowerCase().startsWith(prefix.toLowerCase()));
      }

      if (suggestions.length > 0) {
        return {
          list: suggestions,
          from: CodeMirror.Pos(cur.line, fromCh),
          to: CodeMirror.Pos(cur.line, toCh)
        };
      }
    }

    // 3. Transform array items: "transform": [ "tr|
    const transformMatch = textBefore.match(/"transform"\s*:\s*\[[^\]]*"([a-zA-Z0-9_]*)$/);
    if (transformMatch) {
      const prefix = transformMatch[1];
      fromCh = cur.ch - prefix.length;
      const transforms = ["trim", "lowercase", "uppercase", "strip_html", "regex", "replace", "split", "join", "default"];
      suggestions = transforms.filter(t => t.toLowerCase().startsWith(prefix.toLowerCase()));
      return {
        list: suggestions,
        from: CodeMirror.Pos(cur.line, fromCh),
        to: CodeMirror.Pos(cur.line, toCh)
      };
    }

    // 4. Header keys inside "headers": { ... }
    let inHeadersBlock = false;
    for (let l = cur.line; l >= Math.max(0, cur.line - 15); l--) {
      const ltext = cm.getLine(l);
      if (ltext.includes('"headers"')) {
        inHeadersBlock = true;
        break;
      }
      if (ltext.includes('}') && l < cur.line && !ltext.includes('{')) {
        break;
      }
    }

    const headerKeyMatch = textBefore.match(/"([a-zA-Z0-9_-]*)$/);
    if (inHeadersBlock && headerKeyMatch && !textBefore.includes(":")) {
      const prefix = headerKeyMatch[1];
      fromCh = cur.ch - prefix.length;
      const commonHeaders = [
        "User-Agent", "Accept", "Content-Type", "Authorization",
        "Cookie", "Host", "Referer", "Cache-Control", "Accept-Encoding", "Accept-Language"
      ];
      suggestions = commonHeaders.filter(h => h.toLowerCase().startsWith(prefix.toLowerCase()));
      if (suggestions.length > 0) {
        return {
          list: suggestions,
          from: CodeMirror.Pos(cur.line, fromCh),
          to: CodeMirror.Pos(cur.line, toCh)
        };
      }
    }

    // 5. JSON Object Property Keys
    const keyMatch = textBefore.match(/"([a-zA-Z0-9_]*)$/);
    if (keyMatch) {
      const prefix = keyMatch[1];
      fromCh = cur.ch - prefix.length;

      let context = "top";
      for (let l = cur.line; l >= Math.max(0, cur.line - 30); l--) {
        const ltext = cm.getLine(l);
        if (ltext.includes('"request"')) { context = "request"; break; }
        if (ltext.includes('"for_each"')) { context = "for_each"; break; }
        if (ltext.includes('"extract"')) { context = "extract"; break; }
        if (ltext.includes('"fields"')) { context = "fields"; break; }
        if (ltext.includes('"steps"')) { context = "step"; break; }
      }

      let keys = [];
      if (context === "top") {
        keys = ["name", "version", "variables", "steps"];
      } else if (context === "step") {
        keys = ["id", "parser", "for_each", "request", "extract", "fields", "conditions"];
      } else if (context === "request") {
        keys = ["method", "url", "response_type", "headers", "params"];
      } else if (context === "for_each") {
        keys = ["from", "field", "sub_field"];
      } else if (context === "extract") {
        keys = ["selector", "selector_type"];
      } else if (context === "fields") {
        keys = ["extract", "type", "attribute", "transform", "fields"];
      }

      suggestions = keys.filter(k => k.toLowerCase().startsWith(prefix.toLowerCase()));
      if (suggestions.length > 0) {
        return {
          list: suggestions,
          from: CodeMirror.Pos(cur.line, fromCh),
          to: CodeMirror.Pos(cur.line, toCh)
        };
      }
    }

    return null;
  }

  function jsonLinter(text) {
    const found = [];
    if (!text || !text.trim()) return found;

    try {
      JSON.parse(text);
    } catch (e) {
      const message = e.message || "Invalid JSON syntax";
      let line = 0;
      let ch = 0;

      // Try extracting line number from standard V8 JSON.parse error message (e.g., "... at line 5 column 12")
      const posMatch = message.match(/line\s+(\d+)\s+column\s+(\d+)/i) || message.match(/position\s+(\d+)/i);
      if (posMatch) {
        if (posMatch[2] !== undefined) {
          line = Math.max(0, parseInt(posMatch[1], 10) - 1);
          ch = Math.max(0, parseInt(posMatch[2], 10) - 1);
        } else if (posMatch[1] !== undefined) {
          const pos = parseInt(posMatch[1], 10);
          const lines = text.slice(0, pos).split("\n");
          line = lines.length - 1;
          ch = lines[lines.length - 1].length;
        }
      } else {
        // Fallback: check for common trailing comma issues
        const lines = text.split("\n");
        for (let i = 0; i < lines.length; i++) {
          if (/,\s*[\}\]]/.test(lines[i])) {
            line = i;
            ch = lines[i].indexOf(",");
            break;
          }
        }
      }

      const lineContent = editor ? editor.getLine(line) || "" : "";
      found.push({
        from: CodeMirror.Pos(line, ch),
        to: CodeMirror.Pos(line, Math.max(ch + 1, lineContent.length)),
        message: message,
        severity: "error"
      });
    }

    return found;
  }

  function initEditor() {
    const textarea = document.getElementById("json-editor");
    editor = CodeMirror.fromTextArea(textarea, {
      mode: { name: "javascript", json: true },
      theme: "dracula",
      lineNumbers: true,
      autoCloseBrackets: true,
      matchBrackets: true,
      foldGutter: true,
      gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter", "CodeMirror-lint-markers"],
      lint: { getAnnotations: jsonLinter, async: false },
      indentUnit: 2,
      tabSize: 2,
      lineWrapping: true,
      extraKeys: {
        "Ctrl-Space": function (cm) {
          cm.showHint({ hint: customHintProvider, completeSingle: false });
        },
        "Cmd-Space": function (cm) {
          cm.showHint({ hint: customHintProvider, completeSingle: false });
        }
      }
    });

    const savedDraft = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (savedDraft && savedDraft.trim()) {
      editor.setValue(savedDraft);
    } else {
      editor.setValue(JSON.stringify(defaultSampleConfig, null, 2));
    }

    editor.on("change", function () {
      localStorage.setItem(LOCAL_STORAGE_KEY, editor.getValue());
    });

    editor.on("inputRead", function (cm, change) {
      if (change.origin !== "+input") return;
      const ch = change.text[0];
      if (ch === "{" || ch === '"' || /[a-zA-Z0-9_-]/.test(ch)) {
        cm.showHint({ hint: customHintProvider, completeSingle: false });
      }
    });
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

  function setupResizer() {
    const resizer = document.getElementById("panel-resizer");
    const workspace = document.getElementById("workspace");
    if (!resizer || !workspace) return;

    let isDragging = false;

    resizer.addEventListener("mousedown", function () {
      isDragging = true;
      resizer.classList.add("resizing");
      document.body.style.userSelect = "none";
      document.body.style.cursor = "col-resize";
    });

    document.addEventListener("mousemove", function (e) {
      if (!isDragging) return;

      const rect = workspace.getBoundingClientRect();
      const offsetX = e.clientX - rect.left;
      const totalWidth = rect.width;

      const minWidth = totalWidth * 0.15;
      const maxWidth = totalWidth * 0.85;

      const clampedX = Math.max(minWidth, Math.min(maxWidth, offsetX));
      const percentage = (clampedX / totalWidth) * 100;

      workspace.style.setProperty("--left-panel-width", percentage + "%");

      if (editor) {
        editor.refresh();
      }
    });

    document.addEventListener("mouseup", function () {
      if (isDragging) {
        isDragging = false;
        resizer.classList.remove("resizing");
        document.body.style.userSelect = "";
        document.body.style.cursor = "";
        if (editor) {
          editor.refresh();
        }
      }
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

  function setGlobalButtonsDisabled(disabled) {
    const btns = document.querySelectorAll(".btn");
    btns.forEach(b => {
      b.disabled = disabled;
    });
  }

  async function handleAction(triggerBtn, actionFn) {
    const originalText = triggerBtn ? triggerBtn.textContent : "";
    if (triggerBtn) {
      triggerBtn.textContent = originalText + " ⏳";
    }

    setGlobalButtonsDisabled(true);
    updateStatus("Executing...", "running");

    try {
      const state = await actionFn();
      renderState(state);
    } finally {
      if (triggerBtn) {
        triggerBtn.textContent = originalText;
      }
    }
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
    if (!state) {
      updateStatus("Error", "error");
      setGlobalButtonsDisabled(false);
      return;
    }

    if (state.config_path) {
      currentConfigPath = state.config_path;
    }

    updateValidationAlert(state.validation);

    if (state.validation && !state.validation.valid) {
      updateStatus("Invalid Config", "error");
      setGlobalButtonsDisabled(false);
      return;
    }

    updateStatus("Ready", "success");

    highlightActiveStepLine(state.line_number);

    // Step indicators and button disabled states
    const currentStepNum = state.total_steps > 0 ? state.current_step_index + 1 : 0;
    document.getElementById("step-counter").textContent = `Step ${currentStepNum} / ${state.total_steps}`;
    document.getElementById("step-id-badge").textContent = state.step_id || "none";

    const isFirstStep = state.current_step_index === 0 && state.current_iteration_index === 0;
    const isLastStep =
      state.total_steps === 0 ||
      (state.current_step_index >= state.total_steps - 1 &&
        state.current_iteration_index >= state.total_iterations - 1);

    setGlobalButtonsDisabled(false);
    document.getElementById("btn-prev-step").disabled = isFirstStep;
    document.getElementById("btn-next-step").disabled = isLastStep;

    // Loop iteration indicators and button disabled states
    const iterControls = document.getElementById("iteration-controls");
    if (state.total_iterations > 1) {
      iterControls.classList.remove("hidden");
      document.getElementById("iter-counter").textContent = `${state.current_iteration_index + 1} / ${state.total_iterations}`;
      document.getElementById("loop-context-badge").textContent = "Context: " + JSON.stringify(state.loop_context || {});

      document.getElementById("btn-prev-iter").disabled = state.current_iteration_index === 0;
      document.getElementById("btn-next-iter").disabled = state.current_iteration_index >= state.total_iterations - 1;
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
            html += `  [${i + 1}] ${step.name} (${JSON.stringify(step.spec)}) -> ${JSON.stringify(step.output)}\n`;
          });
        }
        html += `Final Value: ${JSON.stringify(ftrace.final_value)}`;
        fieldBox.innerHTML = html;
        transformsContainer.appendChild(fieldBox);
      }
    }
  }

  // Import File Listener
  const btnImport = document.getElementById("btn-import");
  const fileImportInput = document.getElementById("file-import");

  if (btnImport && fileImportInput) {
    btnImport.addEventListener("click", () => {
      fileImportInput.click();
    });

    fileImportInput.addEventListener("change", (e) => {
      const file = e.target.files && e.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (evt) => {
        const content = evt.target.result;
        if (editor) {
          editor.setValue(content);
          localStorage.setItem(LOCAL_STORAGE_KEY, content);
          currentConfigPath = file.name;
          handleAction(btnApply, () => apiCall("/api/session/load", { config_json: content, filepath: file.name }));
        }
      };
      reader.readAsText(file);
      // reset value so re-uploading the same file works if needed
      fileImportInput.value = "";
    });
  }

  // Export Listener
  const btnExport = document.getElementById("btn-export");
  if (btnExport) {
    btnExport.addEventListener("click", () => {
      try {
        const jsonStr = editor.getValue();
        let filename = "scraper_config.json";
        try {
          const parsed = JSON.parse(jsonStr);
          if (parsed && parsed.name) {
            filename = `${parsed.name}.json`;
          }
        } catch (e) {
          // ignore error if invalid json
        }

        const blob = new Blob([jsonStr], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } catch (err) {
        alert("Failed to export configuration: " + err.message);
      }
    });
  }

  // Save Listener
  const btnSave = document.getElementById("btn-save");
  if (btnSave) {
    btnSave.addEventListener("click", async () => {
      let targetPath = currentConfigPath;
      if (!targetPath) {
        targetPath = prompt("Enter file path to save configuration:", "config.json");
        if (!targetPath) return; // User cancelled prompt
      }

      const jsonStr = editor.getValue();
      const res = await apiCall("/api/config/save", {
        config_json: jsonStr,
        filepath: targetPath
      });

      if (res && res.success) {
        currentConfigPath = res.filepath;
        alert(res.message || `Configuration saved to ${res.filepath}`);
      } else {
        const errorMsg = (res && res.detail) || "Failed to save configuration.";
        alert(`Save Error: ${errorMsg}`);
      }
    });
  }

  // Format JSON Listener
  const btnFormat = document.getElementById("btn-format");
  if (btnFormat) {
    btnFormat.addEventListener("click", () => {
      try {
        const parsed = JSON.parse(editor.getValue());
        const formatted = JSON.stringify(parsed, null, 2);
        editor.setValue(formatted);
        localStorage.setItem(LOCAL_STORAGE_KEY, formatted);
      } catch (err) {
        alert("Cannot format invalid JSON: " + err.message);
      }
    });
  }

  // Event Listeners with Loading States
  const btnApply = document.getElementById("btn-apply");
  btnApply.addEventListener("click", () => {
    handleAction(btnApply, () => apiCall("/api/session/load", { config_json: editor.getValue() }));
  });

  const btnRun = document.getElementById("btn-run");
  btnRun.addEventListener("click", () => {
    handleAction(btnRun, () => apiCall("/api/session/load", { config_json: editor.getValue() }));
  });

  const btnRerun = document.getElementById("btn-rerun");
  btnRerun.addEventListener("click", () => {
    handleAction(btnRerun, () => apiCall("/api/session/rerun", { config_json: editor.getValue() }));
  });

  const btnRestart = document.getElementById("btn-restart");
  btnRestart.addEventListener("click", () => {
    handleAction(btnRestart, () => apiCall("/api/session/restart"));
  });

  const btnNextStep = document.getElementById("btn-next-step");
  btnNextStep.addEventListener("click", () => {
    handleAction(btnNextStep, () => apiCall("/api/session/next"));
  });

  const btnPrevStep = document.getElementById("btn-prev-step");
  btnPrevStep.addEventListener("click", () => {
    handleAction(btnPrevStep, () => apiCall("/api/session/previous"));
  });

  const btnNextIter = document.getElementById("btn-next-iter");
  btnNextIter.addEventListener("click", () => {
    handleAction(btnNextIter, () => apiCall("/api/session/next-iteration"));
  });

  const btnPrevIter = document.getElementById("btn-prev-iter");
  btnPrevIter.addEventListener("click", () => {
    handleAction(btnPrevIter, () => apiCall("/api/session/previous-iteration"));
  });

  // Init
  initEditor();
  setupTabs();
  setupResizer();

  // Load initial session state on boot
  handleAction(null, () => apiCall("/api/session/load", { config_json: editor.getValue() }));
});
