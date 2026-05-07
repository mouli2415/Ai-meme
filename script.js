/**
 * script.js
 * ---------
 * Handles all UI interactions for the AI Meme Generator.
 *
 * Flow:
 *   1. User types a topic → clicks Generate (or presses Enter)
 *   2. POST { topic } → http://localhost:5000/generate
 *   3. Backend returns { caption, image_url }
 *   4. Display caption + meme image + download button
 */

"use strict";

// ── Config ────────────────────────────────────────────────────────────────────
const API_URL = "https://ai-meme.onrender.com/generate";

// ── DOM elements ──────────────────────────────────────────────────────────────
const topicInput     = document.getElementById("topicInput");
const generateBtn    = document.getElementById("generateBtn");
const errorBox       = document.getElementById("errorBox");
const errorText      = document.getElementById("errorText");
const loadingSection = document.getElementById("loadingSection");
const resultSection  = document.getElementById("resultSection");
const captionText    = document.getElementById("captionText");
const memeImage      = document.getElementById("memeImage");
const downloadBtn    = document.getElementById("downloadBtn");

// ── State ─────────────────────────────────────────────────────────────────────
let isLoading = false;


// ── Main handler ──────────────────────────────────────────────────────────────
async function handleGenerate() {
  if (isLoading) return;

  const topic = topicInput.value.trim();

  if (!topic) {
    showError("Please enter a topic first — e.g. \"exam stress\" or \"Monday morning\".");
    topicInput.focus();
    return;
  }

  if (topic.length < 2) {
    showError("Topic is too short. Try something more descriptive!");
    topicInput.focus();
    return;
  }

  setLoading(true);
  hideError();
  hideResult();

  try {
    console.log(`[frontend] Sending POST to ${API_URL} with topic: "${topic}"`);

    const response = await fetch(API_URL, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ topic }),
    });

    // Try to parse JSON even on error (Flask returns JSON error messages)
    let data;
    try {
      data = await response.json();
    } catch (_) {
      throw new Error(
        "The server returned an unreadable response. " +
        "Make sure the Flask backend is running on port 5000."
      );
    }

    if (!response.ok) {
      throw new Error(data?.error || `Server error ${response.status}: ${response.statusText}`);
    }

    if (!data.caption || !data.image_url) {
      throw new Error("Server response is missing caption or image_url.");
    }

    console.log("[frontend] Caption  :", data.caption);
    console.log("[frontend] Image URL:", data.image_url);

    displayResult(data.caption, data.image_url);

  } catch (err) {
    console.error("[frontend] Error:", err);

    // Friendly message for connection refused
    let msg = err.message;
    if (
      msg.includes("Failed to fetch") ||
      msg.includes("NetworkError") ||
      msg.includes("ERR_CONNECTION_REFUSED") ||
      msg.includes("Load failed")
    ) {
      msg =
        "Cannot reach the backend. " +
        "Open a terminal and run:  cd backend  then  python app.py";
    }

    showError(msg);

  } finally {
    setLoading(false);
  }
}


// ── UI helpers ────────────────────────────────────────────────────────────────

function setLoading(active) {
  isLoading            = active;
  generateBtn.disabled = active;

  if (active) {
    loadingSection.classList.remove("hidden");
    generateBtn.querySelector(".btn-label").textContent = "Generating…";
  } else {
    loadingSection.classList.add("hidden");
    generateBtn.querySelector(".btn-label").textContent = "Generate Meme";
  }
}

function displayResult(caption, imageUrl) {
  captionText.textContent = caption;

  // Fade image in once it loads
  memeImage.style.opacity = "0";
  memeImage.onload = () => {
    memeImage.style.transition = "opacity 0.4s ease";
    memeImage.style.opacity    = "1";
  };
  memeImage.src = imageUrl;
  memeImage.alt = `Meme about: ${topicInput.value.trim()}`;

  downloadBtn.href     = imageUrl;
  downloadBtn.download = `meme-${slugify(topicInput.value.trim())}.jpg`;

  resultSection.classList.remove("hidden");

  // Scroll to result on mobile
  setTimeout(() => {
    resultSection.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, 100);
}

function showError(msg) {
  errorText.textContent = msg;
  errorBox.classList.remove("hidden");
}

function hideError() {
  errorBox.classList.add("hidden");
  errorText.textContent = "";
}

function hideResult() {
  resultSection.classList.add("hidden");
}

function resetUI() {
  hideResult();
  hideError();
  topicInput.value = "";
  topicInput.focus();
}

function slugify(str) {
  return str
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "")
    .slice(0, 40) || "meme";
}


// ── Enter key shortcut ────────────────────────────────────────────────────────
topicInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    handleGenerate();
  }
});

// ── Auto-focus on load ────────────────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", () => {
  topicInput.focus();
  console.log("[frontend] Ready. Backend URL:", API_URL);
});