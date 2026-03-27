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
<h2 style="font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:700;color:#000;margin:0 0 1.5rem;">Traditional tools slow you down</h2>
<ul style="font-size:1.15rem;color:#000;line-height:2.2;list-style:disc;padding-left:2rem;">
  <li>Figma and Google Slides can&#x2019;t be driven by AI &#x2014; every change is manual</li>
  <li>Claude can write code, but GUI tools limit what it can iterate on</li>
  <li>You should be refining your story, not dragging boxes around</li>
</ul>
<div style="margin-top:auto;text-align:right;font-size:0.75rem;color:#999;">2</div>
</div>

---
layout: default
---

<!-- Slide 3: Solution -->
<div style="padding:3rem 4rem;height:100%;display:flex;flex-direction:column;">
<h2 style="font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:700;color:#000;margin:0 0 1.5rem;">One command installs the fix</h2>
<ul style="font-size:1.15rem;color:#000;line-height:2.2;list-style:disc;padding-left:2rem;">
  <li>A Claude Code skill that scaffolds a YC-format deck in seconds</li>
  <li>Tell it your story &#x2014; it writes the slides, builds the charts</li>
  <li>Export as PDF or deploy straight to Vercel &#x2014; your call</li>
  <li>Say /seed-deck and you&#x2019;re live</li>
</ul>
<div style="margin-top:auto;text-align:right;font-size:0.75rem;color:#999;">3</div>
</div>

---
layout: default
---

<!-- Slide 4: Traction -->
<div style="padding:3rem 4rem;height:100%;display:flex;flex-direction:column;">
<h2 style="font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:700;color:#000;margin:0 0 1rem;">Decks shipped through our skill</h2>
<div style="display:grid;grid-template-columns:2.2fr 1fr;gap:2rem;flex:1;align-items:center;">
  <div>
    <img src="/chart-decks.png" style="width:100%;height:auto;" alt="Decks created per month" />
  </div>
  <div style="font-size:1rem;color:#000;line-height:2;">
    <div>-&nbsp;&nbsp;50% growth per month. Every month.</div>
    <div>-&nbsp;&nbsp;100% retention</div>
  </div>
</div>
<div style="margin-top:auto;text-align:right;font-size:0.75rem;color:#999;">4</div>
</div>

---
layout: default
---

<!-- Slide 5: More Traction -->
<div style="padding:3rem 4rem;height:100%;display:flex;flex-direction:column;">
<h2 style="font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:700;color:#000;margin:0 0 1rem;">Capital raised using our decks</h2>
<div style="display:grid;grid-template-columns:2.2fr 1fr;gap:2rem;flex:1;align-items:center;">
  <div>
    <img src="/chart-dollars.png" style="width:100%;height:auto;" alt="Dollars per month" />
  </div>
  <div style="font-size:1rem;color:#000;line-height:2;">
    <div>-&nbsp;&nbsp;Real dollars, not tokens</div>
    <div>-&nbsp;&nbsp;95% close rate vs. 12% industry average</div>
  </div>
</div>
<div style="margin-top:auto;text-align:right;font-size:0.75rem;color:#999;">5</div>
</div>

---
layout: default
---

<!-- Slide 6: Insight / Why It Works -->
<div style="padding:3rem 4rem;height:100%;display:flex;flex-direction:column;">
<h2 style="font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:700;color:#000;margin:0 0 1.5rem;">Skills are the new plugins</h2>
<ul style="font-size:1.15rem;color:#000;line-height:2.2;list-style:disc;padding-left:2rem;">
  <li>Skills = domain expertise as reusable prompts</li>
  <li>One file carries the full YC playbook</li>
  <li>Updates on GitHub, improves everywhere instantly</li>
</ul>
<div style="margin-top:auto;text-align:right;font-size:0.75rem;color:#999;">6</div>
</div>

---
layout: default
---

<!-- Slide 7: Business Model -->
<div style="padding:3rem 4rem;height:100%;display:flex;flex-direction:column;">
<h2 style="font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:700;color:#000;margin:0 0 1.5rem;">How to install this skill right now</h2>
<ul style="font-size:1.15rem;color:#000;line-height:2.2;list-style:disc;padding-left:2rem;">
  <li>mkdir -p .claude/skills/seed-deck</li>
  <li>curl the SKILL.md from GitHub into that folder</li>
  <li>Open Claude Code, type /seed-deck, watch it scaffold your deck</li>
  <li>Give it your data &#x2014; it writes slides, builds, and deploys</li>
</ul>
<div style="margin-top:auto;text-align:right;font-size:0.75rem;color:#999;">7</div>
</div>

---
layout: default
---

<!-- Slide 8: Market / Future Growth -->
<div style="padding:3rem 4rem;height:100%;display:flex;flex-direction:column;">
<h2 style="font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:700;color:#000;margin:0 0 1.5rem;">Every founder needs a deck</h2>
<ul style="font-size:1.15rem;color:#000;line-height:2.2;list-style:disc;padding-left:2rem;">
  <li>1,500+ YC companies per batch, 50,000+ startups raising seed rounds per year</li>
  <li>AI-native founders already live in the terminal &#x2014; Claude Code is their IDE</li>
  <li>Skills are the app store for AI workflows. Decks are just the beginning.</li>
</ul>
<div style="margin-top:auto;text-align:right;font-size:0.75rem;color:#999;">8</div>
</div>

---
layout: default
---

<!-- Slide 9: Team -->
<div style="padding:3rem 4rem;height:100%;display:flex;flex-direction:column;">
<h2 style="font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:700;color:currentColor;margin:0 0 1.5rem;text-align:center;">Team</h2>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:2rem;flex:1;align-items:center;">
  <div style="text-align:center;">
    <img src="/peppa.jpg" style="width:160px;height:200px;object-fit:cover;margin:0 auto 0.75rem;display:block;" />
    <div style="font-size:1rem;color:currentColor;line-height:1.5;text-align:center;">CTO who<br/>ships skills<br/>at 2am</div>
  </div>
  <div style="text-align:center;">
    <img src="/kermit.jpg" style="width:160px;height:200px;object-fit:cover;margin:0 auto 0.75rem;display:block;" />
    <div style="font-size:1rem;color:currentColor;line-height:1.5;text-align:center;">CEO who<br/>knows how<br/>to pitch</div>
  </div>
  <div style="text-align:center;">
    <img src="/robot.jpg" style="width:160px;height:200px;object-fit:cover;margin:0 auto 0.75rem;display:block;" />
    <div style="font-size:1rem;color:currentColor;line-height:1.5;text-align:center;">VP eng<br/>who literally<br/>never sleeps</div>
  </div>
</div>
<div style="margin-top:auto;text-align:right;font-size:0.75rem;color:#999;">9</div>
</div>

---
layout: default
---

<!-- Slide 10: The Ask -->
<div style="padding:3rem 4rem;height:100%;display:flex;flex-direction:column;">
<h2 style="font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:700;color:#000;margin:0 0 1.5rem;">What we need</h2>
<ul style="font-size:1.15rem;color:#000;line-height:2.2;list-style:disc;padding-left:2rem;">
  <li>$1.5m to build the skill marketplace for AI-native founders</li>
  <li>Hire 3 engineers, launch 10 vertical skills (decks, contracts, data rooms)</li>
  <li>Series A ready in 12 months: 10k installs, $2M ARR</li>
  <li>Try it yourself: /seed-deck</li>
  <li>Huge thank you to <a href="https://www.ycombinator.com/library/2u-how-to-build-your-seed-round-pitch-deck" target="_blank" style="color:#f60;">YC&#x2019;s How to Build Your Seed Round Pitch Deck</a></li>
  <li>Huge thank you to <a href="https://github.com/garrytan/gstack" target="_blank" style="color:#f60;">Garry Tan</a> and <a href="https://github.com/garrytan/gstack" target="_blank" style="color:#f60;">gstack</a></li>
</ul>
<div style="margin-top:auto;text-align:right;font-size:0.75rem;color:#999;">10</div>
</div>
