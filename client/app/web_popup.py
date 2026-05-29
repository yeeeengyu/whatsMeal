from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pyperclip
import webview

from app.api import MealApiClient, MealData
from app.config import DEFAULT_SCHOOL_NAME
from app.tray import MealTray


WINDOW_WIDTH = 420
WINDOW_HEIGHT = 640


class WebMealApp:
    def __init__(self, api_client: MealApiClient) -> None:
        self._api_client = api_client
        self._settings_path = _settings_path()
        self._window: webview.Window | None = None
        self._tray: MealTray | None = None
        self._visible = True

    def run(self) -> int:
        self._window = webview.create_window(
            "학교 급식",
            html=_html(),
            js_api=self,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            resizable=False,
            frameless=True,
            on_top=True,
            background_color="#f6f7f9",
        )
        self._tray = MealTray(self)
        self._tray.start()
        webview.start(self._on_started, debug=False)
        if self._tray is not None:
            self._tray.stop()
        return 0

    def get_initial_state(self) -> dict[str, Any]:
        return {
            "theme": self._load_theme(),
            "schoolName": self._load_school_name(),
        }

    def get_today(self, school_name: str | None = None) -> dict[str, Any]:
        return self._meal_response(lambda: self._api_client.get_today(school_name))

    def get_by_date(self, date_value: str, school_name: str | None = None) -> dict[str, Any]:
        return self._meal_response(lambda: self._api_client.get_by_date(date_value, school_name))

    def copy_meal(self, meal: dict[str, Any]) -> dict[str, Any]:
        try:
            pyperclip.copy(_meal_clipboard_text(meal))
        except Exception as exc:
            logging.exception("Failed to copy meal")
            return {"ok": False, "error": f"복사하지 못했습니다: {exc}"}

        return {"ok": True}

    def set_theme(self, theme: str) -> dict[str, Any]:
        if theme not in {"light", "dark"}:
            return {"ok": False}

        self._save_settings({"theme": theme})
        return {"ok": True}

    def set_school_name(self, school_name: str) -> dict[str, Any]:
        normalized_name = _normalize_school_name(school_name)
        self._save_settings({"schoolName": normalized_name})
        return {"ok": True, "schoolName": normalized_name}

    def hide_popup(self) -> None:
        self._visible = False
        if self._window is not None:
            self._window.hide()

    def show_popup(self) -> None:
        self._visible = True
        if self._window is not None:
            self._window.show()

    def refresh_today(self) -> None:
        self.show_popup()
        self._evaluate("window.WhatsMeal && window.WhatsMeal.loadToday();")

    def quit_app(self) -> None:
        logging.info("Quit requested")
        if self._tray is not None:
            self._tray.stop()
        if self._window is not None:
            self._window.destroy()

    def _on_started(self) -> None:
        self.refresh_today()

    def _meal_response(self, job) -> dict[str, Any]:
        try:
            meal = job()
        except Exception as exc:
            logging.exception("Failed to load meal")
            return {"ok": False, "error": str(exc)}

        return {"ok": True, "meal": asdict(meal)}

    def _evaluate(self, script: str) -> None:
        if self._window is None:
            return

        try:
            self._window.evaluate_js(script)
        except Exception:
            logging.exception("Failed to evaluate JavaScript")

    def _load_theme(self) -> str:
        settings = self._load_settings()
        theme = settings.get("theme", "light")
        return theme if theme in {"light", "dark"} else "light"

    def _load_school_name(self) -> str:
        settings = self._load_settings()
        return _normalize_school_name(settings.get("schoolName"))

    def _load_settings(self) -> dict[str, Any]:
        try:
            return json.loads(self._settings_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except Exception:
            logging.exception("Failed to load settings")
            return {}

    def _save_settings(self, update: dict[str, Any]) -> None:
        settings = self._load_settings()
        settings.update(update)
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        self._settings_path.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _settings_path() -> Path:
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / "WhatsMeal" / "settings.json"
    return Path.home() / ".whatsmeal" / "settings.json"


def _meal_clipboard_text(meal: dict[str, Any]) -> str:
    date = str(meal.get("date", ""))
    school_name = str(meal.get("school_name") or DEFAULT_SCHOOL_NAME)
    lunch = _string_list(meal.get("lunch"))
    dinner = _string_list(meal.get("dinner"))

    lines = [f"{date} {school_name} 급식", "", "[점심]"]
    lines.extend(f"- {dish}" for dish in lunch)
    lines.extend(["", "[저녁]"])
    lines.extend(f"- {dish}" for dish in dinner)
    return "\n".join(lines)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _normalize_school_name(value: Any) -> str:
    if not isinstance(value, str):
        return DEFAULT_SCHOOL_NAME

    normalized = value.strip()
    return normalized or DEFAULT_SCHOOL_NAME


def _html() -> str:
    return r"""
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {
      color-scheme: light;
      --window: #f6f7f9;
      --window-border: #cfd6df;
      --text: #111827;
      --muted: #526071;
      --control: #ffffff;
      --control-hover: #eef2f6;
      --control-border: #d5dbe3;
      --control-panel: #eef2f7;
      --card: #ffffff;
      --card-border: #e1e6ee;
      --dish: #253044;
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
      --secondary: #344054;
      --secondary-hover: #1f2937;
      --disabled-bg: #d8dee8;
      --disabled-text: #8b95a5;
      --segment: #e5eaf1;
      --segment-checked: #111827;
      --segment-checked-text: #ffffff;
    }

    [data-theme="dark"] {
      color-scheme: dark;
      --window: #111827;
      --window-border: #263244;
      --text: #f8fafc;
      --muted: #a9b4c4;
      --control: #1f2937;
      --control-hover: #273449;
      --control-border: #374151;
      --control-panel: #151e2c;
      --card: #182131;
      --card-border: #303b4f;
      --dish: #e5e7eb;
      --primary: #3b82f6;
      --primary-hover: #60a5fa;
      --secondary: #475569;
      --secondary-hover: #64748b;
      --disabled-bg: #2c3647;
      --disabled-text: #718096;
      --segment: #0f172a;
      --segment-checked: #e5e7eb;
      --segment-checked-text: #0f172a;
    }

    * {
      box-sizing: border-box;
    }

    html,
    body {
      width: 100%;
      height: 100%;
      margin: 0;
      overflow: hidden;
      background: transparent;
      font-family: "Malgun Gothic", "Segoe UI", system-ui, sans-serif;
      font-size: 12px;
      color: var(--text);
    }

    body {
      padding: 0;
      user-select: none;
    }

    button,
    input {
      font: inherit;
    }

    .shell {
      width: 100vw;
      height: 100vh;
      display: flex;
      flex-direction: column;
      gap: 10px;
      padding: 14px;
      background: var(--window);
      border: 1px solid var(--window-border);
      border-radius: 8px;
    }

    .header,
    .actions {
      display: flex;
      align-items: center;
      gap: 8px;
      min-width: 0;
    }

    .header-text {
      flex: 1;
      min-width: 0;
      -webkit-app-region: drag;
    }

    .title {
      margin: 0 0 1px;
      font-size: 17px;
      font-weight: 700;
      color: var(--text);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .date-label,
    .status,
    .theme-label {
      color: var(--muted);
    }

    .theme-label {
      font-weight: 600;
    }

    .control-panel {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 10px;
      background: var(--control-panel);
      border: 1px solid var(--control-border);
      border-radius: 8px;
    }

    .field-row,
    .theme-row {
      display: grid;
      grid-template-columns: 48px minmax(0, 1fr) 64px;
      align-items: center;
      gap: 8px;
      min-width: 0;
    }

    .theme-row {
      grid-template-columns: 48px minmax(0, 1fr);
    }

    .field-label {
      color: var(--muted);
      font-weight: 700;
    }

    .ghost,
    .theme-button,
    .primary,
    .secondary {
      border: 0;
      border-radius: 6px;
      font-weight: 700;
      cursor: pointer;
      -webkit-app-region: no-drag;
    }

    .ghost {
      height: 32px;
      padding: 0 12px;
      background: var(--control);
      color: var(--text);
      border: 1px solid var(--control-border);
    }

    .ghost:hover,
    .theme-button:hover {
      background: var(--control-hover);
    }

    .ghost:disabled,
    .secondary:disabled,
    .theme-button:disabled {
      opacity: 0.6;
      cursor: default;
    }

    .segment {
      display: flex;
      gap: 2px;
      padding: 2px;
      background: var(--segment);
      border: 1px solid var(--control-border);
      border-radius: 8px;
    }

    .theme-button {
      width: 68px;
      height: 28px;
      background: transparent;
      color: var(--muted);
    }

    .theme-button.active {
      background: var(--segment-checked);
      color: var(--segment-checked-text);
    }

    .status {
      min-height: 18px;
      line-height: 18px;
      word-break: keep-all;
    }

    .status.error {
      color: #dc2626;
    }

    .meal-scroll {
      flex: 1;
      min-height: 0;
      overflow-y: auto;
      overflow-x: hidden;
      padding-right: 1px;
    }

    .meal-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .meal-section {
      padding: 12px 14px;
      background: var(--card);
      border: 1px solid var(--card-border);
      border-radius: 8px;
    }

    .section-title {
      margin: 0 0 7px;
      font-size: 14px;
      font-weight: 700;
      color: var(--text);
    }

    .dish {
      margin: 0;
      color: var(--dish);
      line-height: 1.55;
      word-break: keep-all;
      overflow-wrap: anywhere;
    }

    .primary {
      width: 100%;
      height: 38px;
      background: var(--primary);
      color: #ffffff;
    }

    .primary:hover {
      background: var(--primary-hover);
    }

    .primary:disabled {
      background: var(--disabled-bg);
      color: var(--disabled-text);
      cursor: default;
    }

    .date-input,
    .school-input {
      flex: 1;
      min-width: 0;
      height: 34px;
      padding: 0 8px;
      background: var(--control);
      color: var(--text);
      border: 1px solid var(--control-border);
      border-radius: 6px;
    }

    .secondary {
      width: 100%;
      height: 34px;
      background: var(--secondary);
      color: #ffffff;
    }

    .secondary:hover {
      background: var(--secondary-hover);
    }

  </style>
</head>
<body>
  <main class="shell" data-theme="light">
    <section class="header">
      <div class="header-text">
        <h1 class="title" id="titleLabel">경북소프트웨어마이스터고등학교 급식</h1>
        <div class="date-label" id="dateLabel">오늘</div>
      </div>
      <button class="ghost" id="refreshButton" type="button">새로고침</button>
      <button class="ghost" id="closeButton" type="button">닫기</button>
    </section>

    <section class="control-panel">
      <div class="field-row">
        <label class="field-label" for="schoolInput">학교</label>
        <input class="school-input" id="schoolInput" type="text" autocomplete="off" spellcheck="false">
        <button class="secondary" id="schoolButton" type="button">적용</button>
      </div>

      <div class="field-row">
        <label class="field-label" for="dateInput">날짜</label>
        <input class="date-input" id="dateInput" type="date">
        <button class="secondary" id="searchButton" type="button">조회</button>
      </div>

      <div class="theme-row">
        <span class="theme-label">테마</span>
        <div class="segment">
          <button class="theme-button" id="lightThemeButton" type="button">화이트</button>
          <button class="theme-button" id="darkThemeButton" type="button">다크</button>
        </div>
      </div>
    </section>

    <div class="status" id="statusLabel"></div>

    <section class="meal-scroll">
      <div class="meal-list" id="mealList"></div>
    </section>

    <section class="actions">
      <button class="primary" id="copyButton" type="button" disabled>복사</button>
    </section>
  </main>

  <script>
    const DEFAULT_SCHOOL_NAME = "경북소프트웨어마이스터고등학교";
    const shell = document.querySelector(".shell");
    const titleLabel = document.getElementById("titleLabel");
    const statusLabel = document.getElementById("statusLabel");
    const dateLabel = document.getElementById("dateLabel");
    const mealList = document.getElementById("mealList");
    const copyButton = document.getElementById("copyButton");
    const dateInput = document.getElementById("dateInput");
    const schoolInput = document.getElementById("schoolInput");
    const refreshButton = document.getElementById("refreshButton");
    const schoolButton = document.getElementById("schoolButton");
    const searchButton = document.getElementById("searchButton");
    const lightThemeButton = document.getElementById("lightThemeButton");
    const darkThemeButton = document.getElementById("darkThemeButton");
    let currentMeal = null;
    let currentSchoolName = DEFAULT_SCHOOL_NAME;
    let isLoading = false;

    function todayString() {
      const now = new Date();
      const month = String(now.getMonth() + 1).padStart(2, "0");
      const date = String(now.getDate()).padStart(2, "0");
      return `${now.getFullYear()}-${month}-${date}`;
    }

    function setStatus(message, isError) {
      statusLabel.textContent = message || "";
      statusLabel.classList.toggle("error", Boolean(isError));
    }

    function setBusy(value) {
      isLoading = Boolean(value);
      refreshButton.disabled = isLoading;
      schoolButton.disabled = isLoading;
      searchButton.disabled = isLoading;
      copyButton.disabled = isLoading || !currentMeal;
    }

    function normalizeSchoolName(value) {
      const normalized = String(value || "").trim();
      return normalized || DEFAULT_SCHOOL_NAME;
    }

    function setSchoolName(value, save) {
      currentSchoolName = normalizeSchoolName(value);
      schoolInput.value = currentSchoolName;
      titleLabel.textContent = `${currentSchoolName} 급식`;

      if (save) {
        window.pywebview?.api?.set_school_name(currentSchoolName);
      }
    }

    function setLoading(message) {
      setStatus(message);
      currentMeal = null;
      setBusy(true);
      mealList.replaceChildren();
    }

    function setTheme(theme) {
      const safeTheme = theme === "dark" ? "dark" : "light";
      shell.dataset.theme = safeTheme;
      lightThemeButton.classList.toggle("active", safeTheme === "light");
      darkThemeButton.classList.toggle("active", safeTheme === "dark");
      window.pywebview?.api?.set_theme(safeTheme);
    }

    function dishNode(text) {
      const node = document.createElement("p");
      node.className = "dish";
      node.textContent = `• ${text}`;
      return node;
    }

    function sectionNode(title, dishes) {
      const section = document.createElement("section");
      section.className = "meal-section";

      const heading = document.createElement("h2");
      heading.className = "section-title";
      heading.textContent = title;
      section.appendChild(heading);

      const values = Array.isArray(dishes) && dishes.length ? dishes : ["정보 없음"];
      for (const dish of values) {
        section.appendChild(dishNode(dish));
      }

      return section;
    }

    function renderMeal(meal) {
      currentMeal = meal;
      dateLabel.textContent = meal.date || "오늘";
      setSchoolName(meal.school_name || currentSchoolName, true);
      setStatus("");
      setBusy(false);
      mealList.replaceChildren(
        sectionNode("점심", meal.lunch),
        sectionNode("저녁", meal.dinner),
      );
    }

    function renderError(message) {
      currentMeal = null;
      setBusy(false);
      mealList.replaceChildren();
      setStatus(message || "급식을 불러오지 못했습니다.", true);
    }

    async function requestMeal(loader, loadingMessage) {
      setLoading(loadingMessage);
      try {
        const response = await loader();
        if (response.ok) {
          renderMeal(response.meal);
        } else {
          renderError(response.error);
        }
      } catch (error) {
        renderError("급식을 불러오지 못했습니다.");
      }
    }

    async function loadToday() {
      await requestMeal(
        () => window.pywebview.api.get_today(currentSchoolName),
        "오늘 급식을 불러오는 중..."
      );
    }

    async function loadDate() {
      const dateValue = dateInput.value || todayString();
      await requestMeal(
        () => window.pywebview.api.get_by_date(dateValue, currentSchoolName),
        "급식을 불러오는 중..."
      );
    }

    async function applySchoolName() {
      setSchoolName(schoolInput.value, false);
      await loadToday();
    }

    async function copyMeal() {
      if (!currentMeal) {
        return;
      }

      const response = await window.pywebview.api.copy_meal(currentMeal);
      if (response.ok) {
        setStatus("복사됨");
        window.setTimeout(() => setStatus(""), 1600);
      } else {
        setStatus(response.error, true);
      }
    }

    async function init() {
      dateInput.value = todayString();
      const initialState = await window.pywebview.api.get_initial_state();
      setTheme(initialState.theme);
      setSchoolName(initialState.schoolName, false);
      await loadToday();
    }

    refreshButton.addEventListener("click", loadToday);
    document.getElementById("closeButton").addEventListener("click", () => {
      window.pywebview.api.hide_popup();
    });
    searchButton.addEventListener("click", loadDate);
    schoolButton.addEventListener("click", applySchoolName);
    schoolInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        applySchoolName();
      }
    });
    copyButton.addEventListener("click", copyMeal);
    lightThemeButton.addEventListener("click", () => setTheme("light"));
    darkThemeButton.addEventListener("click", () => setTheme("dark"));

    window.WhatsMeal = { loadToday };
    window.addEventListener("pywebviewready", init);
  </script>
</body>
</html>
"""
