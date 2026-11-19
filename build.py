#!/usr/bin/env python3
"""
Couples Intimacy Games — Static Programmatic SEO Website Generator

Python 3, zero external dependencies.

Usage:
    python3 build.py

Optional configuration:
    BASE_URL=https://example.com python3 build.py

Input:
    data.csv

Output:
    dist/
        index.html
        game/
        category/
        topic/
        tag/
        sitemap.xml
        sitemap-1.xml
        sitemap.xsl
        robots.txt
        dmca.html
        2257.html
"""

import os

BASE_URL = os.environ.get(
    "BASE_URL",
    "https://couples-intimacy-games.velvetgrid.workers.dev"
).rstrip("/")

SITE_NAME = "Couples Intimacy Games"
NICHE_TOPIC = "Interactive Date Night Questions, Truth or Dare & Couples Games"
CONTACT_EMAIL = "nancympatten@gmail.com"
AFFILIATE_URL = "#affiliate-link"
AFFILIATE_CTA_TEXT = "Explore Interactive Couples Experiences & Live Shows"

import csv
import re
import json
import html
import math
import shutil
import random
import hashlib
from collections import Counter, defaultdict
from datetime import datetime, timezone
from urllib.parse import quote

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

ROOT = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(ROOT, "data.csv")
DIST = os.path.join(ROOT, "dist")

PER_PAGE = 24
RELATED_LIMIT = 8
LATEST_LIMIT = 30

EXPECTED_COLUMNS = [
    "slug",
    "title",
    "category",
    "subcategory",
    "target_keyword",
    "game_cards",
    "description",
    "tags",
    "faq_q1",
    "faq_a1",
    "faq_q2",
    "faq_a2",
    "upload_date",
]

COLORS = {
    "background": "#0b0910",
    "card": "#161221",
    "card2": "#1d182a",
    "pink": "#ec4899",
    "violet": "#8b5cf6",
    "text": "#f8f4fc",
    "muted": "#aaa0b5",
    "border": "#30263d",
}

# ---------------------------------------------------------
# GENERAL HELPERS
# ---------------------------------------------------------

def esc(value):
    return html.escape(str(value or ""), quote=True)


def slugify(value):
    value = str(value or "").lower().strip()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[\s_]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-") or "uncategorized"


def safe_filename(value):
    return re.sub(r"[^a-zA-Z0-9_-]", "", str(value))


def split_tags(value):
    if not value:
        return []

    parts = re.split(r"[,;|]", str(value))

    result = []
    seen = set()

    for part in parts:
        tag = part.strip()

        if not tag:
            continue

        key = tag.lower()

        if key not in seen:
            result.append(tag)
            seen.add(key)

    return result


def split_cards(value):
    if not value:
        return []

    cards = []

    for item in str(value).split("|"):
        item = item.strip()

        if item and item not in cards:
            cards.append(item)

    return cards


def normalize_date(value):
    value = str(value or "").strip()

    if not value:
        return "Unknown"

    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%Y-%m-%d %H:%M:%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).strftime("%Y-%m-%d")
    except ValueError:
        return "Unknown"


def date_sort_key(game):
    date = normalize_date(game["upload_date"])

    try:
        return datetime.strptime(date, "%Y-%m-%d").timestamp()
    except ValueError:
        return 0


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def canonical(path):
    return BASE_URL + "/" + path.lstrip("/")


def json_script(data):
    return json.dumps(
        data,
        ensure_ascii=False
    ).replace("</", "<\\/")


def format_count(number, singular, plural=None):
    plural = plural or singular + "s"
    return f"{number} {singular if number == 1 else plural}"


def truncate(value, length=160):
    value = re.sub(r"\s+", " ", str(value or "")).strip()

    if len(value) <= length:
        return value

    return value[:length - 3].rsplit(" ", 1)[0] + "..."


# ---------------------------------------------------------
# CSV LOADING
# ---------------------------------------------------------

def load_games():
    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(
            f"Missing input file: {CSV_FILE}"
        )

    games = []

    with open(
        CSV_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        if not reader.fieldnames:
            raise ValueError("data.csv has no header row.")

        missing = [
            col for col in EXPECTED_COLUMNS
            if col not in reader.fieldnames
        ]

        if missing:
            raise ValueError(
                "Missing required CSV columns: "
                + ", ".join(missing)
            )

        seen_slugs = set()

        for row_number, row in enumerate(reader, start=2):

            game = {
                column: (row.get(column) or "").strip()
                for column in EXPECTED_COLUMNS
            }

            if not game["title"]:
                print(
                    f"Warning: Skipping row {row_number}: missing title."
                )
                continue

            if not game["slug"]:
                game["slug"] = slugify(game["title"])

            game["slug"] = safe_filename(
                slugify(game["slug"])
            )

            if game["slug"] in seen_slugs:
                raise ValueError(
                    f"Duplicate slug '{game['slug']}' "
                    f"at CSV row {row_number}."
                )

            seen_slugs.add(game["slug"])

            game["category"] = (
                game["category"] or "General Couples Games"
            )

            game["subcategory"] = (
                game["subcategory"] or "General"
            )

            game["target_keyword"] = (
                game["target_keyword"] or game["title"]
            )

            game["description"] = (
                game["description"]
                or f"Explore {game['title']}, an interactive "
                   "couples game designed to encourage connection."
            )

            game["tags_list"] = split_tags(game["tags"])
            game["cards_list"] = split_cards(game["game_cards"])
            game["upload_date"] = normalize_date(
                game["upload_date"]
            )

            if not game["cards_list"]:
                game["cards_list"] = [
                    "What is one thing you appreciate about your partner?",
                    "What would your ideal date night look like?",
                    "What is a favorite memory you share?",
                    "What makes you feel most connected?",
                    "What is something new you would enjoy trying together?",
                    "What is one question you have always wanted to ask?"
                ]

            if len(game["cards_list"]) < 6:
                print(
                    f"Warning: {game['slug']} has fewer than "
                    "6 unique game cards."
                )

            games.append(game)

    if not games:
        raise ValueError("No valid game records found in data.csv.")

    return games


# ---------------------------------------------------------
# SHARED DATA INDEXES
# ---------------------------------------------------------

def build_indexes(games):

    categories = defaultdict(list)
    subcategories = defaultdict(list)
    tags = defaultdict(list)

    for game in games:

        game["category_slug"] = slugify(game["category"])
        game["subcategory_slug"] = slugify(game["subcategory"])

        categories[game["category_slug"]].append(game)

        subcategories[game["subcategory_slug"]].append(game)

        for tag in game["tags_list"]:
            tags[slugify(tag)].append(game)

    return categories, subcategories, tags


# ---------------------------------------------------------
# SHARED HTML COMPONENTS
# ---------------------------------------------------------

def global_css():
    return r"""
<style>
:root {
    color-scheme: dark;
    --bg: #0b0910;
    --card: #161221;
    --card2: #1d182a;
    --pink: #ec4899;
    --violet: #8b5cf6;
    --text: #f8f4fc;
    --muted: #aaa0b5;
    --border: #30263d;
}

* {
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
}

body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: Inter, system-ui, -apple-system,
        BlinkMacSystemFont, "Segoe UI", sans-serif;
    line-height: 1.7;
}

a {
    color: inherit;
    text-decoration: none;
}

a:hover {
    color: var(--pink);
}

button, input, select {
    font: inherit;
}

button {
    cursor: pointer;
}

.container {
    width: min(1160px, calc(100% - 36px));
    margin: auto;
}

.header {
    position: sticky;
    top: 0;
    z-index: 50;
    background: rgba(11,9,16,.94);
    backdrop-filter: blur(16px);
    border-bottom: 1px solid var(--border);
}

.nav {
    min-height: 70px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
}

.brand {
    font-size: 19px;
    font-weight: 900;
    letter-spacing: -.6px;
}

.brand span {
    color: var(--pink);
}

.nav-links {
    display: flex;
    gap: 18px;
    align-items: center;
    font-size: 13px;
    color: var(--muted);
}

.hero {
    padding: 76px 0 45px;
    text-align: center;
}

.eyebrow {
    display: inline-block;
    color: #f9a8d4;
    background: rgba(236,72,153,.12);
    border: 1px solid rgba(236,72,153,.25);
    border-radius: 30px;
    padding: 5px 14px;
    font-size: 12px;
    font-weight: 800;
}

h1 {
    font-size: clamp(32px, 6vw, 58px);
    line-height: 1.13;
    letter-spacing: -2px;
    margin: 20px auto;
}

h2 {
    font-size: clamp(23px, 4vw, 32px);
    letter-spacing: -.8px;
    line-height: 1.25;
}

h3 {
    line-height: 1.35;
}

.gradient {
    background: linear-gradient(100deg, #f472b6, #a78bfa);
    background-clip: text;
    -webkit-background-clip: text;
    color: transparent;
}

.muted {
    color: var(--muted);
}

.section {
    padding: 34px 0;
}

.section-heading {
    margin-bottom: 22px;
}

.grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0,1fr));
    gap: 17px;
}

.card {
    padding: 21px;
    border: 1px solid var(--border);
    background: var(--card);
    border-radius: 17px;
    transition: transform .2s, border-color .2s;
}

.card:hover {
    transform: translateY(-3px);
    border-color: var(--pink);
}

.game-card {
    display: block;
}

.game-card h3 {
    font-size: 17px;
    margin: 8px 0;
}

.game-card p {
    font-size: 13px;
    color: var(--muted);
}

.meta {
    font-size: 11px;
    color: #e9a5ce;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: .6px;
}

.pills {
    display: flex;
    flex-wrap: wrap;
    gap: 9px;
}

.pill {
    display: inline-flex;
    border: 1px solid var(--border);
    background: var(--card);
    color: #e9d5ff;
    border-radius: 30px;
    padding: 7px 13px;
    font-size: 12px;
}

.pill:hover {
    border-color: var(--pink);
}

.search-wrap {
    max-width: 700px;
    margin: 30px auto;
}

.search {
    width: 100%;
    background: var(--card);
    color: var(--text);
    border: 1px solid var(--border);
    padding: 17px 20px;
    border-radius: 14px;
    outline: none;
}

.search:focus {
    border-color: var(--pink);
}

.btn {
    display: inline-flex;
    justify-content: center;
    align-items: center;
    padding: 11px 17px;
    border: 0;
    border-radius: 11px;
    background: linear-gradient(110deg,var(--pink),var(--violet));
    color: white;
    font-weight: 800;
    font-size: 13px;
}

.btn:hover {
    color: white;
    filter: brightness(1.12);
}

.btn-secondary {
    background: var(--card2);
    border: 1px solid var(--border);
    color: var(--text);
}

.controls {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.deck {
    margin-top: 24px;
    perspective: 1100px;
}

.playing-card {
    position: relative;
    min-height: 260px;
    max-width: 650px;
    margin: auto;
    transform-style: preserve-3d;
    transition: transform .6s;
    cursor: pointer;
}

.playing-card.flipped {
    transform: rotateY(180deg);
}

.card-face {
    position: absolute;
    inset: 0;
    min-height: 260px;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 35px;
    text-align: center;
    border: 1px solid #63385d;
    border-radius: 22px;
    background:
        radial-gradient(circle at 15% 10%,
            rgba(236,72,153,.18), transparent 45%),
        var(--card);
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
}

.card-back {
    transform: rotateY(180deg);
    background:
        radial-gradient(circle at 85% 20%,
            rgba(139,92,246,.23), transparent 45%),
        var(--card2);
}

.card-face h3 {
    font-size: clamp(21px,4vw,29px);
    font-weight: 800;
}

.player-panel {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin: 22px 0;
}

.player {
    padding: 17px;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 13px;
    text-align: center;
}

.player.active {
    border-color: var(--pink);
    box-shadow: 0 0 20px rgba(236,72,153,.12);
}

.player strong {
    display: block;
    color: #f9a8d4;
}

.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin: 18px 0;
}

.field {
    display: block;
    width: 100%;
    background: var(--card);
    color: var(--text);
    border: 1px solid var(--border);
    padding: 12px;
    border-radius: 10px;
}

.audio-panel {
    padding: 22px;
    border: 1px solid var(--border);
    background: var(--card);
    border-radius: 17px;
    margin-top: 22px;
}

.audio-panel label {
    display: block;
    margin: 12px 0;
}

.audio-panel input[type=range] {
    width: 100%;
    accent-color: var(--pink);
}

.affiliate {
    padding: 30px;
    text-align: center;
    border-radius: 20px;
    border: 1px solid rgba(236,72,153,.4);
    background:
        radial-gradient(circle at 20% 20%,
            rgba(236,72,153,.16), transparent 50%),
        var(--card);
    margin: 30px 0;
}

.faq-item {
    border-bottom: 1px solid var(--border);
    padding: 16px 0;
}

.faq-item summary {
    cursor: pointer;
    font-weight: 800;
}

.pagination {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin: 30px 0;
}

.breadcrumbs {
    color: var(--muted);
    font-size: 12px;
    padding: 20px 0;
}

.footer {
    border-top: 1px solid var(--border);
    margin-top: 60px;
    padding: 38px 0;
    color: var(--muted);
    font-size: 12px;
}

.footer-links {
    display: flex;
    flex-wrap: wrap;
    gap: 18px;
}

.age-overlay {
    display: none;
    position: fixed;
    z-index: 9999;
    inset: 0;
    background: rgba(0,0,0,.94);
    backdrop-filter: blur(15px);
    align-items: center;
    justify-content: center;
    padding: 20px;
}

.age-box {
    width: min(450px,100%);
    padding: 32px;
    text-align: center;
    border: 1px solid var(--border);
    border-radius: 20px;
    background: var(--card);
}

.age-box h2 {
    color: var(--pink);
}

.empty-state {
    display: none;
    padding: 25px;
    text-align: center;
    color: var(--muted);
}

@media(max-width:850px) {
    .grid {
        grid-template-columns: repeat(2,minmax(0,1fr));
    }
}

@media(max-width:580px) {
    .grid {
        grid-template-columns: 1fr;
    }

    .hero {
        padding-top: 48px;
    }

    .nav-links {
        gap: 9px;
        font-size: 11px;
    }

    .form-row {
        grid-template-columns: 1fr;
    }

    .playing-card, .card-face {
        min-height: 240px;
    }

    .card-face {
        padding: 23px;
    }
}
</style>
"""


def age_modal():
    return """
<div class="age-overlay" id="ageOverlay" role="dialog"
     aria-modal="true" aria-labelledby="ageTitle">
    <div class="age-box">
        <div class="eyebrow">AGE-RESTRICTED WEBSITE</div>
        <h2 id="ageTitle">Are you 18 or older?</h2>
        <p class="muted">
            This website is intended exclusively for adults.
            By continuing, you confirm that you meet the
            legal age requirement in your location.
        </p>
        <button class="btn" id="ageYes">Yes, I am 18+</button>
        <p>
            <a href="https://www.google.com/" class="muted">
                No, leave this website
            </a>
        </p>
    </div>
</div>

<script>
(function() {
    try {
        if (localStorage.getItem("couples_age_verified") !== "yes") {
            document.getElementById("ageOverlay").style.display = "flex";
        }
    } catch(e) {
        document.getElementById("ageOverlay").style.display = "flex";
    }

    document.getElementById("ageYes").addEventListener("click", function() {
        try {
            localStorage.setItem("couples_age_verified", "yes");
        } catch(e) {}
        document.getElementById("ageOverlay").style.display = "none";
    });
})();
</script>
"""


def header():
    return """
<header class="header">
    <div class="container nav">
        <a class="brand" href="/">Couples <span>Intimacy</span> Games</a>
        <nav class="nav-links">
            <a href="/">Home</a>
            <a href="/#categories">Categories</a>
            <a href="/#latest">Latest Games</a>
        </nav>
    </div>
</header>
"""


def footer():
    return f"""
<footer class="footer">
    <div class="container">
        <div class="footer-links">
            <a href="/">Home</a>
            <a href="/dmca.html">DMCA</a>
            <a href="/2257.html">18 U.S.C. 2257</a>
            <a href="mailto:{CONTACT_EMAIL}">Contact</a>
            <a href="/sitemap.xml">Sitemap</a>
        </div>
        <p>
            © {datetime.now().year} {SITE_NAME}.
            For adults 18+ only. Play respectfully and
            communicate openly with your partner.
        </p>
        <p>
            All games are intended for consensual,
            respectful adult interaction.
        </p>
    </div>
</footer>
"""


def page_head(title, description, path, og_type="website"):
    url = canonical(path)

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="{COLORS['background']}">
<meta name="rating" content="RTA-5042-1996-1400-1577-RTA">
<title>{esc(title)}</title>
<meta name="description" content="{esc(truncate(description, 160))}">
<link rel="canonical" href="{esc(url)}">
<meta property="og:type" content="{esc(og_type)}">
<meta property="og:site_name" content="{esc(SITE_NAME)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(truncate(description, 160))}">
<meta property="og:url" content="{esc(url)}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(truncate(description, 160))}">
{global_css()}
</head>
<body>
"""


# ---------------------------------------------------------
# GAME CARDS AND RELATED GAMES
# ---------------------------------------------------------

def game_card_html(game):
    path = f"/game/{game['slug']}.html"

    search_text = " ".join([
        game["title"],
        game["target_keyword"],
        game["description"],
        " ".join(game["tags_list"]),
    ]).lower()

    return f"""
<a class="card game-card"
   href="{path}"
   data-search="{esc(search_text)}">
    <div class="meta">{esc(game['category'])}</div>
    <h3>{esc(game['title'])}</h3>
    <p>{esc(truncate(game['description'], 120))}</p>
    <div class="pills">
        <span class="pill">{esc(game['subcategory'])}</span>
        <span class="pill">{len(game['cards_list'])} cards</span>
    </div>
</a>
"""


def related_games(game, games):
    scored = []

    current_tags = set(
        slugify(tag) for tag in game["tags_list"]
    )

    for other in games:

        if other["slug"] == game["slug"]:
            continue

        score = 0

        if other["subcategory_slug"] == game["subcategory_slug"]:
            score += 10

        if other["category_slug"] == game["category_slug"]:
            score += 3

        other_tags = set(
            slugify(tag) for tag in other["tags_list"]
        )

        score += len(current_tags & other_tags) * 2

        scored.append((score, other["slug"], other))

    scored.sort(
        key=lambda item: (-item[0], item[1])
    )

    result = [item[2] for item in scored[:RELATED_LIMIT]]

    if len(result) < RELATED_LIMIT:
        already = {game["slug"]} | {
            item["slug"] for item in result
        }

        for other in games:
            if other["slug"] not in already:
                result.append(other)
                already.add(other["slug"])

            if len(result) == RELATED_LIMIT:
                break

    return result


# ---------------------------------------------------------
# INTERACTIVE GAME JAVASCRIPT
# ---------------------------------------------------------

def game_javascript(game):
    cards = json_script(game["cards_list"])

    return f"""
<script>
(function() {{
"use strict";

const originalCards = {cards};

let cards = originalCards.slice();
let currentIndex = 0;
let currentPlayer = 1;
let turnCount = 0;
let flipped = false;

const cardElement = document.getElementById("playingCard");
const front = document.getElementById("cardFront");
const back = document.getElementById("cardBack");
const counter = document.getElementById("cardCounter");

const name1 = document.getElementById("partner1");
const name2 = document.getElementById("partner2");

const player1 = document.getElementById("player1");
const player2 = document.getElementById("player2");
const turnLabel = document.getElementById("turnLabel");

function personalized(text) {{
    const first = (name1.value || "Partner 1").trim();
    const second = (name2.value || "Partner 2").trim();

    return text
        .replace(/\\[Partner 1\\]/gi, first)
        .replace(/\\[Partner 2\\]/gi, second)
        .replace(/\\{{Partner 1\\}}/gi, first)
        .replace(/\\{{Partner 2\\}}/gi, second);
}}

function showCard() {{
    if (!cards.length) return;

    front.textContent = "Tap to reveal your question";
    back.textContent = personalized(cards[currentIndex]);

    counter.textContent =
        "Card " + (currentIndex + 1) + " of " + cards.length;

    cardElement.classList.remove("flipped");
    flipped = false;
}}

function flipCard() {{
    flipped = !flipped;
    cardElement.classList.toggle("flipped", flipped);
}}

cardElement.addEventListener("click", flipCard);

name1.addEventListener("input", showCard);
name2.addEventListener("input", showCard);

document.getElementById("nextCard").addEventListener("click", function() {{
    currentIndex = (currentIndex + 1) % cards.length;
    showCard();
}});

document.getElementById("shuffleDeck").addEventListener("click", function() {{
    for (let i = cards.length - 1; i > 0; i--) {{
        const j = Math.floor(Math.random() * (i + 1));
        [cards[i], cards[j]] = [cards[j], cards[i]];
    }}

    currentIndex = 0;
    showCard();
}});

document.getElementById("copyCards").addEventListener("click", async function() {{
    const allCards = cards.map(function(card, index) {{
        return (index + 1) + ". " + personalized(card);
    }}).join("\\n\\n");

    try {{
        if (navigator.clipboard && window.isSecureContext) {{
            await navigator.clipboard.writeText(allCards);
        }} else {{
            const textarea = document.createElement("textarea");
            textarea.value = allCards;
            document.body.appendChild(textarea);
            textarea.select();

            if (!document.execCommand("copy")) {{
                throw new Error("Copy failed");
            }}

            textarea.remove();
        }}

        this.textContent = "Copied!";
        setTimeout(() => this.textContent = "Copy All Cards", 1500);
    }} catch(e) {{
        this.textContent = "Copy unavailable";
    }}
}});

function updatePlayers() {{
    player1.classList.toggle("active", currentPlayer === 1);
    player2.classList.toggle("active", currentPlayer === 2);

    turnLabel.textContent =
        "Turn " + turnCount + " · " +
        (currentPlayer === 1 ? "Player 1" : "Player 2");
}}

document.getElementById("nextTurn").addEventListener("click", function() {{
    currentPlayer = currentPlayer === 1 ? 2 : 1;
    turnCount++;
    updatePlayers();
}});

showCard();
updatePlayers();

// -----------------------------------------------------
// WEB AUDIO API ROMANTIC AMBIENCE
// -----------------------------------------------------

let audioContext = null;
let masterGain = null;
let oscillators = [];
let noiseSource = null;
let playing = false;

const soundSelect = document.getElementById("soundSelect");
const volumeSlider = document.getElementById("volumeSlider");
const audioButton = document.getElementById("audioButton");

function stopAudio() {{
    oscillators.forEach(function(osc) {{
        try {{ osc.stop(); }} catch(e) {{}}
    }});

    oscillators = [];

    if (noiseSource) {{
        try {{ noiseSource.stop(); }} catch(e) {{}}
        noiseSource = null;
    }}
}}

function addOscillator(frequency, type, gainValue) {{
    const osc = audioContext.createOscillator();
    const gain = audioContext.createGain();

    osc.type = type;
    osc.frequency.value = frequency;

    gain.gain.value = gainValue;

    osc.connect(gain);
    gain.connect(masterGain);

    osc.start();

    oscillators.push(osc);
}}

function addNoise() {{
    const bufferSize = 2 * audioContext.sampleRate;
    const buffer = audioContext.createBuffer(
        1, bufferSize, audioContext.sampleRate
    );

    const output = buffer.getChannelData(0);

    for (let i = 0; i < bufferSize; i++) {{
        output[i] = Math.random() * 2 - 1;
    }}

    noiseSource = audioContext.createBufferSource();
    const filter = audioContext.createBiquadFilter();
    const gain = audioContext.createGain();

    noiseSource.buffer = buffer;
    noiseSource.loop = true;

    filter.type = "lowpass";
    filter.frequency.value = 800;

    gain.gain.value = 0.09;

    noiseSource.connect(filter);
    filter.connect(gain);
    gain.connect(masterGain);

    noiseSource.start();
}}

function createAmbience() {{
    audioContext = new (
        window.AudioContext || window.webkitAudioContext
    )();

    masterGain = audioContext.createGain();

    masterGain.gain.value =
        Number(volumeSlider.value) / 100;

    masterGain.connect(audioContext.destination);

    const sound = soundSelect.value;

    if (sound === "rain") {{
        addNoise();
        addOscillator(110, "sine", 0.035);
        addOscillator(165, "sine", 0.018);
    }} else if (sound === "fire") {{
        addNoise();
        addOscillator(73, "triangle", 0.025);
        addOscillator(110, "sine", 0.025);
    }} else {{
        addOscillator(55, "sine", 0.08);
        addOscillator(82.41, "sine", 0.035);
        addOscillator(110, "sine", 0.025);
    }}

    playing = true;
    audioButton.textContent = "Pause Ambience";
}}

function toggleAudio() {{
    if (playing) {{
        stopAudio();

        if (audioContext) {{
            audioContext.close();
            audioContext = null;
        }}

        playing = false;
        audioButton.textContent = "Play Ambience";
        return;
    }}

    try {{
        createAmbience();
    }} catch(e) {{
        audioButton.textContent = "Audio unavailable";
    }}
}}

audioButton.addEventListener("click", toggleAudio);

soundSelect.addEventListener("change", function() {{
    if (playing) {{
        stopAudio();

        if (audioContext) {{
            audioContext.close();
            audioContext = null;
        }}

        playing = false;
        createAmbience();
    }}
}});

volumeSlider.addEventListener("input", function() {{
    if (masterGain) {{
        masterGain.gain.setTargetAtTime(
            Number(volumeSlider.value) / 100,
            audioContext.currentTime,
            0.05
        );
    }}
}});

window.addEventListener("pagehide", function() {{
    stopAudio();

    if (audioContext) {{
        audioContext.close();
        audioContext = null;
    }}
}});
}})();
</script>
"""


# ---------------------------------------------------------
# DETAIL PAGE
# ---------------------------------------------------------

def render_game_page(game, games):

    path = f"game/{game['slug']}.html"

    title = (
        f"{game['title']} | Interactive Couples Game "
        f"– {SITE_NAME}"
    )

    description = game["description"]

    related = related_games(game, games)

    faq = []

    if game["faq_q1"] and game["faq_a1"]:
        faq.append({
            "@type": "Question",
            "name": game["faq_q1"],
            "acceptedAnswer": {
                "@type": "Answer",
                "text": game["faq_a1"],
            }
        })

    if game["faq_q2"] and game["faq_a2"]:
        faq.append({
            "@type": "Question",
            "name": game["faq_q2"],
            "acceptedAnswer": {
                "@type": "Answer",
                "text": game["faq_a2"],
            }
        })

    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Article",
                "headline": game["title"],
                "description": description,
                "datePublished": (
                    game["upload_date"]
                    if game["upload_date"] != "Unknown"
                    else None
                ),
                "author": {
                    "@type": "Organization",
                    "name": SITE_NAME
                },
                "publisher": {
                    "@type": "Organization",
                    "name": SITE_NAME
                },
                "mainEntityOfPage": canonical(path),
                "articleSection": game["category"],
                "keywords": ", ".join(
                    [game["target_keyword"]] + game["tags_list"]
                )
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Home",
                        "item": canonical("index.html")
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": game["category"],
                        "item": canonical(
                            f"category/{game['category_slug']}/page-1.html"
                        )
                    },
                    {
                        "@type": "ListItem",
                        "position": 3,
                        "name": game["title"],
                        "item": canonical(path)
                    }
                ]
            },
            {
                "@type": "FAQPage",
                "mainEntity": faq
            }
        ]
    }

    category_url = (
        f"/category/{game['category_slug']}/page-1.html"
    )

    topic_url = f"/topic/{game['subcategory_slug']}.html"

    tags_html = "".join(
        f'<a class="pill" href="/tag/{slugify(tag)}.html">'
        f'{esc(tag)}</a>'
        for tag in game["tags_list"]
    )

    related_html = "".join(
        game_card_html(item) for item in related
    )

    faq_html = ""

    if faq:
        for item in faq:
            faq_html += f"""
            <div class="faq-item">
                <details>
                    <summary>{esc(item['name'])}</summary>
                    <p class="muted">
                        {esc(item['acceptedAnswer']['text'])}
                    </p>
                </details>
            </div>
            """

    elif not faq:
        faq_html = """
        <p class="muted">
            No frequently asked questions have been added yet.
        </p>
        """

    cards_html = f"""
<section class="section">
    <div class="container">
        <div class="eyebrow">PLAYABLE COUPLES CARD DECK</div>
        <h2>Discover Your Next Question</h2>
        <p class="muted">
            Take turns, reveal questions and enjoy a shared experience.
            Tap the card to flip it.
        </p>

        <div class="form-row">
            <div>
                <label for="partner1">Partner 1 Name</label>
                <input id="partner1" class="field"
                       maxlength="40" placeholder="Partner 1">
            </div>
            <div>
                <label for="partner2">Partner 2 Name</label>
                <input id="partner2" class="field"
                       maxlength="40" placeholder="Partner 2">
            </div>
        </div>

        <div class="deck">
            <div class="playing-card" id="playingCard">
                <div class="card-face">
                    <div>
                        <div class="eyebrow">COUPLES GAME</div>
                        <h3 id="cardFront">Tap to reveal your question</h3>
                        <p class="muted">Your next conversation starts here.</p>
                    </div>
                </div>
                <div class="card-face card-back">
                    <h3 id="cardBack"></h3>
                </div>
            </div>
        </div>

        <p id="cardCounter" class="muted" style="text-align:center"></p>

        <div class="controls" style="justify-content:center">
            <button class="btn" id="nextCard">Next Card</button>
            <button class="btn btn-secondary" id="shuffleDeck">
                Shuffle Deck
            </button>
            <button class="btn btn-secondary" id="copyCards">
                Copy All Cards
            </button>
        </div>

        <h3>Player Turn Tracker</h3>

        <div class="player-panel">
            <div class="player" id="player1">
                <strong>Player 1</strong>
                <span class="muted">Ready to play</span>
            </div>
            <div class="player" id="player2">
                <strong>Player 2</strong>
                <span class="muted">Ready to play</span>
            </div>
        </div>

        <div style="text-align:center">
            <p id="turnLabel" class="muted">Turn 0 · Player 1</p>
            <button class="btn" id="nextTurn">Switch Player Turn</button>
        </div>
    </div>
</section>
"""

    audio_html = """
<section class="section">
    <div class="container">
        <div class="audio-panel">
            <h2>Romantic Mood Ambience</h2>
            <p class="muted">
                Create a relaxing atmosphere using locally generated
                Web Audio API sounds. No external audio files required.
            </p>

            <button class="btn" id="audioButton">
                Play Ambience
            </button>

            <label for="soundSelect">Choose Sound</label>
            <select id="soundSelect" class="field">
                <option value="rain">Warm Rain</option>
                <option value="fire">Soft Fireplace</option>
                <option value="ambient">Deep Ambient Hum</option>
            </select>

            <label for="volumeSlider">
                Volume
            </label>
            <input type="range" id="volumeSlider"
                   min="0" max="100" value="30">
        </div>
    </div>
</section>
"""

    affiliate_html = f"""
<!-- AD_SLOT_MID_CONTENT -->
<section class="section">
    <div class="container">
        <div class="affiliate">
            <div class="eyebrow">FEATURED EXPERIENCE</div>
            <h2>Make Your Date Night Memorable</h2>
            <p class="muted">
                Explore additional interactive couples experiences,
                entertainment and live shows.
            </p>
            <a class="btn" href="{esc(AFFILIATE_URL)}"
               rel="nofollow sponsored noopener">
                {esc(AFFILIATE_CTA_TEXT)}
            </a>
        </div>
    </div>
</section>
"""

    return (
        page_head(title, description, path, "article")
        + header()
        + f"""
<!-- AD_SLOT_POPUNDER -->
<!-- AD_SLOT_TOP_BANNER -->

<main class="container">
    <div class="breadcrumbs">
        <a href="/">Home</a> /
        <a href="{category_url}">{esc(game['category'])}</a> /
        {esc(game['title'])}
    </div>

    <section class="section">
        <div class="eyebrow">{esc(game['category'])}</div>
        <h1>{esc(game['title'])}</h1>
        <p class="muted">{esc(description)}</p>

        <div class="pills">
            <a class="pill" href="{category_url}">
                {esc(game['category'])}
            </a>
            <a class="pill" href="{topic_url}">
                {esc(game['subcategory'])}
            </a>
            {tags_html}
        </div>

        <p class="muted">
            Published: {esc(game['upload_date'])}
            · {len(game['cards_list'])} playable questions
        </p>
    </section>
</main>

{cards_html}
{audio_html}
{affiliate_html}

<!-- AD_SLOT_STICKY_FOOTER -->

<section class="section">
    <div class="container">
        <h2>About This Couples Game</h2>
        <p class="muted">{esc(description)}</p>

        <h2>Frequently Asked Questions</h2>
        {faq_html}
    </div>
</section>

<section class="section">
    <div class="container">
        <h2>Related Couples Games</h2>
        <div class="grid">{related_html}</div>
    </div>
</section>

"""
        + footer()
        + age_modal()
        + f'<script type="application/ld+json">{json_script(schema)}</script>'
        + game_javascript(game)
        + "\n</body></html>"
    )


# ---------------------------------------------------------
# HOMEPAGE
# ---------------------------------------------------------

def render_home(games, categories, subcategories, tags):

    newest = sorted(
        games,
        key=date_sort_key,
        reverse=True
    )[:LATEST_LIMIT]

    category_html = ""

    # One card per unique category, with true total count.
    for category_slug, items in sorted(
        categories.items(),
        key=lambda x: (-len(x[1]), x[0])
    ):
        category_name = items[0]["category"]

        category_html += f"""
        <a class="card game-card"
           href="/category/{category_slug}/page-1.html">
            <h3>{esc(category_name)}</h3>
            <p>{format_count(len(items), "game")}</p>
            <span class="pill">Explore Category →</span>
        </a>
        """

    subcategory_html = ""

    for sub_slug, items in sorted(
        subcategories.items(),
        key=lambda x: (-len(x[1]), x[0])
    ):
        sub_name = items[0]["subcategory"]

        subcategory_html += f"""
        <a class="pill" href="/topic/{sub_slug}.html">
            {esc(sub_name)} ({len(items)})
        </a>
        """

    tag_counts = Counter(
        slugify(tag)
        for game in games
        for tag in game["tags_list"]
    )

    tag_names = {}

    for game in games:
        for tag in game["tags_list"]:
            tag_names.setdefault(slugify(tag), tag)

    popular_tags = sorted(
        tag_counts.items(),
        key=lambda x: (-x[1], x[0])
    )[:30]

    tag_html = "".join(
        f'<a class="pill" href="/tag/{slug}.html">'
        f'{esc(tag_names[slug])} ({count})</a>'
        for slug, count in popular_tags
    )

    latest_html = "".join(
        game_card_html(game)
        for game in newest
    )

    schema = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_NAME,
        "url": BASE_URL,
        "description": NICHE_TOPIC
    }

    return (
        page_head(
            f"{SITE_NAME} | Interactive Date Night Questions & Couples Games",
            NICHE_TOPIC,
            "index.html"
        )
        + header()
        + """
<!-- AD_SLOT_POPUNDER -->
<!-- AD_SLOT_TOP_BANNER -->

<main>
    <section class="hero">
        <div class="container">
            <div class="eyebrow">YOUR NEXT DATE NIGHT STARTS HERE</div>
            <h1>
                Discover <span class="gradient">
                Interactive Couples Games</span>
            </h1>
            <p class="muted">
                Explore date night questions, truth or dare,
                conversation starters and playful card decks
                designed to bring couples closer.
            </p>

            <div class="search-wrap">
                <input type="search" id="gameSearch"
                    class="search"
                    placeholder="Search games, topics, tags and keywords..."
                    aria-label="Search couples games">
                <p class="muted" id="searchCount"></p>
            </div>
        </div>
    </section>

    <section class="section" id="categories">
        <div class="container">
            <div class="section-heading">
                <h2>Browse Game Categories</h2>
                <p class="muted">
                    Explore every unique category in our collection.
                </p>
            </div>
            <div class="grid">
"""
        + category_html
        + """
            </div>
        </div>
    </section>

    <section class="section">
        <div class="container">
            <h2>Browse Subcategories</h2>
            <div class="pills">
"""
        + subcategory_html
        + """
            </div>
        </div>
    </section>

    <section class="section">
        <div class="container">
            <h2>Popular Game Tags</h2>
            <div class="pills">
"""
        + tag_html
        + """
            </div>
        </div>
    </section>

    <!-- AD_SLOT_MID_CONTENT -->

    <section class="section" id="latest">
        <div class="container">
            <h2>30 Newest Couples Games</h2>
            <div class="grid" id="gamesGrid">
"""
        + latest_html
        + """
            </div>
            <div class="empty-state" id="emptyState">
                No matching games found.
            </div>
        </div>
    </section>
</main>

<!-- AD_SLOT_STICKY_FOOTER -->
"""
        + footer()
        + age_modal()
        + f"""
<script type="application/ld+json">
{json_script(schema)}
</script>

<script>
(function() {{
    const search = document.getElementById("gameSearch");
    const cards = Array.from(
        document.querySelectorAll("#gamesGrid .game-card")
    );

    const count = document.getElementById("searchCount");
    const empty = document.getElementById("emptyState");

    function filter() {{
        const query = search.value.trim().toLowerCase();
        let visible = 0;

        cards.forEach(function(card) {{
            const text = card.dataset.search || "";
            const match = !query || text.includes(query);

            card.style.display = match ? "" : "none";

            if (match) visible++;
        }});

        count.textContent = query
            ? visible + " matching games"
            : "Explore " + cards.length + " newest games";

        empty.style.display = visible ? "none" : "block";
    }}

    search.addEventListener("input", filter);
    filter();
}})();
</script>

</body></html>
"""
    )


# ---------------------------------------------------------
# CATEGORY HUBS
# ---------------------------------------------------------

def render_category_page(category_slug, items, page_number, total_pages):

    category_name = items[0]["category"]

    start = (page_number - 1) * PER_PAGE
    page_items = items[start:start + PER_PAGE]

    path = (
        f"category/{category_slug}/page-{page_number}.html"
    )

    description = (
        f"Explore {category_name}: discover interactive couples "
        f"games, date night questions and conversation starters."
    )

    cards = "".join(
        game_card_html(game)
        for game in page_items
    )

    pagination = ""

    if page_number > 1:
        previous = page_number - 1
        pagination += (
            f'<a class="btn btn-secondary" '
            f'href="page-{previous}.html">← Previous</a>'
        )

    for number in range(1, total_pages + 1):
        pagination += (
            f'<a class="pill" href="page-{number}.html">'
            f'{number}</a>'
        )

    if page_number < total_pages:
        next_page = page_number + 1
        pagination += (
            f'<a class="btn" href="page-{next_page}.html">'
            f'Next →</a>'
        )

    prev_link = ""

    if page_number > 1:
        prev_link = (
            f'<link rel="prev" href="{esc(canonical(
                f"category/{category_slug}/page-{page_number - 1}.html"
            ))}">'
        )

    next_link = ""

    if page_number < total_pages:
        next_link = (
            f'<link rel="next" href="{esc(canonical(
                f"category/{category_slug}/page-{page_number + 1}.html"
            ))}">'
        )

    return (
        page_head(
            f"{category_name} Couples Games – Page {page_number}",
            description,
            path
        )
        .replace("</head>", prev_link + next_link + "\n</head>")
        + header()
        + f"""
<main class="container">
    <div class="breadcrumbs">
        <a href="/">Home</a> / {esc(category_name)}
    </div>

    <section class="section">
        <div class="eyebrow">GAME CATEGORY</div>
        <h1>{esc(category_name)}</h1>
        <p class="muted">{esc(description)}</p>
        <p class="muted">
            {format_count(len(items), "game")}
            · Page {page_number} of {total_pages}
        </p>
    </section>

    <section class="section">
        <div class="grid">{cards}</div>
        <div class="pagination">{pagination}</div>
    </section>
</main>
"""
        + footer()
        + age_modal()
        + "\n</body></html>"
    )


# ---------------------------------------------------------
# TOPIC AND TAG HUBS
# ---------------------------------------------------------

def render_collection_page(title, description, path, items):

    cards = "".join(
        game_card_html(game)
        for game in items
    )

    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title,
        "description": description,
        "url": canonical(path)
    }

    return (
        page_head(title, description, path)
        + header()
        + f"""
<main class="container">
    <div class="breadcrumbs">
        <a href="/">Home</a> / {esc(title)}
    </div>

    <section class="section">
        <div class="eyebrow">EXPLORE THE COLLECTION</div>
        <h1>{esc(title)}</h1>
        <p class="muted">{esc(description)}</p>
        <p class="muted">
            {format_count(len(items), "game")}
        </p>
    </section>

    <section class="section">
        <div class="grid">{cards}</div>
    </section>
</main>
"""
        + footer()
        + age_modal()
        + f'<script type="application/ld+json">{json_script(schema)}</script>'
        + "\n</body></html>"
    )


# ---------------------------------------------------------
# LEGAL PAGES
# ---------------------------------------------------------

def render_legal_pages():

    dmca = f"""
{page_head(
    "DMCA Copyright Policy | " + SITE_NAME,
    "Copyright and DMCA takedown policy and contact information.",
    "dmca.html"
)}
{header()}

<main class="container section">
    <div class="eyebrow">LEGAL INFORMATION</div>
    <h1>DMCA Copyright Policy</h1>

    <p class="muted">
        {esc(SITE_NAME)} respects intellectual property rights.
        We respond to properly submitted copyright infringement
        notifications in accordance with applicable law.
    </p>

    <h2>Submitting a Copyright Notice</h2>
    <p>
        Please include your contact information, identification
        of the copyrighted work, the URL of the allegedly
        infringing material, a good-faith statement, and a
        statement of accuracy and authorization.
    </p>

    <h2>Contact</h2>
    <p>
        Copyright requests:
        <a href="mailto:{CONTACT_EMAIL}">
            {CONTACT_EMAIL}
        </a>
    </p>

    <p class="muted">
        This policy does not waive any rights or defenses
        available under applicable law.
    </p>
</main>

{footer()}
{age_modal()}
</body></html>
"""

    page2257 = f"""
{page_head(
    "18 U.S.C. 2257 Compliance Statement | " + SITE_NAME,
    "Recordkeeping and content compliance information.",
    "2257.html"
)}
{header()}

<main class="container section">
    <div class="eyebrow">LEGAL INFORMATION</div>
    <h1>18 U.S.C. § 2257 Statement</h1>

    <p>
        {esc(SITE_NAME)} is an interactive couples games and
        conversation website. The site primarily publishes
        textual questions, games, descriptions and
        user-interaction experiences.
    </p>

    <p>
        No sexually explicit visual depictions are intentionally
        published as part of the generated website.
    </p>

    <p>
        Where applicable, content and recordkeeping obligations
        are handled in accordance with relevant laws and
        regulations. This statement is informational and
        does not constitute a legal determination of exemption.
    </p>

    <h2>Contact</h2>
    <p>
        <a href="mailto:{CONTACT_EMAIL}">
            {CONTACT_EMAIL}
        </a>
    </p>
</main>

{footer()}
{age_modal()}
</body></html>
"""

    write_file(
        os.path.join(DIST, "dmca.html"),
        dmca
    )

    write_file(
        os.path.join(DIST, "2257.html"),
        page2257
    )


# ---------------------------------------------------------
# XML SITEMAP STYLESHEET
# ---------------------------------------------------------

def sitemap_stylesheet():
    return r'''<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:s="http://www.sitemaps.org/schemas/sitemap/0.9">

<xsl:output method="html" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>XML Sitemap</title>
<style>
body {
    background:#0b0910;
    color:#f8f4fc;
    font-family:system-ui,sans-serif;
    padding:30px;
}
main {
    max-width:1000px;
    margin:auto;
}
h1 {color:#ec4899}
table {
    width:100%;
    border-collapse:collapse;
    background:#161221;
    border-radius:12px;
}
td,th {
    padding:13px;
    border-bottom:1px solid #30263d;
    text-align:left;
}
a {color:#c4b5fd}
.muted {color:#aaa0b5}
</style>
</head>
<body>
<main>
<h1>Website XML Sitemap</h1>
<p class="muted">
    Sitemap URLs indexed for discovery and crawling.
</p>
<table>
<tr>
<th>Location</th>
<th>Last Modified</th>
</tr>
<xsl:for-each select="s:urlset/s:url">
<tr>
<td>
<a href="{s:loc}">
<xsl:value-of select="s:loc"/>
</a>
</td>
<td><xsl:value-of select="s:lastmod"/></td>
</tr>
</xsl:for-each>
</table>
</main>
</body>
</html>
</xsl:template>
</xsl:stylesheet>'''


# ---------------------------------------------------------
# XML SITEMAPS
# ---------------------------------------------------------

def render_sitemaps(games, categories, subcategories, tags):

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    urls = []

    def add_url(path, priority="0.7", frequency="weekly"):
        urls.append({
            "loc": canonical(path),
            "priority": priority,
            "frequency": frequency,
            "lastmod": today,
        })

    add_url("index.html", "1.0", "daily")

    for game in games:
        add_url(
            f"game/{game['slug']}.html",
            "0.8",
            "monthly"
        )

    for category_slug, items in categories.items():

        pages = max(
            1,
            math.ceil(len(items) / PER_PAGE)
        )

        for page in range(1, pages + 1):
            add_url(
                f"category/{category_slug}/page-{page}.html",
                "0.8",
                "weekly"
            )

    for sub_slug in subcategories:
        add_url(
            f"topic/{sub_slug}.html",
            "0.7",
            "weekly"
        )

    for tag_slug in tags:
        add_url(
            f"tag/{tag_slug}.html",
            "0.6",
            "weekly"
        )

    add_url("dmca.html", "0.3", "yearly")
    add_url("2257.html", "0.3", "yearly")

    def sitemap_entry(item):
        return f"""
    <url>
        <loc>{esc(item['loc'])}</loc>
        <lastmod>{item['lastmod']}</lastmod>
        <changefreq>{item['frequency']}</changefreq>
        <priority>{item['priority']}</priority>
    </url>"""

    # Keep individual sitemap files below the standard URL limit.
    chunks = [
        urls[i:i + 45000]
        for i in range(0, len(urls), 45000)
    ]

    if not chunks:
        chunks = [[]]

    for index, chunk in enumerate(chunks, start=1):

        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<?xml-stylesheet type="text/xsl" href="/sitemap.xsl"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "".join(sitemap_entry(item) for item in chunk)
            + "\n</urlset>"
        )

        filename = f"sitemap-{index}.xml"

        write_file(
            os.path.join(DIST, filename),
            xml
        )

    sitemap_index = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<?xml-stylesheet type="text/xsl" href="/sitemap.xsl"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    )

    for index in range(1, len(chunks) + 1):
        sitemap_index += f"""
    <sitemap>
        <loc>{esc(canonical(f'sitemap-{index}.xml'))}</loc>
        <lastmod>{today}</lastmod>
    </sitemap>
"""

    sitemap_index += "\n</sitemapindex>"

    write_file(
        os.path.join(DIST, "sitemap.xml"),
        sitemap_index
    )

    write_file(
        os.path.join(DIST, "sitemap.xsl"),
        sitemap_stylesheet()
    )

    robots = f"""User-agent: *
Allow: /

Sitemap: {canonical('sitemap.xml')}
"""

    write_file(
        os.path.join(DIST, "robots.txt"),
        robots
    )


# ---------------------------------------------------------
# BUILD DIRECTORIES
# ---------------------------------------------------------

def prepare_output():

    if os.path.exists(DIST):
        shutil.rmtree(DIST)

    directories = [
        "game",
        "category",
        "topic",
        "tag",
    ]

    os.makedirs(DIST, exist_ok=True)

    for directory in directories:
        os.makedirs(
            os.path.join(DIST, directory),
            exist_ok=True
        )


# ---------------------------------------------------------
# MAIN BUILD
# ---------------------------------------------------------

def build():

    print("=" * 65)
    print(f"Building {SITE_NAME}")
    print("=" * 65)

    games = load_games()

    print(f"Loaded {len(games)} games.")

    prepare_output()

    categories, subcategories, tags = build_indexes(games)

    # Homepage
    write_file(
        os.path.join(DIST, "index.html"),
        render_home(
            games,
            categories,
            subcategories,
            tags
        )
    )

    # Individual game detail pages
    for index, game in enumerate(games, start=1):

        page = render_game_page(game, games)

        write_file(
            os.path.join(
                DIST,
                "game",
                game["slug"] + ".html"
            ),
            page
        )

        if index % 100 == 0:
            print(f"Generated {index} game pages.")

    # Category hubs
    for category_slug, items in categories.items():

        total_pages = max(
            1,
            math.ceil(len(items) / PER_PAGE)
        )

        category_directory = os.path.join(
            DIST,
            "category",
            category_slug
        )

        os.makedirs(
            category_directory,
            exist_ok=True
        )

        for page_number in range(1, total_pages + 1):

            page = render_category_page(
                category_slug,
                items,
                page_number,
                total_pages
            )

            write_file(
                os.path.join(
                    category_directory,
                    f"page-{page_number}.html"
                ),
                page
            )

    # Dedicated subcategory hubs
    for sub_slug, items in subcategories.items():

        sub_name = items[0]["subcategory"]

        description = (
            f"Explore {sub_name} with interactive couples "
            "questions, date night games and conversation starters."
        )

        page = render_collection_page(
            f"{sub_name} Couples Games",
            description,
            f"topic/{sub_slug}.html",
            items
        )

        write_file(
            os.path.join(
                DIST,
                "topic",
                sub_slug + ".html"
            ),
            page
        )

    # Dedicated tag hubs
    for tag_slug, items in tags.items():

        tag_name = next(
            (
                tag
                for game in games
                for tag in game["tags_list"]
                if slugify(tag) == tag_slug
            ),
            tag_slug.replace("-", " ").title()
        )

        description = (
            f"Discover couples games tagged {tag_name}, "
            "including interactive date night questions "
            "and conversation activities."
        )

        page = render_collection_page(
            f"{tag_name} Couples Games",
            description,
            f"tag/{tag_slug}.html",
            items
        )

        write_file(
            os.path.join(
                DIST,
                "tag",
                tag_slug + ".html"
            ),
            page
        )

    # Legal pages
    render_legal_pages()

    # XML sitemaps and robots
    render_sitemaps(
        games,
        categories,
        subcategories,
        tags
    )

    # Build statistics
    detail_count = len(games)

    category_page_count = sum(
        max(1, math.ceil(len(items) / PER_PAGE))
        for items in categories.values()
    )

    total_pages = (
        1
        + detail_count
        + category_page_count
        + len(subcategories)
        + len(tags)
        + 2
    )

    print()
    print("=" * 65)
    print("BUILD COMPLETED SUCCESSFULLY")
    print("=" * 65)
    print(f"Website:          {BASE_URL}")
    print(f"Games:             {detail_count}")
    print(f"Categories:        {len(categories)}")
    print(f"Subcategories:     {len(subcategories)}")
    print(f"Unique tags:       {len(tags)}")
    print(f"Category pages:    {category_page_count}")
    print(f"Total HTML pages:   {total_pages}")
    print(f"Output directory:   {DIST}")
    print("=" * 65)


if __name__ == "__main__":
    try:
        build()
    except Exception as error:
        print(f"\nBUILD ERROR: {error}")
        raise
