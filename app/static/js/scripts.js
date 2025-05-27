document.addEventListener("DOMContentLoaded", function () {
  const sqlCode = document.getElementById("sqlCode");
  if (
    sqlCode &&
    sqlCode.textContent.trim() !== "" &&
    sqlCode.textContent.trim() !== "No SQL generated yet" &&
    sqlCode.textContent.trim().toUpperCase() !== "NONE"
  ) {
    hljs.highlightElement(sqlCode);
    const sqlSection = document.getElementById("sqlSection");
    if (sqlSection) {
      sqlSection.style.display = "block";
    }
  }

  const errorContainer = document.getElementById("errorContainer");
  if (errorContainer && errorContainer.textContent.trim() !== "") {
    errorContainer.style.display = "block";
  }

  bindEventListeners();

  if (localStorage.getItem("theme") === "dark") {
    document.body.classList.add("dark-mode");
    document.querySelector("#themeToggle i").className = "bi bi-sun";
  }

  updateHistoryUI();
});

function copySQL() {
  const sqlCode = document.getElementById("sqlCode");
  if (sqlCode) {
    navigator.clipboard.writeText(sqlCode.textContent).then(function () {
      const copyBtn = document.querySelector(".copy-btn");
      copyBtn.innerHTML = '<i class="bi bi-check"></i> Copied';
      setTimeout(function () {
        copyBtn.innerHTML = '<i class="bi bi-clipboard"></i> Copy';
      }, 2000);
    });
  }
}

function saveQueryToHistory(question, sql) {
  const history = getHistoryFromStorage();
  history.unshift({
    question: question,
    sql: sql,
    timestamp: new Date().toISOString(),
  });

  if (history.length > 10) {
    history.pop();
  }

  localStorage.setItem("queryHistory", JSON.stringify(history));
  updateHistoryUI();
}

function getHistoryFromStorage() {
  const historyStr = localStorage.getItem("queryHistory");
  return historyStr ? JSON.parse(historyStr) : [];
}

function updateHistoryUI() {
  const history = getHistoryFromStorage();
  const historyList = document.querySelector(".history-list");

  if (!historyList) return;

  historyList.innerHTML = "";

  if (history.length === 0) {
    historyList.innerHTML =
      '<div class="p-3 text-center text-muted">Query history is Empty</div>';
    return;
  }

  history.forEach(function (item, index) {
    const historyItem = document.createElement("div");
    historyItem.className = "history-item";
    historyItem.innerHTML = `
      <div class="history-question">${item.question}</div>
      <div class="history-sql">${item.sql}</div>
      <small class="text-muted">${formatDate(item.timestamp)}</small>
    `;

    historyItem.addEventListener("click", function () {
      document.getElementById("question").value = item.question;
      document.getElementById("question").focus();
    });

    historyList.appendChild(historyItem);
  });
}

function formatDate(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleString();
}

let mediaRecorder;
let audioChunks = [];

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: true,
    });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = (event) => {
      audioChunks.push(event.data);
    };

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
      const formData = new FormData();
      formData.append("file", audioBlob, "recording.webm");

      document.getElementById("stopRecordingBtn").style.display = "none";
      document.getElementById("startRecordingBtn").style.display =
        "inline-block";

      try {
        console.log("Sending audio to /ask-voice");
        document.getElementById("loadingIndicator").style.display = "block";
        const response = await fetch("/ask-voice", {
          method: "POST",
          body: formData,
        });
        console.log("Response:", response);
        document.getElementById("loadingIndicator").style.display = "none";

        if (response.ok) {
          const html = await response.text();
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, "text/html");
          document.querySelector(".app-container").innerHTML =
            doc.querySelector(".app-container").innerHTML;
          const sqlCode = document.getElementById("sqlCode");
          if (
            sqlCode &&
            sqlCode.textContent.trim() !== "" &&
            sqlCode.textContent.trim().toUpperCase() !== "NONE"
          ) {
            hljs.highlightElement(sqlCode);
            const sqlSection = document.getElementById("sqlSection");
            if (sqlSection) {
              sqlSection.style.display = "block";
            }
          }

          const resultsContainer = document.getElementById("resultsContainer");
          if (resultsContainer) {
            resultsContainer.style.display = "block";
          }

          const questionInput = document.getElementById("question");
          if (questionInput && questionInput.value.trim() !== "") {
            saveQueryToHistory(
              questionInput.value,
              sqlCode ? sqlCode.textContent : "-- Voice query executed"
            );
          }

          bindEventListeners();
        } else {
          console.error("Request failed:", response.status);
          document.getElementById(
            "errorContainer"
          ).innerHTML = `Failed to process voice query: HTTP ${response.status}`;
          document.getElementById("errorContainer").style.display = "block";
        }
      } catch (error) {
        console.error("Error:", error);
        document.getElementById("loadingIndicator").style.display = "none";
        document.getElementById(
          "errorContainer"
        ).innerHTML = `Error: ${error.message}`;
        document.getElementById("errorContainer").style.display = "block";
      }
    };

    mediaRecorder.start();

    document.getElementById("startRecordingBtn").style.display = "none";
    document.getElementById("stopRecordingBtn").style.display = "inline-block";

    setTimeout(() => {
      if (mediaRecorder.state === "recording") {
        mediaRecorder.stop();
        document.getElementById("stopRecordingBtn").style.display = "none";
        document.getElementById("startRecordingBtn").style.display =
          "inline-block";
      }
    }, 10000);
  } catch (error) {
    console.error("Error accessing microphone:", error);
    document.getElementById(
      "errorContainer"
    ).innerHTML = `Error accessing microphone: ${error.message}`;
    document.getElementById("errorContainer").style.display = "block";
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    document.getElementById("stopRecordingBtn").style.display = "none";
    document.getElementById("startRecordingBtn").style.display = "inline-block";
  }
}

function setupPdfDownload() {
  const downloadForm = document.getElementById("downloadReportForm");
  const downloadBtn = document.getElementById("downloadPdfBtn");

  if (!downloadForm || !downloadBtn) {
    console.log("PDF download elements not found");
    return;
  }

  const newForm = downloadForm.cloneNode(true);
  downloadForm.parentNode.replaceChild(newForm, downloadForm);

  newForm.addEventListener("submit", function (e) {
    e.preventDefault();

    try {
      const table = document.getElementById("resultsTable");
      if (!table) {
        console.error("Table not found");
        alert("Table not found");
        return;
      }

      const headers = Array.from(table.querySelectorAll("thead th")).map((th) =>
        th.textContent.trim()
      );

      const rows = Array.from(table.querySelectorAll("tbody tr")).map((tr) => {
        const cells = Array.from(tr.querySelectorAll("td"));
        const obj = {};
        headers.forEach((header, i) => {
          obj[header] = cells[i] ? cells[i].textContent.trim() : "";
        });
        return obj;
      });

      console.log("Headers:", headers);
      console.log("Rows:", rows);

      if (headers.length === 0 || rows.length === 0) {
        alert("No data for export");
        return;
      }

      document.getElementById("rowsJsonInput").value = JSON.stringify(rows);
      if (document.getElementById("headersJsonInput")) {
        document.getElementById("headersJsonInput").value =
          JSON.stringify(headers);
      }

      const newDownloadBtn = document.getElementById("downloadPdfBtn");
      if (newDownloadBtn) {
        newDownloadBtn.innerHTML =
          '<i class="bi bi-hourglass-split me-1"></i> Generating PDF...';
        newDownloadBtn.disabled = true;
      }

      const formData = new FormData(newForm);

      fetch("/download-report-pdf", {
        method: "POST",
        body: formData,
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }
          return response.blob();
        })
        .then((blob) => {
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.style.display = "none";
          a.href = url;
          a.download = `report_${new Date()
            .toISOString()
            .slice(0, 19)
            .replace(/:/g, "-")}.pdf`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
        })
        .catch((error) => {
          console.error("Error during downloading PDF:", error);
          alert("Error during generating PDF: " + error.message);
        })
        .finally(() => {
          const finalBtn = document.getElementById("downloadPdfBtn");
          if (finalBtn) {
            finalBtn.innerHTML =
              '<i class="bi bi-file-earmark-pdf me-1"></i> Download Report (PDF)';
            finalBtn.disabled = false;
          }
        });
    } catch (error) {
      console.error("Error in preparing data:", error);
      alert("Error in preparing data: " + error.message);
      const errorBtn = document.getElementById("downloadPdfBtn");
      if (errorBtn) {
        errorBtn.innerHTML =
          '<i class="bi bi-file-earmark-pdf me-1"></i> Download Report (PDF)';
        errorBtn.disabled = false;
      }
    }
  });
}

function bindEventListeners() {
  const queryForm = document.getElementById("queryForm");
  if (queryForm) {
    queryForm.addEventListener("submit", function () {
      document.getElementById("loadingIndicator").style.display = "block";
      const question = document.getElementById("question").value;
      if (question.trim() !== "") {
        saveQueryToHistory(question, "-- The request is executed...");
      }
    });
  }

  document.querySelectorAll(".copy-btn").forEach((btn) => {
    btn.addEventListener("click", copySQL);
  });

  document.querySelectorAll(".example-chip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      const input = document.getElementById("question");
      input.focus();
      input.scrollLeft = 0;
      input.value = this.textContent.trim();
      setTimeout(function () {
        input.scrollLeft = 0;
        input.setSelectionRange(0, 0);
      }, 0);
      const submitBtn = document.querySelector(".submit-btn");
      submitBtn.classList.add("pulse-animation");
      setTimeout(function () {
        submitBtn.classList.remove("pulse-animation");
      }, 2000);
    });
  });

  const schemaToggle = document.getElementById("schemaToggle");
  if (schemaToggle) {
    schemaToggle.addEventListener("click", function () {
      const schemaContainer = document.getElementById("schemaContainer");
      if (schemaContainer.style.display === "block") {
        schemaContainer.style.display = "none";
        this.innerHTML = '<i class="bi bi-table"></i> Show database structure';
      } else {
        schemaContainer.style.display = "block";
        this.innerHTML = '<i class="bi bi-table"></i> Hide database structure';
      }
    });
  }

  const historyToggle = document.getElementById("historyToggle");
  if (historyToggle) {
    historyToggle.addEventListener("click", function () {
      const historyContainer = document.getElementById("historyContainer");
      if (historyContainer) {
        historyContainer.classList.toggle("active");
      }
    });
  }

  const themeToggle = document.getElementById("themeToggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      document.body.classList.toggle("dark-mode");
      const icon = this.querySelector("i");
      if (document.body.classList.contains("dark-mode")) {
        icon.className = "bi bi-sun";
        localStorage.setItem("theme", "dark");
      } else {
        icon.className = "bi bi-moon";
        localStorage.setItem("theme", "light");
      }
    });
  }

  setupPdfDownload();

  updateHistoryUI();
}
