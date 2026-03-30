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

  <!-- Video present overlay (iPhone CSS fallback + video canvas renderer) -->
  <div v-if="showVideoOverlay" class="video-overlay" @click="handleOverlayTap" @touchstart="onTouchStart" @touchend="onTouchEnd">
    <video ref="overlayVideo" class="video-overlay-screen" muted playsinline webkit-playsinline autoplay />
    <button class="video-overlay-close" @click.stop="exitPresent">✕</button>
    <div class="video-overlay-nav">{{ currentSlideNo }} / {{ total }}</div>
    <div v-if="overlayHint" class="video-overlay-hint">{{ overlayHint }}</div>
  </div>

  <!-- Hint for iPhone in browser tab -->
  <div v-if="showHint && !showVideoOverlay" class="present-hint" @click="showHint = false">{{ hintText }}</div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useNav } from '@slidev/client'

const { currentSlideNo, total, go, isPrintMode } = useNav()

// ── Reveal Animation Trigger ──
function triggerReveals(slideNo) {
  nextTick(() => {
    document.querySelectorAll('.bar-fill').forEach(bar => { bar.style.height = '0' })
    document.querySelectorAll('.reveal.is-visible').forEach(el => { el.classList.remove('is-visible') })
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
function recordSlideEnter(slideNo) { currentSlide = slideNo; enterTime = Date.now() }
watch(currentSlideNo, (n) => { recordSlideLeave(); recordSlideEnter(n) })
function sendAnalytics() {
  recordSlideLeave()
  const payload = JSON.stringify({ slides: analytics, total_slides: total.value, timestamp: new Date().toISOString() })
  try { if (navigator.sendBeacon) navigator.sendBeacon('/api/track', new Blob([payload], { type: 'application/json' })) } catch (e) {}
}

// ── Video Present Pipeline ──
const isPresenting = ref(false)
const showVideoOverlay = ref(false)
const showHint = ref(false)
const hintText = ref('')
const overlayHint = ref('')
const overlayVideo = ref(null)

let isIphone = false
let isStandalone = false
let presentCanvas = null
let presentStream = null
let captureStreamWorks = false
let slideImages = {}          // slideNo → HTMLImageElement (pre-loaded)

function detectPlatform() {
  isIphone = /iPhone/.test(navigator.userAgent)
  isStandalone = window.navigator.standalone === true ||
    window.matchMedia('(display-mode: standalone)').matches
}

// Pre-load all slide PNGs into memory so draw is synchronous on Present tap
async function preloadSlides() {
  const loads = []
  for (let i = 1; i <= total.value; i++) {
    loads.push(new Promise(resolve => {
      const img = new Image()
      img.onload = () => { slideImages[i] = img; resolve() }
      img.onerror = resolve   // tolerate missing
      img.src = `/slide-images/${i}.png`
    }))
  }
  await Promise.all(loads)
}

// Draw a slide PNG to the presenter canvas (<2ms once image is cached)
function drawSlide(slideNo) {
  if (!presentCanvas || !slideImages[slideNo]) return
  const ctx = presentCanvas.getContext('2d')
  ctx.drawImage(slideImages[slideNo], 0, 0, presentCanvas.width, presentCanvas.height)
}

// Set up canvas + captureStream; returns true if captureStream is functional
async function setupCanvas() {
  presentCanvas = document.createElement('canvas')
  presentCanvas.width = 1920
  presentCanvas.height = 1080
  // Fill white so first frame isn't black
  const ctx = presentCanvas.getContext('2d')
  ctx.fillStyle = '#fff'
  ctx.fillRect(0, 0, 1920, 1080)

  try {
    presentStream = presentCanvas.captureStream(30)
    if (!presentStream.getTracks().length) return false
    captureStreamWorks = true
    return true
  } catch (e) {
    return false
  }
}

// Keep canvas in sync with current slide while presenting
watch(currentSlideNo, (n) => {
  if (isPresenting.value) drawSlide(n)
})

// ── Present Entry / Exit ──
async function enterPresent() {
  if (!captureStreamWorks) {
    enterCSSOverlay()
    return
  }

  // Draw current slide before entering fullscreen (synchronous — images pre-loaded)
  drawSlide(currentSlideNo.value)

  if (isIphone) {
    // Path 1: native video fullscreen via webkitEnterFullscreen
    // This is the only true fullscreen available on iPhone Safari
    const video = createHiddenVideo()
    if (video && video.webkitSupportsFullscreen) {
      setupMediaSession()
      video.addEventListener('webkitbeginfullscreen', () => { isPresenting.value = true }, { once: true })
      video.addEventListener('webkitendfullscreen', () => {
        isPresenting.value = false
        showVideoOverlay.value = false
        removeHiddenVideo()
      }, { once: true })
      video.webkitEnterFullscreen()
      isPresenting.value = true
      return
    }
    // Path 2: CSS overlay with canvas-rendered video (address bar stays but slide looks clean)
    enterVideoOverlay()
    collapseAddressBar()
    showIphoneHint()
  } else {
    // Desktop / Android — standard fullscreen
    const el = document.documentElement
    const p = el.requestFullscreen?.() || el.webkitRequestFullscreen?.()
    if (p) {
      p.then(() => {
        isPresenting.value = true
        screen.orientation?.lock?.('landscape').catch(() => {})
      }).catch(() => enterCSSOverlay())
    } else {
      enterCSSOverlay()
    }
  }
}

function createHiddenVideo() {
  // Create video from canvas stream, hidden but in DOM (required for iOS webkitEnterFullscreen)
  if (!presentStream) return null
  const video = document.createElement('video')
  video.id = '__present_video__'
  video.srcObject = presentStream
  video.muted = true
  video.setAttribute('playsinline', '')
  video.setAttribute('webkit-playsinline', '')
  video.style.cssText = 'position:fixed;opacity:0.01;pointer-events:none;width:1px;height:1px;top:0;left:0;z-index:-1;'
  document.body.appendChild(video)
  video.play().catch(() => {})
  return video
}

function removeHiddenVideo() {
  const v = document.getElementById('__present_video__')
  if (v) { v.srcObject = null; v.remove() }
}

function enterVideoOverlay() {
  showVideoOverlay.value = true
  isPresenting.value = true
  // Attach stream to the overlay video element after it renders
  nextTick(() => {
    if (overlayVideo.value && presentStream) {
      overlayVideo.value.srcObject = presentStream
      overlayVideo.value.play().catch(() => {})
    }
  })
}

function enterCSSOverlay() {
  document.documentElement.classList.add('is-presenting')
  isPresenting.value = true
}

function exitPresent() {
  isPresenting.value = false
  showVideoOverlay.value = false
  showHint.value = false
  document.documentElement.classList.remove('is-presenting')
  if (document.fullscreenElement) document.exitFullscreen?.().catch(() => {})
  removeHiddenVideo()
  window.scrollTo(0, 0)
  // Clear MediaSession
  if ('mediaSession' in navigator) {
    navigator.mediaSession.setActionHandler('nexttrack', null)
    navigator.mediaSession.setActionHandler('previoustrack', null)
  }
}

function togglePresent() {
  if (isPresenting.value) exitPresent()
  else enterPresent()
}

// ── Touch nav inside overlay ──
let touchStartX = 0
function onTouchStart(e) { touchStartX = e.touches[0].clientX }
function onTouchEnd(e) {
  const dx = e.changedTouches[0].clientX - touchStartX
  if (Math.abs(dx) > 40) {
    dx < 0 ? go(Math.min(currentSlideNo.value + 1, total.value)) : go(Math.max(currentSlideNo.value - 1, 1))
  }
}
function handleOverlayTap(e) {
  // Tap right 2/3 → next, tap left 1/3 → prev
  const x = e.clientX / window.innerWidth
  if (x > 0.33) go(Math.min(currentSlideNo.value + 1, total.value))
  else go(Math.max(currentSlideNo.value - 1, 1))
}

// ── MediaSession (Control Center next/prev while in native video fullscreen) ──
function setupMediaSession() {
  if (!('mediaSession' in navigator)) return
  navigator.mediaSession.metadata = new MediaMetadata({ title: 'Slide Presentation' })
  navigator.mediaSession.setActionHandler('nexttrack', () => go(Math.min(currentSlideNo.value + 1, total.value)))
  navigator.mediaSession.setActionHandler('previoustrack', () => go(Math.max(currentSlideNo.value - 1, 1)))
}

// ── Address bar collapse (scroll trick) ──
function collapseAddressBar() {
  const extra = document.body.scrollHeight <= window.innerHeight
  if (extra) document.body.style.minHeight = (window.innerHeight + 2) + 'px'
  window.scrollTo(0, 1)
  if (extra) setTimeout(() => { document.body.style.minHeight = '' }, 400)
}

// ── iPhone hint ──
function showIphoneHint() {
  if (isStandalone) return
  const isPortrait = window.innerWidth < window.innerHeight
  overlayHint.value = isPortrait
    ? 'Rotate to landscape · Add to Home Screen for true fullscreen'
    : 'Add to Home Screen for true fullscreen'
  setTimeout(() => { overlayHint.value = '' }, 5000)
}

// ── Fullscreen change (desktop / non-webkit) ──
function onFullscreenChange() {
  if (document.fullscreenElement) {
    isPresenting.value = true
    screen.orientation?.lock?.('landscape').catch(() => {})
  } else {
    isPresenting.value = false
    document.documentElement.classList.remove('is-presenting')
  }
}

onMounted(async () => {
  detectPlatform()
  window.addEventListener('beforeunload', sendAnalytics)
  document.addEventListener('fullscreenchange', onFullscreenChange)
  document.addEventListener('webkitfullscreenchange', onFullscreenChange)

  // Set up canvas pipeline in background; preload slide images
  const ok = await setupCanvas()
  if (ok) await preloadSlides()
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', sendAnalytics)
  document.removeEventListener('fullscreenchange', onFullscreenChange)
  document.removeEventListener('webkitfullscreenchange', onFullscreenChange)
  document.documentElement.classList.remove('is-presenting')
  removeHiddenVideo()
})
</script>
