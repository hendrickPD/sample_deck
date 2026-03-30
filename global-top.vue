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

  <!-- Rotate hint (iPhone, portrait, presenting) -->
  <div v-if="showRotateHint" class="rotate-hint">Rotate to landscape</div>
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

watch(currentSlideNo, (n) => {
  triggerReveals(n)
})

onMounted(() => {
  setTimeout(() => triggerReveals(currentSlideNo.value), 300)
})

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
  } catch (e) {
    // Analytics are best-effort
  }
}

// ── Present Mode ──
const isPresenting = ref(false)
const showRotateHint = ref(false)

// Platform detection (run once at mount to avoid SSR issues)
let isIphone = false
let canFullscreen = false
let canLockOrientation = false

function detectPlatform() {
  isIphone = /iPhone/.test(navigator.userAgent)
  canFullscreen = !!document.documentElement.requestFullscreen
  canLockOrientation = !!screen.orientation?.lock
}

function checkOrientation() {
  // Show rotate hint on devices where we can't force orientation
  showRotateHint.value = isPresenting.value && window.innerWidth < window.innerHeight
}

function enterPresent() {
  if (isIphone) {
    // iPhone Safari: can't do fullscreen — use CSS overlay mode
    document.documentElement.classList.add('is-presenting')
    isPresenting.value = true
    checkOrientation()
    window.addEventListener('resize', checkOrientation)
  } else if (canFullscreen) {
    document.documentElement.requestFullscreen().catch(() => {})
    // isPresenting set in fullscreenchange handler
  }
}

function exitPresent() {
  if (isIphone) {
    document.documentElement.classList.remove('is-presenting')
    isPresenting.value = false
    showRotateHint.value = false
    window.removeEventListener('resize', checkOrientation)
  } else if (document.fullscreenElement) {
    document.exitFullscreen().catch(() => {})
    // isPresenting cleared in fullscreenchange handler
  }
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
    if (canLockOrientation) {
      screen.orientation.lock('landscape').catch(() => {})
    }
  } else {
    isPresenting.value = false
  }
}

onMounted(() => {
  detectPlatform()
  window.addEventListener('beforeunload', sendAnalytics)
  document.addEventListener('fullscreenchange', onFullscreenChange)
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', sendAnalytics)
  document.removeEventListener('fullscreenchange', onFullscreenChange)
  window.removeEventListener('resize', checkOrientation)
  // Clean up iPhone overlay if component unmounts while presenting
  document.documentElement.classList.remove('is-presenting')
})
</script>
