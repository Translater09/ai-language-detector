const textInput = document.getElementById("textInput");
const targetSelect = document.getElementById("targetSelect");
const analyzeBtn = document.getElementById("analyzeBtn");
const resultDiv = document.getElementById("result");
const clearBtn = document.getElementById("clearBtn");
const toast = document.getElementById("toast");
const charCount = document.getElementById("charCount");

// --- DAKTİLO EFEKTİ ---
function typeWriter(element, text, speed = 5) {
    element.innerHTML = ""; 
    let i = 0;
    function type() {
        if (i < text.length) {
            const char = text.charAt(i);
            element.innerHTML += (char === '\n') ? '<br>' : char;
            i++;
            setTimeout(type, speed);
        } else {
            element.classList.remove("typing-cursor");
        }
    }
    element.classList.add("typing-cursor"); 
    type();
}

// --- YÜKLENİYOR ---
function setLoading(isLoading) {
    if (isLoading) {
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<span class="spinner"></span> Analiz ediliyor...';
    } else {
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<span class="btn-text">Analiz Et</span>';
    }
}

// --- SESLENDİRME ---
function speakResult() {
    window.speechSynthesis.cancel();
    const textToSpeak = document.getElementById("typewriter-target").innerText;
    const targetLang = targetSelect.value; 
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.lang = targetLang; 
    utterance.rate = 0.9;        
    window.speechSynthesis.speak(utterance);
}

// --- SONUÇ GÖSTERME ---
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
                <div id="typewriter-target" class="result-text"></div>
            </div>
            <div class="result-footer">
                <button class="copy-btn" onclick="speakResult()" title="Sesli Oku">
                    🔊 Dinle
                </button>
                <button class="copy-btn" onclick="copyToClipboard('${data.translated_text.replace(/'/g, "\\'")}')" title="Kopyala">
                    📋 Kopyala
                </button>
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

    if (data.translated_text) {
        const targetElement = document.getElementById("typewriter-target");
        typeWriter(targetElement, data.translated_text);
    }
}

// --- KOPYALAMA VE TOAST ---
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast();
    }).catch(err => {
        console.error('Kopyalama hatası:', err);
    });
}

function showToast() {
    toast.className = "toast show";
    setTimeout(function(){ 
        toast.className = toast.className.replace("show", ""); 
    }, 3000);
}

function showError(message) {
    resultDiv.classList.remove("hidden");
    resultDiv.classList.add("result-error");
    resultDiv.innerHTML = `<strong>Hata:</strong> ${message}`;
}

// --- ANA İŞLEM ---
async function performAnalysis() {
    window.speechSynthesis.cancel();
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
            headers: { "Content-Type": "application/json" },
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
}

// --- EVENT LISTENERS ---
analyzeBtn.addEventListener("click", performAnalysis);

textInput.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        event.preventDefault(); 
        performAnalysis();      
    }
});

if (clearBtn) {
    clearBtn.addEventListener("click", () => {
        window.speechSynthesis.cancel();
        
        textInput.value = "";
        textInput.style.height = 'auto'; 
        
        
        charCount.textContent = "0/5000";

        resultDiv.classList.add("hidden");
        resultDiv.innerHTML = "";
        textInput.focus();
    });
}


textInput.addEventListener('input', function() {
    
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';

    
    const text = this.value;
    const charLen = text.length;
    const maxLimit = 5000;

    charCount.textContent = `${charLen} /5000`;

    if (charLen >= maxLimit) {
        charCount.style.color = "#ef4444";
    } else {
        charCount.style.color = "#94a3b8"; 
    }
});

document.addEventListener("DOMContentLoaded", function () {
    const messages = document.querySelectorAll('.flash-message');

    if (messages.length > 0) {
      
        setTimeout(function () {
            messages.forEach(function (msg) {
              
                msg.style.transition = "opacity 0.5s ease, transform 0.5s ease";
                msg.style.opacity = "0";
                msg.style.transform = "translateY(-20px)";

                
                setTimeout(function () {
                    msg.remove();
                }, 500);
            });
        }, 3000); 
    }
});