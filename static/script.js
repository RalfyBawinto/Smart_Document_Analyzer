const toggleBtn = document.getElementById("toggleModeBtn");
const analyzeBtn = document.getElementById("analyzeBtn");
const loadingSpinner = document.getElementById("loadingSpinner");
const resultSection = document.getElementById("resultSection");
const fileInput = document.getElementById("fileInput");
const fileInfo = document.getElementById("fileInfo");
const uploadBox = document.getElementById("uploadBox");
const summaryText = document.getElementById("summaryText");
const highlightList = document.getElementById("highlightList");
const copyBtn = document.getElementById("copyBtn");
const body = document.body;

// Toggle light/dark mode
toggleBtn.addEventListener("click", () => {
  body.classList.toggle("light-mode");
  body.classList.toggle("dark-mode");
  toggleBtn.textContent = body.classList.contains("light-mode")
    ? "Ganti ke Dark Mode"
    : "Ganti ke Light Mode";
});

// File input listener
fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (file) {
    if (file.type !== "application/pdf") {
      alert("Hanya file PDF yang diperbolehkan.");
      fileInput.value = "";
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      alert("Ukuran file melebihi 5 MB.");
      fileInput.value = "";
      return;
    }
    fileInfo.textContent = `File terpilih: ${file.name} (${(
      file.size /
      1024 /
      1024
    ).toFixed(2)} MB)`;
    fileInfo.classList.remove("hidden");
    analyzeBtn.classList.remove("hidden");
    uploadBox.classList.add("hidden");
  }
});

// Analyze PDF
// Analyze PDF
analyzeBtn.addEventListener("click", async () => {
  const file = fileInput.files[0];
  if (!file) return alert("Harap unggah file PDF terlebih dahulu.");

  analyzeBtn.disabled = true;
  loadingSpinner.classList.remove("hidden");
  resultSection.classList.add("hidden");

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("http://127.0.0.1:8000/analyze", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    let data;
    try {
      data = await response.json();
    } catch (jsonError) {
      throw new Error("Gagal memparsing respon JSON dari server.");
    }

    loadingSpinner.classList.add("hidden");
    analyzeBtn.disabled = false;
    resultSection.classList.remove("hidden");

    // Pastikan elemen ada sebelum mengubahnya
    if (summaryText) {
      summaryText.textContent = data.summary || "Ringkasan tidak tersedia.";
    }

    if (highlightList) {
      highlightList.innerHTML = "";
      if (data.highlights && data.highlights.length > 0) {
        data.highlights.forEach((kw) => {
          const li = document.createElement("li");
          li.textContent = kw;
          highlightList.appendChild(li);
        });
      } else {
        highlightList.innerHTML = "<li>Tidak ada highlight tersedia.</li>";
      }
    }
  } catch (err) {
    console.error("Gagal memproses:", err);
    loadingSpinner.classList.add("hidden");
    analyzeBtn.disabled = false;
    alert("Terjadi kesalahan saat menghubungi server. Silakan coba lagi.");
  }
});

// Copy summary
copyBtn.addEventListener("click", () => {
  navigator.clipboard
    .writeText(summaryText.textContent)
    .then(() => alert("Ringkasan berhasil disalin ke clipboard!"))
    .catch((err) => console.error("Gagal menyalin ringkasan:", err));
});
