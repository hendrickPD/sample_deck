---
name: seed-deck
version: 0.3.0
description: |
  Edit a Slidev seed-round pitch deck following the YC recommended format.
  Use when asked to update slide content, add slides, fix formatting,
  change stats, scaffold a new deck, or deploy. Proactively suggest
  when the user mentions "deck", "slides", "presentation", "pitch", or "Slidev".
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Grep
  - Glob
  - Agent
  - AskUserQuestion
---



# Edit Deck

You are editing a Slidev-based seed-round pitch deck. The canonical structure follows the YC seed deck template by Aaron Harris ("How to Build Your Seed Round Pitch Deck").

> "Focus on narrative. The rest is commentary." — Aaron Harris

---

## First Run: Setup + Scaffold

When the skill is invoked for the first time on a project (no `slides.md` exists, or user asks to "set up" / "start a new deck"), run this flow:

### Step 1: Project setup

Check what already exists and set up what's missing:

```bash
# Check for existing Slidev project
ls package.json slides.md style.css 2>/dev/null
```

**If no Slidev project exists**, scaffold one:
```bash
npm init -y
npm install @slidev/cli @slidev/theme-default
```

Add scripts to `package.json`:
```json
{
  "scripts": {
    "dev": "slidev",
    "slides:build": "slidev build",
    "slides:export": "slidev export"
  }
}
```

### Step 1b: Download template assets

The YC template images are stored in the skill's GitHub repo. Download them into `public/`:

```bash
mkdir -p public
curl -sL https://raw.githubusercontent.com/hendrickPD/deck_skill/main/peppa.jpg -o public/peppa.jpg
curl -sL https://raw.githubusercontent.com/hendrickPD/deck_skill/main/kermit.jpg -o public/kermit.jpg
curl -sL https://raw.githubusercontent.com/hendrickPD/deck_skill/main/robot.jpg -o public/robot.jpg
```

These are assets extracted from the original YC seed deck PPTX:
- Team photos: Peppa Pig (CTO), Kermit (CEO), Cyberman (VP eng) — replaced when user provides real headshots.
- Traction charts are generated as animated CSS bar charts (no PNG needed — see template below).

### Step 1c: Create global-top.vue

This file provides dot rail navigation, reveal animation triggering, and slide view analytics. Slidev auto-loads it on every slide.

```vue
<template>
  <!-- Dot Rail Navigation -->
  <nav v-if="!isPrintMode" class="dot-nav">
    <button
      v-for="i in total"
      :key="i"
      :class="['dot-pip', { active: currentSlideNo === i }]"
      :title="'Slide ' + i"
      @click="go(i)"
    />
  </nav>
</template>

<script setup>
import { watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useNav } from '@slidev/client'

const { currentSlideNo, total, go, isPrintMode } = useNav()

// ── Reveal Animation Trigger ──
function triggerReveals(slideNo) {
  nextTick(() => {
    document.querySelectorAll('.bar-fill').forEach(bar => {
      bar.style.height = '0'
    })
    document.querySelectorAll('.reveal.is-visible').forEach(el => {
      el.classList.remove('is-visible')
    })
    nextTick(() => {
      const activeWrapper = document.querySelector('.slidev-page-' + slideNo)
      if (activeWrapper) {
        activeWrapper.querySelectorAll('.reveal').forEach(el => el.classList.add('is-visible'))
        activeWrapper.querySelectorAll('.bar-chart.is-visible .bar-fill').forEach((bar, i) => {
          setTimeout(() => { bar.style.height = bar.dataset.h }, i * 100)
        })
      }
    })
  })
}

watch(currentSlideNo, (n) => { triggerReveals(n) })
onMounted(() => { setTimeout(() => triggerReveals(currentSlideNo.value), 300) })

// ── Slide View Analytics ──
const analytics = {}
let enterTime = Date.now()
let currentSlide = 1

function recordSlideLeave() {
  const duration = Date.now() - enterTime
  if (!analytics[currentSlide]) analytics[currentSlide] = 0
  analytics[currentSlide] += duration
}

function recordSlideEnter(slideNo) {
  currentSlide = slideNo
  enterTime = Date.now()
}

watch(currentSlideNo, (newSlide) => {
  recordSlideLeave()
  recordSlideEnter(newSlide)
})

function sendAnalytics() {
  recordSlideLeave()
  const payload = JSON.stringify({ slides: analytics, total_slides: total.value, timestamp: new Date().toISOString() })
  try {
    if (navigator.sendBeacon) {
      navigator.sendBeacon('/api/track', new Blob([payload], { type: 'application/json' }))
    }
  } catch (e) {}
}

// ── Orientation lock on fullscreen (desktop / Android) ──
function onFullscreenChange() {
  if (document.fullscreenElement && screen.orientation?.lock) {
    screen.orientation.lock('landscape').catch(() => {})
  }
}

onMounted(() => {
  window.addEventListener('beforeunload', sendAnalytics)
  document.addEventListener('fullscreenchange', onFullscreenChange)
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', sendAnalytics)
  document.removeEventListener('fullscreenchange', onFullscreenChange)
})
</script>
```

### Step 2: Vercel + GitHub setup

**Check for existing deploy config:**
```bash
ls deploy.sh vercel.json .vercel/project.json 2>/dev/null
```

**If no deploy pipeline exists**, set one up:

1. **Git repo** — initialize if needed:
   ```bash
   git init
   echo "node_modules/\ndist/\n.vercel/" > .gitignore
   ```

2. **Vercel project** — link or create:
   ```bash
   npx vercel link
   ```
   This will prompt the user to authenticate and select/create a project.

3. **Create `deploy.sh`:**
   ```bash
   #!/usr/bin/env bash
   set -e
   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
   cd "$SCRIPT_DIR"

   echo "▶ Building slides..."
   npm run slides:build

   echo "▶ Deploying to Vercel..."
   npx vercel deploy --prod --yes

   echo "✓ Done."
   ```
   Then: `chmod +x deploy.sh`

4. **GitHub remote** — if not set:
   ```bash
   git remote get-url origin 2>/dev/null || echo "No remote"
   ```
   If no remote, ask the user for their GitHub repo URL and add it:
   ```bash
   git remote add origin <URL>
   ```

**If deploy config already exists**, read `deploy.sh`, `CLAUDE.md`, and `vercel.json` to learn the existing pipeline. Report what you found.

### Step 3: Generate template deck

Generate a `slides.md` following the YC 10-slide structure. Use placeholder content that clearly marks what the user needs to fill in.

**Generate `style.css`** with a clean design system (or read the existing one).

**Generate the template `slides.md`** — see "Template Deck Content" section below.

### Step 4: Ask the user for their data

After generating the template, ask the user to provide:

1. **Company name** and one-line description
2. **Problem** — what pain point do you solve?
3. **Solution** — what does your product do?
4. **Traction** — key metrics (MRR/ARR, users, growth rate, retention). Any chart data?
5. **Insight** — what makes this work? What's your unfair advantage?
6. **Business model** — how do you make money? Pricing?
7. **Market** — how big is the opportunity?
8. **Team** — founders: names, roles, backgrounds. Headshot files?
9. **The Ask** — how much are you raising? Use of funds? Target milestones?

Collect whatever the user provides and fill in the template. Leave `[PLACEHOLDER]` markers for anything not yet provided.

### Step 5: Build + verify

```bash
npx slidev build
```

If the build succeeds, report success and offer to:
- Start dev server: `npx slidev`
- Deploy: `./deploy.sh`
- Continue editing specific slides

---

## Template Deck Content

When generating a new deck, create `slides.md` that is a **pixel-faithful Slidev reproduction** of the YC seed deck template by Aaron Harris (Google Slides source: `17nFIwCyf2Kz-Ao5HGnmvNZ74L8eSKA2C2Qdaoe-47OM`).

**Visual rules — match the Google Slides exactly:**
- White background on every slide. No dark/cover slides.
- Black text (`#000`). No grey secondary text, no accent colors.
- Titles use a large serif font (Google Fonts "Playfair Display" approximates the original). Centered horizontally, positioned in the upper portion of the slide.
- Body text uses bullet points (`●` disc style) in a regular sans-serif, left-aligned with generous left margin, vertically centered in the remaining space.
- Page number in the bottom-right corner of every slide except the title slide (slide 1). Rendered as a small grey number.
- No eyebrow labels, no cards, no colored backgrounds, no borders, no CSS variable theming. The design is intentionally spartan.
- Traction slides (4 & 5) use a 2-column layout: a line chart on the left (~70% width) and a short dash-list of key stats on the right (~30% width). The chart is an SVG hockey-stick curve.
- Team slide uses a 3-column grid of placeholder images with role descriptions centered below each.

The content below uses the **exact placeholder text** from the YC template. When the user provides their real data, replace these placeholders — but the scaffolded deck should ship with this content verbatim so it matches the original.

```markdown
---
theme: default
title: 'Seed deck template, AI'
author: 'Seed deck template, AI'
fonts:
  sans: 'Inter'
  serif: 'Playfair Display'
  mono: 'JetBrains Mono'
  provider: google
defaults:
  layout: default
transition: fade
layout: default
head:
  - - meta
    - name: apple-mobile-web-app-capable
      content: 'yes'
  - - meta
    - name: apple-mobile-web-app-status-bar-style
      content: black-translucent
  - - meta
    - name: viewport
      content: 'width=device-width, initial-scale=1, viewport-fit=cover'
---

<!-- Slide 1: Title -->
<div style="height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;">
<h1 style="font-family:'Playfair Display',serif;font-size:3.2rem;font-weight:700;color:#000;margin:0 0 1.5rem;">Seed deck AI, inc</h1>
<div style="display:flex;align-items:center;gap:0.5rem;max-width:650px;">
<p class="subtitle" style="font-size:0.85rem;color:#666;font-weight:400;line-height:1.6;margin:0;">Paste this into Claude Code to start: &#x201C;download the seed-deck skill from https://raw.githubusercontent.com/hendrickPD/deck_skill/main/SKILL.md and install it to .claude/skills/seed-deck/SKILL.md&#x201D;</p>
<button @click="copyInstall" style="flex-shrink:0;padding:0.35rem 0.7rem;font-size:0.75rem;border:1px solid #ccc;border-radius:6px;background:#f5f5f5;color:#333;cursor:pointer;white-space:nowrap;transition:all 0.2s;" :style="copied ? {background:'#000',color:'#fff',borderColor:'#000'} : {}">{{ copied ? 'Copied!' : 'Copy' }}</button>
</div>
</div>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useNav } from '@slidev/client'
const copied = ref(false)

// Keep control bar visible on slide 1 only
const { currentSlideNo } = useNav()
let navEl = null
function syncNav(n) {
  if (!navEl) navEl = document.querySelector('#slide-container div[class*="opacity-0"][class*="bottom-0"]')
  if (navEl) navEl.style.opacity = n === 1 ? '1' : ''
}
onMounted(() => syncNav(currentSlideNo.value))
watch(currentSlideNo, syncNav)
onUnmounted(() => { if (navEl) navEl.style.opacity = '' })
function copyInstall() {
  const text = 'download the seed-deck skill from https://raw.githubusercontent.com/hendrickPD/deck_skill/main/SKILL.md and install it to .claude/skills/seed-deck/SKILL.md'
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => flash()).catch(() => fallback(text))
  } else {
    fallback(text)
  }
}
function fallback(text) {
  const ta = document.createElement('textarea')
  ta.value = text
  ta.style.position = 'fixed'
  ta.style.opacity = '0'
  document.body.appendChild(ta)
  ta.select()
  document.execCommand('copy')
  document.body.removeChild(ta)
  flash()
}
function flash() {
  copied.value = true
  setTimeout(() => copied.value = false, 2000)
}
</script>

---
layout: default
---

<!-- Slide 2: Problem -->
<div style="padding:3rem 4rem;height:100%;display:flex;flex-direction:column;">
<h2 class="reveal" style="font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:700;color:#000;margin:0 0 1.5rem;">Traditional tools slow you down</h2>
<ul style="font-size:1.15rem;color:#000;line-height:2.2;list-style:disc;padding-left:2rem;">
  <li class="reveal reveal-delay-1">Figma and Google Slides can&#x2019;t be driven by AI &#x2014; every change is manual</li>
  <li class="reveal reveal-delay-2">Claude can write code, but GUI tools limit what it can iterate on</li>
  <li class="reveal reveal-delay-3">You should be refining your story, not dragging boxes around</li>
</ul>
<div style="margin-top:auto;text-align:right;font-size:0.75rem;color:#999;">2</div>
</div>

---
layout: default
---

<!-- Slide 3: Solution -->
<div style="padding:3rem 4rem;height:100%;display:flex;flex-direction:column;">
<h2 class="reveal" style="font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:700;color:#000;margin:0 0 1.5rem;">One command installs the fix</h2>
<ul style="font-size:1.15rem;color:#000;line-height:2.2;list-style:disc;padding-left:2rem;">
  <li class="reveal reveal-delay-1">A Claude Code skill that scaffolds a YC-format deck in seconds</li>
  <li class="reveal reveal-delay-2">Tell it your story &#x2014; it writes the slides, builds the charts</li>
  <li class="reveal reveal-delay-3">Export as PDF or deploy straight to Vercel &#x2014; your call</li>
  <li class="reveal reveal-delay-4">Say /seed-deck and you&#x2019;re live</li>
</ul>
<div style="margin-top:auto;text-align:right;font-size:0.75rem;color:#999;">3</div>
</div>

---
layout: default
---

<!-- Slide 4: Traction -->
<div style="padding:3rem 4rem;height:100%;display:flex;flex-direction:column;">
<h2 class="reveal" style="font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:700;color:#000;margin:0 0 1rem;">[Traction headline]</h2>
<div style="display:grid;grid-template-columns:2.2fr 1fr;gap:2rem;flex:1;align-items:center;">
  <div class="bar-chart reveal reveal-delay-1">
    <div class="bar"><div class="bar-value">[v1]</div><div class="bar-fill" style="height:0" data-h="[h1]%"></div><div class="bar-label">[l1]</div></div>
    <div class="bar"><div class="bar-value">[v2]</div><div class="bar-fill" style="height:0" data-h="[h2]%"></div><div class="bar-label">[l2]</div></div>
    <div class="bar"><div class="bar-value">[v3]</div><div class="bar-fill" style="height:0" data-h="[h3]%"></div><div class="bar-label">[l3]</div></div>
    <div class="bar"><div class="bar-value">[v4]</div><div class="bar-fill" style="height:0" data-h="[h4]%"></div><div class="bar-label">[l4]</div></div>
    <div class="bar"><div class="bar-value">[v5]</div><div class="bar-fill" style="height:0" data-h="[h5]%"></div><div class="bar-label">[l5]</div></div>
    <div class="bar"><div class="bar-value">[v6]</div><div class="bar-fill" style="height:0" data-h="100%"></div><div class="bar-label">[l6]</div></div>
  </div>
  <div class="reveal reveal-delay-2" style="font-size:1rem;color:#000;line-height:2;">
    <div>-&nbsp;&nbsp;[Key stat 1]</div>
    <div>-&nbsp;&nbsp;[Key stat 2]</div>
  </div>
</div>
<div style="margin-top:auto;text-align:right;font-size:0.75rem;color:#999;">4</div>
</div>

---
layout: default
---

<!-- Slide 5: More Traction -->
<div style="padding:3rem 4rem;height:100%;display:flex;flex-direction:column;">
<h2 class="reveal" style="font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:700;color:#000;margin:0 0 1rem;">[Traction headline 2]</h2>
<div style="display:grid;grid-template-columns:2.2fr 1fr;gap:2rem;flex:1;align-items:center;">
  <div class="bar-chart reveal reveal-delay-1">
    <div class="bar"><div class="bar-value">[v1]</div><div class="bar-fill" style="height:0" data-h="[h1]%"></div><div class="bar-label">[l1]</div></div>
    <div class="bar"><div class="bar-value">[v2]</div><div class="bar-fill" style="height:0" data-h="[h2]%"></div><div class="bar-label">[l2]</div></div>
    <div class="bar"><div class="bar-value">[v3]</div><div class="bar-fill" style="height:0" data-h="[h3]%"></div><div class="bar-label">[l3]</div></div>
    <div class="bar"><div class="bar-value">[v4]</div><div class="bar-fill" style="height:0" data-h="[h4]%"></div><div class="bar-label">[l4]</div></div>
    <div class="bar"><div class="bar-value">[v5]</div><div class="bar-fill" style="height:0" data-h="[h5]%"></div><div class="bar-label">[l5]</div></div>
    <div class="bar"><div class="bar-value">[v6]</div><div class="bar-fill" style="height:0" data-h="100%"></div><div class="bar-label">[l6]</div></div>
  </div>
  <div class="reveal reveal-delay-2" style="font-size:1rem;color:#000;line-height:2;">
    <div>-&nbsp;&nbsp;[Key stat 1]</div>
    <div>-&nbsp;&nbsp;[Key stat 2]</div>
  </div>
</div>
<div style="margin-top:auto;text-align:right;font-size:0.75rem;color:#999;">5</div>
</div>

---
layout: default
---

<!-- Slide 6: Insight / Why It Works -->
<div style="padding:3rem 4rem;height:100%;display:flex;flex-direction:column;">
<h2 class="reveal" style="font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:700;color:#000;margin:0 0 1.5rem;">Skills are the new plugins</h2>
<ul style="font-size:1.15rem;color:#000;line-height:2.2;list-style:disc;padding-left:2rem;">
  <li class="reveal reveal-delay-1">Skills = domain expertise as reusable prompts</li>
  <li class="reveal reveal-delay-2">One file carries the full YC playbook</li>
  <li class="reveal reveal-delay-3">Updates on GitHub, improves everywhere instantly</li>
</ul>
<div style="margin-top:auto;text-align:right;font-size:0.75rem;color:#999;">6</div>
</div>

---
layout: default
---

<!-- Slide 7: Business Model -->
<div style="padding:3rem 4rem;height:100%;display:flex;flex-direction:column;">
<h2 class="reveal" style="font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:700;color:#000;margin:0 0 1.5rem;">How to install this skill right now</h2>
<ul style="font-size:1.15rem;color:#000;line-height:2.2;list-style:disc;padding-left:2rem;">
  <li class="reveal reveal-delay-1">mkdir -p .claude/skills/seed-deck</li>
  <li class="reveal reveal-delay-2">curl the SKILL.md from GitHub into that folder</li>
  <li class="reveal reveal-delay-3">Open Claude Code, type /seed-deck, watch it scaffold your deck</li>
  <li class="reveal reveal-delay-4">Give it your data &#x2014; it writes slides, builds, and deploys</li>
</ul>
<div style="margin-top:auto;text-align:right;font-size:0.75rem;color:#999;">7</div>
</div>

---
layout: default
---

<!-- Slide 8: Market / Future Growth -->
<div style="padding:3rem 4rem;height:100%;display:flex;flex-direction:column;">
<h2 class="reveal" style="font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:700;color:#000;margin:0 0 1.5rem;">Every founder needs a deck</h2>
<ul style="font-size:1.15rem;color:#000;line-height:2.2;list-style:disc;padding-left:2rem;">
  <li class="reveal reveal-delay-1">1,500+ YC companies per batch, 50,000+ startups raising seed rounds per year</li>
  <li class="reveal reveal-delay-2">AI-native founders already live in the terminal &#x2014; Claude Code is their IDE</li>
  <li class="reveal reveal-delay-3">Skills are the app store for AI workflows. Decks are just the beginning.</li>
</ul>
<div style="margin-top:auto;text-align:right;font-size:0.75rem;color:#999;">8</div>
</div>

---
layout: default
---

<!-- Slide 9: Team -->
<div style="padding:3rem 4rem;height:100%;display:flex;flex-direction:column;">
<h2 class="reveal" style="font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:700;color:currentColor;margin:0 0 1.5rem;text-align:center;">Team</h2>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:2rem;flex:1;align-items:center;">
  <div class="reveal reveal-delay-1" style="text-align:center;">
    <img src="/peppa.jpg" style="width:160px;height:200px;object-fit:cover;margin:0 auto 0.75rem;display:block;" />
    <div style="font-size:1rem;color:currentColor;line-height:1.5;">CTO who<br/>ships skills<br/>at 2am</div>
  </div>
  <div class="reveal reveal-delay-2" style="text-align:center;">
    <img src="/kermit.jpg" style="width:160px;height:200px;object-fit:cover;margin:0 auto 0.75rem;display:block;" />
    <div style="font-size:1rem;color:currentColor;line-height:1.5;">CEO who<br/>knows how<br/>to pitch</div>
  </div>
  <div class="reveal reveal-delay-3" style="text-align:center;">
    <img src="/robot.jpg" style="width:160px;height:200px;object-fit:cover;margin:0 auto 0.75rem;display:block;" />
    <div style="font-size:1rem;color:currentColor;line-height:1.5;">VP eng<br/>who literally<br/>never sleeps</div>
  </div>
</div>
<div style="margin-top:auto;text-align:right;font-size:0.75rem;color:#999;">9</div>
</div>

---
layout: default
---

<!-- Slide 10: The Ask -->
<div style="padding:3rem 4rem;height:100%;display:flex;flex-direction:column;">
<h2 class="reveal" style="font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:700;color:#000;margin:0 0 1.5rem;">What we need</h2>
<ul style="font-size:1.15rem;color:#000;line-height:2.2;list-style:disc;padding-left:2rem;">
  <li class="reveal reveal-delay-1">$1.5m to build the skill marketplace for AI-native founders</li>
  <li class="reveal reveal-delay-2">Hire 3 engineers, launch 10 vertical skills (decks, contracts, data rooms)</li>
  <li class="reveal reveal-delay-3">Series A ready in 12 months: 10k installs, $2M ARR</li>
  <li class="reveal reveal-delay-4">Try it yourself: /seed-deck</li>
  <li>Huge thank you to <a href="https://www.ycombinator.com/library/2u-how-to-build-your-seed-round-pitch-deck" target="_blank" style="color:#f60;">YC&#x2019;s How to Build Your Seed Round Pitch Deck</a></li>
  <li>Huge thank you to <a href="https://github.com/garrytan/gstack" target="_blank" style="color:#f60;">Garry Tan</a> and <a href="https://github.com/garrytan/gstack" target="_blank" style="color:#f60;">gstack</a></li>
</ul>
<div style="margin-top:auto;text-align:right;font-size:0.75rem;color:#999;">10</div>
</div>
```

After generating, tell the user: "I've scaffolded a 10-slide deck following the YC template with the AI skill-install motif. Every slide tells the story of installing and using this skill. What would you like to customize first?"

---

## YC Seed Deck Template (Aaron Harris)

Source: YC Startup Library. Original template: https://docs.google.com/presentation/d/17nFIwCyf2Kz-Ao5HGnmvNZ74L8eSKA2C2Qdaoe-47OM/edit

This is the canonical slide order. Every deck should follow this sequence unless the user explicitly deviates.

### Slide count rule

The title slide is the **only** section limited to exactly 1 slide. All other sections can be 1-3 slides, but aim for n=1 per section. "This is a seed deck, remember."

### Core slides

| #  | Slide | What to show | Aaron Harris guidance |
|----|-------|-------------|----------------------|
| 1  | **Title** | Company name + one-line description of what you do | "This is the only place in the deck where you can only have 1 slide." |
| 2  | **Problem** | Clearly state the problem. Bullet the real-world impact. | "Particulars of how this problem impacts real world people/businesses are valuable." |
| 3  | **Solution** | What you do about it. Concrete benefits. | "Explain what you do very clearly, in as few words as possible. Describe the concrete benefit(s) you provide." |
| 4  | **Traction** | Growth chart (up-and-to-the-right) + key stats next to it. | "Show off your traction (if you have it). Make the numbers clear and meaningful. It's unlikely your curve will be this smooth. That's ok." Add context next to the chart if you have great stats. |
| 5  | **More Traction** (optional) | Additional metrics, revenue chart, second proof point. | "Got more metrics? Awesome! Add them!" Revenue is ideal here. This slide is optional if slide 4 covers it. |
| 6  | **Insight / Why It Works** | What makes you special. Your unique insight. Why this works. | "Tell the investor what makes you so special, what makes this work, what your insights are. This might take more than one slide." |
| 7  | **Business Model** | How you make money. Pricing, revenue, unit economics. | "Business model is important. You probably don't know all the details yet, but you should know a lot of them. Lay it out. If you need more space to dig into something complicated, add slides." |
| 8  | **Market / Future Growth** | Market size, growth trajectory, why it gets bigger. | "What's the market here? Is it going to be big? Will you make it big? How much money are you going to make off this thing? Convince the investor that they're going to make lots of money with you." |
| 9  | **Team** | Founders: photos, names, roles, why suited to this problem. | "Team! So important at seed. Talk about what makes your team particularly well suited to the problem. This should be about founders. Nobody cares about your advisors." |
| 10 | **The Ask** | Amount raising, use of funds, milestones it unlocks. | "Tell the investor how much money you need, and what it gets you. If you can lay out where you'll be inside of a year, which should make you Series A ready, that's powerful." |

### Optional slides (add as needed for fund decks or specific contexts)

| Slide | When to include |
|-------|----------------|
| **Disclosures** | Required for regulated fundraises (fund decks, SEC compliance) |
| **Financials / Projections** | If you have revenue — 3-5yr outlook |
| **Testimonials** | Strong founder/customer quotes that reinforce traction |
| **Portfolio / Track Record** | For fund decks — past performance, notable exits |
| **Network / Access** | For fund decks — sourcing advantage, relationships |
| **Appendix** | Supplementary detail investors may request |

### YC formatting principles

- **~10 slides** for seed — tight and focused. Can extend to 15-20 with optional slides.
- **One idea per slide** — if a slide makes two points, split it
- **Intentionally simple design** — content > aesthetics. Clean, legible, no clutter.
- **Designed for async** — deck must stand alone without a presenter
- **Charts > text** — show traction visually. "Add context next to the chart."
- **Founders only on Team** — "Nobody cares about your advisors."
- **Series A ready** — the ask should show milestones that position you for the next round

### Auditing an existing deck against YC format

When asked to review or restructure a deck:
1. Read all of `slides.md` and build the slide map
2. Map each existing slide to the 10-slide YC structure above
3. Identify: missing slides, out-of-order slides, slides that combine multiple ideas
4. Report gaps and propose a reordering plan
5. Only restructure after user approval

---

## Slidev Architecture

| File | Purpose |
|------|---------|
| `slides.md` | All slide content — single markdown file, slides separated by `---` |
| `style.css` | Custom CSS — design system classes and CSS variables |
| `global-top.vue` | Persistent global component: dot rail nav, reveal animation trigger, slide view analytics |
| `global-bottom.vue` | Global bottom component |
| `components/` | Custom Vue components |
| `public/` | Static assets — images, logos. Referenced as `/filename.jpg` |
| `deploy.sh` | Build + deploy script |
| `CLAUDE.md` | Project context for Claude Code |

## Slide Location

`slides.md` is a single file. Slides are separated by `---` on its own line. The first `---` block is YAML frontmatter, not a slide separator.

**To find slide N:** Count `---` separators from the top. Each pair of `---` lines (with `layout:` between them) marks the start of a new slide.

**Build a slide map on first use:** Read the file and create a table mapping slide numbers to line numbers and section eyebrows. Line numbers drift as content changes — always verify before editing.

**IMPORTANT:** Always `Read` the target area before editing.

---

## Edit Patterns

### Updating a stat value
```html
<div class="stat" style="font-size:2.8rem;">42</div>
```

### Updating a stat label
```html
<div class="stat-label">Total Count</div>
```

### Updating a card
```html
<div class="card" style="padding:1.1rem 1.25rem;">
  <div class="stat" style="font-size:2.8rem;">$100M</div>
  <div class="stat-label">Total Revenue</div>
</div>
```

### Updating eyebrow / section label
```html
<div class="eyebrow">Section Name</div>
```

### Updating display heading
```html
<h2 class="display-heading" style="font-size:2.4rem;color:var(--heading-color);margin:0 0 0.25rem;">
  Your headline here.
</h2>
```

### Updating footnote / disclosure text
```html
<p style="font-size:0.28rem;color:#6B7280;line-height:1.4;margin-top:0.3rem;">
  Disclosure text here...
</p>
```

### Adding a new slide
Insert between two `---` blocks. Every slide needs:
1. Frontmatter: `layout: default` (or `cover` for dark slides)
2. Outer wrapper: `<div style="padding:2rem 3.5rem;height:100%;display:flex;flex-direction:column;justify-content:flex-start;">`
3. Section label / eyebrow
4. Display heading
5. Content area
6. Footer
7. Closing `</div>`

**Standard footer (light):**
```html
<div class="footer">
  <span><img src="/icon.png" alt="" style="height:14px;vertical-align:middle;opacity:0.5;" /></span>
  <span>Confidential</span>
</div>
```

**Standard footer (dark/cover):**
```html
<div class="footer-dark">
  <span>Location Info</span>
  <span>Confidential</span>
</div>
```

### Traction slide (the most important slide)
The traction slide should feature a prominent growth chart. Pattern:
```html
<div class="eyebrow">Traction</div>
<h2 class="display-heading">Headline emphasizing growth.</h2>

<!-- Growth chart: SVG or image -->
<div style="...">
  <svg viewBox="..." width="100%"><!-- up-and-to-the-right line/bar chart --></svg>
</div>

<!-- Key metrics row -->
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;">
  <div class="card">
    <div class="stat">$1.2M</div>
    <div class="stat-label">ARR</div>
  </div>
  <div class="card">
    <div class="stat">25%</div>
    <div class="stat-label">MoM Growth</div>
  </div>
  <div class="card">
    <div class="stat">500+</div>
    <div class="stat-label">Customers</div>
  </div>
</div>
```

### Competition slide (2x2 matrix pattern)
```html
<div class="eyebrow">Competition</div>
<h2 class="display-heading">Where we sit.</h2>

<div style="display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:0;width:80%;aspect-ratio:1;border:1px solid var(--border);border-radius:8px;overflow:hidden;">
  <div style="padding:1rem;border-right:1px solid var(--border);border-bottom:1px solid var(--border);">
    <div style="font-size:0.7rem;color:var(--text-secondary);">Quadrant label</div>
    <div style="font-weight:600;">Competitor A</div>
  </div>
  <div style="padding:1rem;border-bottom:1px solid var(--border);background:var(--highlight-bg);">
    <div style="font-size:0.7rem;color:var(--accent);">Your quadrant</div>
    <div style="font-weight:700;color:var(--accent);">Your Company</div>
  </div>
  <!-- bottom two quadrants -->
</div>
<!-- Axis labels positioned outside the grid -->
```

### Team slide (photo grid pattern)
```html
<div class="eyebrow">Team</div>
<h2 class="display-heading">The team.</h2>

<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1.5rem;">
  <div style="text-align:center;">
    <img src="/person.jpg" style="width:64px;height:64px;border-radius:50%;object-fit:cover;" />
    <div style="font-weight:600;font-size:0.85rem;margin-top:0.5rem;">Name</div>
    <div style="font-size:0.7rem;color:var(--text-secondary);">Role</div>
    <div style="font-size:0.65rem;color:var(--text-secondary);margin-top:0.2rem;">Background · School</div>
  </div>
  <!-- more team members -->
</div>
```

### The Ask slide
```html
<div class="eyebrow">The Ask</div>
<h2 class="display-heading">Raising $X to reach Y.</h2>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:2rem;">
  <!-- Left: terms table -->
  <div>
    <div style="display:flex;justify-content:space-between;padding:0.5rem 0;border-bottom:1px solid var(--border);">
      <span style="font-size:0.7rem;color:var(--text-secondary);text-transform:uppercase;">Raising</span>
      <span style="font-weight:700;">$X</span>
    </div>
    <div style="display:flex;justify-content:space-between;padding:0.5rem 0;border-bottom:1px solid var(--border);">
      <span style="font-size:0.7rem;color:var(--text-secondary);text-transform:uppercase;">Instrument</span>
      <span style="font-weight:600;">SAFE / Priced</span>
    </div>
    <!-- more rows -->
  </div>

  <!-- Right: use of funds or milestone card -->
  <div class="card" style="padding:1.25rem;">
    <div style="font-size:0.7rem;text-transform:uppercase;color:var(--text-secondary);margin-bottom:0.5rem;">Use of Funds</div>
    <ul style="font-size:0.8rem;line-height:1.8;padding-left:1rem;">
      <li>Engineering — hire X</li>
      <li>Go-to-market — launch Y</li>
      <li>Reach Z milestone</li>
    </ul>
  </div>
</div>
```

### Person card
```html
<div class="card" style="display:flex;gap:0.75rem;align-items:flex-start;padding:0.65rem 0.9rem;">
  <div style="width:38px;height:38px;min-width:38px;border-radius:50%;overflow:hidden;flex-shrink:0;">
    <img src="/person-name.jpg" style="width:100%;height:100%;object-fit:cover;object-position:center top;" />
  </div>
  <div>
    <div style="font-weight:600;font-size:0.82rem;margin-bottom:0.05rem;">Person Name</div>
    <div style="font-size:0.62rem;color:var(--accent);margin-bottom:0.2rem;">Title, Company</div>
    <div style="font-size:0.7rem;color:var(--text-secondary);line-height:1.4;">Description text.</div>
  </div>
</div>
```

### Testimonial card
```html
<div style="background:var(--card-bg);border-radius:8px;padding:0.75rem 0.8rem;display:flex;flex-direction:column;align-items:center;text-align:center;overflow:hidden;">
  <img src="/person.jpg" alt="Name" style="width:42px;height:42px;border-radius:50%;object-fit:cover;margin-bottom:0.3rem;border:2px solid var(--highlight);flex-shrink:0;" />
  <div style="font-weight:700;font-size:0.72rem;color:var(--heading-color);margin-bottom:0.04rem;">Name</div>
  <div style="font-size:0.55rem;color:var(--text-secondary);margin-bottom:0.35rem;">Title, Company</div>
  <div style="border-left:3px solid var(--accent);padding-left:0.55rem;text-align:left;font-size:0.55rem;color:var(--text-secondary);line-height:1.5;font-style:italic;">"Quote text here."</div>
</div>
```

---

## Charts and Graphics

**Preferred: CSS animated bar charts** — Use the `.bar-chart` / `.bar` / `.bar-fill` / `.bar-value` / `.bar-label` classes from `style.css`. These animate on slide enter via `global-top.vue`. Set each bar's target height with `data-h="XX%"` (the last/tallest bar should be `100%`; scale others proportionally). Start with `style="height:0"`.

```html
<div class="bar-chart reveal reveal-delay-1">
  <div class="bar">
    <div class="bar-value">42</div>
    <div class="bar-fill" style="height:0" data-h="30%"></div>
    <div class="bar-label">Jan</div>
  </div>
  <!-- repeat for each period -->
  <div class="bar">
    <div class="bar-value">135</div>
    <div class="bar-fill" style="height:0" data-h="100%"></div>
    <div class="bar-label">Jun</div>
  </div>
</div>
```

**Alternative: Pre-rendered PNG/JPG images** — For complex charts (line charts, scatter plots), export from Google Sheets/Excel and place in `public/`. Reference with `<img src="/chart-name.png" style="width:100%;height:auto;" />`.

**Never:**
- Write inline `<svg>` with `<text>` elements for charts — SVG text does not scale predictably in Slidev's viewport.
- Use `font-size` values below 10px in any SVG.

**When replacing placeholder bar charts with real user data:**
1. Get the actual data values and time periods from the user
2. Calculate `data-h` percentages relative to the largest value (largest = 100%)
3. Update `bar-value` text to match the actual values
4. Update `bar-label` text to match the time periods

---

## HTML Entity Handling

Slidev renders HTML directly. Use HTML entities in `<div>` and `<span>` blocks:

| Character | Entity | Use case |
|-----------|--------|----------|
| Smart quotes | `&#x201C;` `&#x201D;` `&#x2018;` `&#x2019;` | Disclaimers, testimonials |
| Em dash | `&#x2014;` | Prose |
| Multiplication | `&#xD7;` | Multiplier values (e.g., `4.5×`) |
| Arrow right | `&#x2192;` | Flow indicators |
| Middle dot | `&#183;` | Separators |
| Non-breaking space | `&nbsp;` | Prevent line breaks |
| Up-right arrow | `&#8599;` | Growth indicators |

**Rule:** In HTML context, use entities. In pure markdown, use UTF-8 directly.

## Cross-References

When adding or removing slides:
1. Search for hardcoded page references: `grep -n "slide \d\|page \d\|p\.\d" slides.md`
2. Update all affected references

## Design System Reference

Every Slidev deck has a custom CSS design system in `style.css`. On first use, **read `style.css`** and catalog:

1. **CSS custom properties** (variables) — colors, fonts, spacing
2. **CSS classes** — component classes for cards, stats, headings, footers
3. **Layout patterns** — common grid/flex patterns used across slides

Use these classes and variables consistently. Never hardcode values that exist as variables.

### Default style.css (YC template)

When generating a new deck, create `style.css` with this content:

```css
/* ── YC Seed Deck – Minimal Design System ── */

/* Match the intentionally simple Google Slides aesthetic */
:root {
  --font-sans: 'Inter', ui-sans-serif, system-ui, sans-serif;
  --font-serif: 'Playfair Display', ui-serif, Georgia, serif;
}

/* Light mode (default) — plain white */
.slidev-layout {
  background: #fff !important;
  color: #000 !important;
}

/* Dark mode — inverted */
html.dark .slidev-layout {
  background: #1a1a2e !important;
  color: #e0e0e0 !important;
}

html.dark .slidev-layout h1,
html.dark .slidev-layout h2 {
  color: #f0f0f0 !important;
}

html.dark .slidev-layout ul li,
html.dark .slidev-layout div {
  color: #d0d0d0;
}

/* Invert chart images in dark mode so they remain legible */
html.dark .slidev-layout img[src*="chart-"] {
  filter: invert(1) hue-rotate(180deg);
}

/* Subtitle text in dark mode */
html.dark .slidev-layout .subtitle,
html.dark .slidev-layout p {
  color: #b0b0b0 !important;
}

/* Page numbers in dark mode */
html.dark .slidev-layout div[style*="color:#999"] {
  color: #666 !important;
}

/* ── Reveal Animations ── */
.reveal {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 0.7s cubic-bezier(0.16, 1, 0.3, 1),
              transform 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}
.reveal.is-visible {
  opacity: 1;
  transform: none;
}
.reveal-delay-1 { transition-delay: 0.1s; }
.reveal-delay-2 { transition-delay: 0.2s; }
.reveal-delay-3 { transition-delay: 0.3s; }
.reveal-delay-4 { transition-delay: 0.4s; }

/* ── Animated Bar Charts ── */
.bar-chart {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  height: 220px;
  padding-bottom: 32px;
  position: relative;
  border-bottom: 1px solid #ddd;
}
html.dark .bar-chart { border-bottom-color: #444; }
.bar-chart .bar {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
  position: relative;
}
.bar-chart .bar-fill {
  width: 100%;
  max-width: 64px;
  background: #000;
  border-radius: 3px 3px 0 0;
  height: 0;
  transition: height 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}
html.dark .bar-chart .bar-fill { background: #f59e0b; }
.bar-chart .bar:nth-child(1) .bar-fill { transition-delay: 0.05s; }
.bar-chart .bar:nth-child(2) .bar-fill { transition-delay: 0.1s; }
.bar-chart .bar:nth-child(3) .bar-fill { transition-delay: 0.15s; }
.bar-chart .bar:nth-child(4) .bar-fill { transition-delay: 0.2s; }
.bar-chart .bar:nth-child(5) .bar-fill { transition-delay: 0.25s; }
.bar-chart .bar:nth-child(6) .bar-fill { transition-delay: 0.3s; }
.bar-chart .bar-value {
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  font-size: 0.7rem;
  color: #000;
  margin-bottom: 6px;
  white-space: nowrap;
}
html.dark .bar-chart .bar-value { color: #e0e0e0; }
.bar-chart .bar-label {
  position: absolute;
  bottom: -26px;
  font-family: 'Inter', sans-serif;
  font-size: 0.65rem;
  color: #999;
  white-space: nowrap;
}

/* ── Dot Rail Navigation ── */
.dot-nav {
  position: fixed;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.dot-pip {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: 1.5px solid #ccc;
  background: transparent;
  cursor: pointer;
  padding: 0;
  transition: all 0.2s ease;
}
.dot-pip:hover { border-color: #666; transform: scale(1.4); }
.dot-pip.active { background: #000; border-color: #000; transform: scale(1.3); }
html.dark .dot-pip { border-color: #555; }
html.dark .dot-pip:hover { border-color: #aaa; }
html.dark .dot-pip.active { background: #f59e0b; border-color: #f59e0b; }
@media (max-width: 768px) { .dot-nav { display: none; } }
```

**Dark mode rules:**
- Slidev has a built-in dark mode toggle (moon icon in toolbar). The CSS above makes it work out of the box.
- Chart PNGs are auto-inverted via `filter: invert(1) hue-rotate(180deg)` — this keeps the line colors correct while flipping bg/text.
- Team photos and other non-chart images are NOT inverted — only `img[src*="chart-"]` is targeted.
- When users provide custom charts, name them with `chart-` prefix (e.g., `chart-revenue.png`) so the dark mode inversion applies automatically.

### Common inline patterns
- Slide padding: `padding:2rem 3.5rem` or `padding:3rem 3.5rem`
- Flex column: `height:100%;display:flex;flex-direction:column;justify-content:flex-start;`
- Grid: `display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;`
- Highlight border: `border:1.5px solid rgba(74,222,128,0.6);background:rgba(74,222,128,0.08);`

---

## Ship Workflow

When the user says "ship", "deploy", "push it live", or similar:

### Step 1: Pre-flight
```bash
npx slidev build
```
Fix any build errors before proceeding (unclosed tags, missing images, bad YAML, Vue errors).

### Step 2: Commit
```bash
git add slides.md style.css global-top.vue  # only changed files
git commit -m "descriptive message"
```

### Step 3: Push
```bash
git push origin main
```

### Step 4: Deploy to Vercel
Auto-detect:
1. `deploy.sh` exists → `./deploy.sh`
2. `vercel.json` exists → `npx vercel deploy --prod`
3. Git-triggered auto-deploy → check `npx vercel ls --prod 2>/dev/null | head -5`
4. None found → ask the user

### Step 5: Verify
```bash
# Check status
npx vercel ls --prod 2>/dev/null | head -3

# Check live URL
curl -s -o /dev/null -w "%{http_code}" <PRODUCTION_URL>
```
Report: deploy status, live URL, commit hash.

### Step 6: Post-deploy (optional)
If asked to verify content: fetch the live page and check key content appears.

### Rollback
```bash
git revert HEAD
git push origin main
# re-deploy
```
**Always ask the user before reverting.**

### Quick ship (edit + deploy in one flow)
1. Make the edit
2. `npx slidev build` to verify
3. Commit + push + deploy
4. Verify
5. Report: what changed, commit hash, live URL

---

## Key Facts Table

On first use, scan `slides.md` and build a reference table of key facts (names, numbers, dates). **Always verify against actual slide content before changing values** — slides are the source of truth.

## Completion Protocol

End every task with one of:
- **DONE** — changes applied successfully
- **DONE_WITH_CONCERNS** — changes applied but flagged an issue
- **BLOCKED** — cannot proceed, explain why
- **NEEDS_CONTEXT** — need more information from user
