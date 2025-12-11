const textInput = document.getElementById("textInput");
const targetSelect = document.getElementById("targetSelect");
const analyzeBtn = document.getElementById("analyzeBtn");
const resultDiv = document.getElementById("result");

function setLoading(isLoading) {
    if (isLoading) {
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = "Analiz ediliyor...";
    } else {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = "Analiz Et";
    }
}

function showResult(data) {
    resultDiv.classList.remove("hidden");
    resultDiv.classList.remove("result-error");

    let html = `
        <div class="result-title">Sonuç</div>

        <div class="result-section">
            <span class="result-label">Algılanan dil:</span>
            <span> ${data.source_language_name} (${data.source_language_code})</span>
        </div>
    `;

    if (data.translated_text) {
        html += `
            <div class="result-section" style="margin-top:8px;">
                <span class="result-label">Çeviri:</span>
                <div class="result-text">${data.translated_text}</div>
            </div>
        `;
    } else {
        html += `
            <div class="result-section" style="margin-top:8px;">
                <span class="result-label">Çeviri:</span>
                <span> Bu dil çifti için çeviri yapılamadı.</span>
            </div>
        `;
    }

    resultDiv.innerHTML = html;
}

function showError(message) {
    resultDiv.classList.remove("hidden");
    resultDiv.classList.add("result-error");
    resultDiv.innerHTML = `<strong>Hata:</strong> ${message}`;
}

analyzeBtn.addEventListener("click", async () => {
    const text = textInput.value.trim();
    const target = targetSelect.value;

    if (!text) {
        showError("Lütfen bir metin gir.");
        return;
    }

    setLoading(true);
    resultDiv.classList.add("hidden");

    try {
        const resp = await fetch("/api/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ text, target })
        });

        const data = await resp.json();

        if (!resp.ok) {
            showError(data.error || "Bilinmeyen hata oluştu.");
        } else {
            showResult(data);
        }
    } catch (err) {
        console.error(err);
        showError("Sunucuya ulaşılamadı.");
    } finally {
        setLoading(false);
    }
});
