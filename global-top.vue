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
    // Reset bar heights and remove is-visible from all reveals
    document.querySelectorAll('.bar-fill').forEach(bar => {
      bar.style.height = '0'
    })
    document.querySelectorAll('.reveal.is-visible').forEach(el => {
      el.classList.remove('is-visible')
    })

    // Find the active slide container by class name
    nextTick(() => {
      const activeWrapper = document.querySelector('.slidev-page-' + slideNo)
      if (activeWrapper) {
        const reveals = activeWrapper.querySelectorAll('.reveal')
        reveals.forEach(el => el.classList.add('is-visible'))

        // Animate bar charts — set heights from data-h
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

onMounted(() => {
  window.addEventListener('beforeunload', sendAnalytics)
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', sendAnalytics)
})
</script>
