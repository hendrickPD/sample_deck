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

  <!-- Present Button -->
  <button v-if="!isPrintMode" class="present-btn" @click="togglePresent" :title="isPresenting ? 'Exit presentation' : 'Present'">
    <svg v-if="!isPresenting" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
      <path d="M1.5 1h4v1.5h-2.5v2.5h-1.5v-4zm9 0h4v4h-1.5v-2.5h-2.5v-1.5zm-9 9h1.5v2.5h2.5v1.5h-4v-4zm12.5 2.5h-2.5v1.5h4v-4h-1.5v2.5z"/>
    </svg>
    <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
      <path d="M4.5 1h-4v4h1.5v-2.5h2.5v-1.5zm7 0v1.5h2.5v2.5h1.5v-4h-4zm-11 10.5v4h4v-1.5h-2.5v-2.5h-1.5zm12.5 2.5v1.5h-4v-1.5h2.5v-2.5h1.5z"/>
    </svg>
  </button>

  <!-- iPhone hint: rotate or add to home screen -->
  <div v-if="showHint" class="present-hint" @click="showHint = false">{{ hintText }}</div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
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
        const reveals = activeWrapper.querySelectorAll('.reveal')
        reveals.forEach(el => el.classList.add('is-visible'))

        activeWrapper.querySelectorAll('.bar-chart.is-visible .bar-fill').forEach((bar, i) => {
          setTimeout(() => {
            bar.style.height = bar.dataset.h
          }, i * 100)
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

// ── Present Mode ──
const isPresenting = ref(false)
const showHint = ref(false)
const hintText = ref('')

// Platform state — populated at mount
let isIphone = false
let isStandalone = false
let hintDismissed = false

function detectPlatform() {
  const ua = navigator.userAgent
  isIphone = /iPhone/.test(ua)
  isStandalone = window.navigator.standalone === true ||
    window.matchMedia('(display-mode: standalone)').matches
}

// Try to get the address bar to collapse by scrolling to y=1
function collapseAddressBar() {
  if (document.body.scrollHeight <= window.innerHeight) {
    // Page not tall enough to scroll; temporarily extend it
    document.body.style.minHeight = (window.innerHeight + 2) + 'px'
    window.scrollTo(0, 1)
    setTimeout(() => { document.body.style.minHeight = '' }, 400)
  } else {
    window.scrollTo(0, 1)
  }
}

function showIphoneHint() {
  if (hintDismissed) return
  const isPortrait = window.innerWidth < window.innerHeight
  if (!isStandalone) {
    hintText.value = isPortrait
      ? 'Rotate to landscape · Add to Home Screen for true fullscreen'
      : 'Add to Home Screen for true fullscreen'
    showHint.value = true
    setTimeout(() => { showHint.value = false }, 5000)
  } else if (isPortrait) {
    hintText.value = 'Rotate to landscape'
    showHint.value = true
    setTimeout(() => { showHint.value = false }, 3000)
  }
}

function enterPresent() {
  if (isIphone && !isStandalone) {
    // Path 1: Try native fullscreen first — works on iOS 17.2+ in some configs
    const el = document.documentElement
    const fsPromise = el.requestFullscreen?.() || el.webkitRequestFullscreen?.()
    if (fsPromise) {
      fsPromise.then(() => {
        isPresenting.value = true
        // If fullscreen succeeded, try orientation lock
        if (screen.orientation?.lock) {
          screen.orientation.lock('landscape').catch(() => {})
        }
      }).catch(() => {
        // Fullscreen blocked — fall through to CSS overlay
        enterIphoneOverlay()
      })
    } else {
      enterIphoneOverlay()
    }
  } else if (isIphone && isStandalone) {
    // Standalone PWA on iPhone — just enter overlay + try orientation
    enterIphoneOverlay()
    if (screen.orientation?.lock) {
      screen.orientation.lock('landscape').catch(() => {})
    }
  } else {
    // Desktop / Android — native fullscreen + orientation lock
    const el = document.documentElement
    const fsPromise = el.requestFullscreen?.() || el.webkitRequestFullscreen?.()
    if (fsPromise) {
      fsPromise.then(() => {
        isPresenting.value = true
        if (screen.orientation?.lock) {
          screen.orientation.lock('landscape').catch(() => {})
        }
      }).catch(() => {
        enterCSSOverlay()
      })
    } else {
      enterCSSOverlay()
    }
  }
}

function enterIphoneOverlay() {
  enterCSSOverlay()
  collapseAddressBar()
  showIphoneHint()
}

function enterCSSOverlay() {
  document.documentElement.classList.add('is-presenting')
  isPresenting.value = true
}

function exitPresent() {
  document.documentElement.classList.remove('is-presenting')
  isPresenting.value = false
  showHint.value = false
  if (document.fullscreenElement) {
    document.exitFullscreen?.().catch(() => {})
  }
  window.scrollTo(0, 0)
}

function togglePresent() {
  if (isPresenting.value) {
    exitPresent()
  } else {
    enterPresent()
  }
}

function onFullscreenChange() {
  if (document.fullscreenElement) {
    isPresenting.value = true
    if (screen.orientation?.lock) {
      screen.orientation.lock('landscape').catch(() => {})
    }
  } else {
    // Exited fullscreen via Escape or native controls
    document.documentElement.classList.remove('is-presenting')
    isPresenting.value = false
  }
}

onMounted(() => {
  detectPlatform()
  window.addEventListener('beforeunload', sendAnalytics)
  document.addEventListener('fullscreenchange', onFullscreenChange)
  document.addEventListener('webkitfullscreenchange', onFullscreenChange)
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', sendAnalytics)
  document.removeEventListener('fullscreenchange', onFullscreenChange)
  document.removeEventListener('webkitfullscreenchange', onFullscreenChange)
  document.documentElement.classList.remove('is-presenting')
})
</script>
