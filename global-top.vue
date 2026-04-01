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

// ── Counter Animation ──
const activeCounters = new Map() // el → rAF id

function parseBarValue(text) {
  const m = text.trim().match(/^(\$?)([0-9.]+)(K|M|B|x|%)?$/)
  if (!m) return null
  return { num: parseFloat(m[2]), prefix: m[1], suffix: m[3] || '' }
}

function formatBarValue(num, prefix, suffix) {
  // Integer suffix (K/M/B/%/x): show rounded; decimal like 1.2M: 1 decimal place
  const needsDecimal = !Number.isInteger(parseFloat(num.toFixed(1))) && num < 10
  const display = needsDecimal ? num.toFixed(1) : String(Math.round(num))
  return `${prefix}${display}${suffix}`
}

function cancelCounter(el) {
  const id = activeCounters.get(el)
  if (id !== undefined) { cancelAnimationFrame(id); activeCounters.delete(el) }
}

function resetAllCounters() {
  document.querySelectorAll('.bar-value').forEach(el => {
    cancelCounter(el)
    // Restore original text from data-value (set once on first encounter)
    if (el.dataset.value) el.textContent = el.dataset.value
  })
}

function animateCounter(el, delay = 0) {
  // Initialize data-value from DOM exactly once — this is the source of truth
  if (!el.dataset.value) el.dataset.value = el.textContent.trim()
  const parsed = parseBarValue(el.dataset.value)
  if (!parsed) return

  cancelCounter(el)

  const startTime = performance.now() + delay
  const duration = 900

  function tick(now) {
    if (now < startTime) {
      activeCounters.set(el, requestAnimationFrame(tick))
      return
    }
    const elapsed = now - startTime
    const t = Math.min(elapsed / duration, 1)
    const eased = 1 - Math.pow(1 - t, 3)  // ease-out cubic
    el.textContent = formatBarValue(parsed.num * eased, parsed.prefix, parsed.suffix)

    if (t < 1) {
      activeCounters.set(el, requestAnimationFrame(tick))
    } else {
      el.textContent = el.dataset.value  // snap to exact original at end
      activeCounters.delete(el)
    }
  }

  activeCounters.set(el, requestAnimationFrame(tick))
}

// ── Reveal Animation Trigger ──
function triggerReveals(slideNo) {
  nextTick(() => {
    // Reset everything: cancel counters, restore text, reset bars, remove reveals
    resetAllCounters()
    document.querySelectorAll('.bar-fill').forEach(bar => { bar.style.height = '0' })
    document.querySelectorAll('.reveal.is-visible').forEach(el => { el.classList.remove('is-visible') })

    nextTick(() => {
      const activeWrapper = document.querySelector('.slidev-page-' + slideNo)
      if (activeWrapper) {
        activeWrapper.querySelectorAll('.reveal').forEach(el => el.classList.add('is-visible'))

        activeWrapper.querySelectorAll('.bar-chart .bar').forEach((bar, i) => {
          const fill = bar.querySelector('.bar-fill')
          const value = bar.querySelector('.bar-value')
          const delay = i * 100
          // Animate bar height via CSS transition (set after brief delay for stagger)
          setTimeout(() => {
            if (fill) fill.style.height = fill.dataset.h
          }, delay)
          // Animate counter in sync with bar, starting from 0
          if (value) animateCounter(value, delay)
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
  const payload = JSON.stringify({
    slides: analytics,
    total_slides: total.value,
    timestamp: new Date().toISOString()
  })
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
