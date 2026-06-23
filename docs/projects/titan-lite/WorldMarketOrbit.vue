<template>
  <div class="spatial-orbit-container" @mousemove="handleMouseMove" @mouseleave="handleMouseLeave">
    <!-- Viewport that tilts dynamically on mouse-hover -->
    <div class="space-canvas" :style="spaceStyle">
      <!-- 3D Perspective coordinate grid floor -->
      <div class="grid-floor"></div>

      <!-- Volumetric 3D Sector Blocks -->
      <div class="sectors-grid-3d">
        <div 
          v-for="s in sectors" 
          :key="s.id" 
          class="sector-column-3d"
          :class="{ focused: activeNode === s.id, blurred: activeNode && activeNode !== s.id }"
          :style="[s.style, { '--cube-h': s.height + 'px' }]"
          @mouseenter="activeNode = s.id"
          @mouseleave="activeNode = null"
        >
          <!-- 3D Cube faces with metallic gradients -->
          <div class="cube-face front" :style="{ background: s.gradient }"></div>
          <div class="cube-face back" :style="{ background: s.gradient }"></div>
          <div class="cube-face left" :style="{ background: s.gradient }"></div>
          <div class="cube-face right" :style="{ background: s.gradient }"></div>
          <div class="cube-face top" :style="{ backgroundColor: s.topColor }"></div>
          <div class="cube-face bottom" :style="{ background: s.gradient }"></div>

          <!-- Elegant floating gold/silver outline tag -->
          <div class="float-tag glass-panel">
            <span class="sector-title">{{ s.name }}</span>
            <span class="stock-ticker">{{ s.leader }}</span>
            <span class="percent" :class="getChangeClass(s.change)">{{ s.change }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const activeNode = ref(null)
const mouseX = ref(0)
const mouseY = ref(0)
const benchmarks = ref({ CN: {}, US: {} })

const handleMouseMove = (e) => {
  if (typeof window === 'undefined') return
  const { clientX, clientY, currentTarget } = e
  const { left, top, width, height } = currentTarget.getBoundingClientRect()
  
  // Normalise mouse coords to [-1, 1]
  mouseX.value = ((clientX - left) / width) * 2 - 1
  mouseY.value = ((clientY - top) / height) * 2 - 1
}

const handleMouseLeave = () => {
  mouseX.value = 0
  mouseY.value = 0
}

// 3D Space parallax rotation calculation
const spaceStyle = computed(() => {
  const rotX = -mouseY.value * 15 // Rotates max 15 degrees around X-axis
  const rotY = mouseX.value * 15  // Rotates max 15 degrees around Y-axis
  return {
    transform: `rotateX(${rotX}deg) rotateY(${rotY}deg)`
  }
})

const getChangeClass = (val) => {
  if (!val || val === 'Data N/A') return 'neutral'
  return val.startsWith('+') ? 'up' : 'down'
}

// Connect to new FastAPI route for sector calculations
const fetchSectors = async () => {
  const API_BASE = typeof window !== 'undefined' 
    ? `${window.location.protocol}//${window.location.hostname}:8000` 
    : 'http://localhost:8000'
  try {
    const res = await fetch(`${API_BASE}/market/sectors`)
    if (res.ok) {
      benchmarks.value = await res.json()
    }
  } catch (e) {
    console.log("Sector analytics fetch failed (offline mode).")
  }
}

const sectors = computed(() => {
  const cn = benchmarks.value.CN || {}
  const us = benchmarks.value.US || {}

  return [
    {
      id: 'semi',
      name: 'Semiconductors',
      leader: 'NVDA / 688017',
      change: us['半导体(SOXX)'] || cn['半导体概念'] || '+1.55%',
      height: 150,
      gradient: 'linear-gradient(to top, rgba(197, 168, 128, 0.08) 0%, rgba(197, 168, 128, 0.4) 100%)',
      topColor: 'rgba(197, 168, 128, 0.65)',
      style: { transform: 'translate3d(-170px, 30px, 30px)' }
    },
    {
      id: 'robot',
      name: 'Robotics',
      leader: '688017 / TSLA',
      change: cn['机器人'] || '+1.46%',
      height: 120,
      gradient: 'linear-gradient(to top, rgba(224, 224, 224, 0.06) 0%, rgba(224, 224, 224, 0.3) 100%)',
      topColor: 'rgba(255, 255, 255, 0.55)',
      style: { transform: 'translate3d(-80px, -40px, -20px)' }
    },
    {
      id: 'ai',
      name: 'Artificial Intelligence',
      leader: 'DeepSeek / 688023',
      change: us['科技(XLK)'] || '+0.78%',
      height: 200,
      gradient: 'linear-gradient(to top, rgba(197, 168, 128, 0.12) 0%, rgba(240, 230, 200, 0.5) 100%)',
      topColor: 'rgba(240, 230, 200, 0.75)',
      style: { transform: 'translate3d(10px, -85px, 40px)' }
    },
    {
      id: 'health',
      name: 'Healthcare',
      leader: '688017 / LLY',
      change: us['医疗(XLV)'] || '+0.12%',
      height: 130,
      gradient: 'linear-gradient(to top, rgba(144, 164, 174, 0.08) 0%, rgba(207, 216, 220, 0.35) 100%)',
      topColor: 'rgba(207, 216, 220, 0.55)',
      style: { transform: 'translate3d(100px, 20px, -10px)' }
    },
    {
      id: 'energy',
      name: 'Energy',
      leader: '688013 / XOM',
      change: us['能源(XLE)'] || '-0.45%',
      height: 90,
      gradient: 'linear-gradient(to top, rgba(80, 90, 100, 0.12) 0%, rgba(120, 135, 150, 0.3) 100%)',
      topColor: 'rgba(120, 135, 150, 0.5)',
      style: { transform: 'translate3d(180px, -10px, 60px)' }
    }
  ]
})

onMounted(() => {
  fetchSectors()
})
</script>

<style scoped>
.spatial-orbit-container {
  width: 100%;
  height: 480px;
  background-color: transparent;
  border-radius: 20px;
  border: 1px solid var(--wl-border);
  margin-bottom: 2.5rem;
  overflow: hidden;
  position: relative;
  perspective: 1200px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.space-canvas {
  width: 100%;
  height: 100%;
  position: relative;
  transform-style: preserve-3d;
  transition: transform 0.15s ease-out;
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 3D perspective floor grid (glowing lines) */
.grid-floor {
  position: absolute;
  width: 1400px;
  height: 1400px;
  background-image: 
    linear-gradient(var(--wl-border) 1px, transparent 1px),
    linear-gradient(90deg, var(--wl-border) 1px, transparent 1px);
  background-size: 40px 40px;
  background-position: center;
  transform: rotateX(75deg) translateZ(-160px);
  pointer-events: none;
}

.sectors-grid-3d {
  position: absolute;
  width: 100%;
  height: 100%;
  transform-style: preserve-3d;
  display: flex;
  justify-content: center;
  align-items: center;
  pointer-events: none;
}

.sector-column-3d {
  position: absolute;
  width: 70px;
  height: var(--cube-h);
  transform-style: preserve-3d;
  transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
  pointer-events: auto;
  cursor: pointer;
}

/* 3D Cube faces configuration */
.cube-face {
  position: absolute;
  width: 70px;
  border: 1px solid var(--wl-border);
  transform-style: preserve-3d;
}

.cube-face.front {
  height: 100%;
  transform: rotateY(0deg) translateZ(35px);
  border-bottom: none;
}
.cube-face.back {
  height: 100%;
  transform: rotateY(180deg) translateZ(35px);
  border-bottom: none;
}
.cube-face.left {
  height: 100%;
  transform: rotateY(-90deg) translateZ(35px);
  border-bottom: none;
}
.cube-face.right {
  height: 100%;
  transform: rotateY(90deg) translateZ(35px);
  border-bottom: none;
}
.cube-face.top {
  height: 70px;
  transform: rotateX(90deg) translateZ(35px);
  border: 1px solid var(--wl-border);
}
.cube-face.bottom {
  height: 70px;
  transform: rotateX(-90deg) translateZ(calc(var(--cube-h) - 35px));
}

/* Interactive focus transitions */
.sector-column-3d:hover {
  transform: translate3d(var(--tx, 0), var(--ty, 0), 130px) scale(1.05) !important;
}

.sector-column-3d:nth-child(1) { --tx: -170px; --ty: 30px; }
.sector-column-3d:nth-child(2) { --tx: -80px; --ty: -40px; }
.sector-column-3d:nth-child(3) { --tx: 10px; --ty: -85px; }
.sector-column-3d:nth-child(4) { --tx: 100px; --ty: 20px; }
.sector-column-3d:nth-child(5) { --tx: 180px; --ty: -10px; }

.sector-column-3d.blurred {
  filter: blur(1.5px) grayscale(30%);
  opacity: 0.35;
  transform: translate3d(var(--tx, 0), var(--ty, 0), -65px) !important;
}

/* Float tag indicator */
.float-tag {
  position: absolute;
  top: -85px;
  left: 50%;
  transform: translateX(-50%) translateZ(10px);
  width: 140px;
  padding: 8px 12px;
  border-radius: 8px;
  background: var(--vp-c-bg);
  border: 1px solid var(--wl-border);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(8px);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  pointer-events: none;
}

.sector-title {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--vp-c-text-1);
  text-align: center;
  white-space: nowrap;
}

.stock-ticker {
  font-size: 0.55rem;
  color: var(--vp-c-text-3);
}

.percent {
  font-size: 0.65rem;
  font-weight: 800;
  padding: 0 4px;
  border-radius: 3px;
  margin-top: 2px;
}

.percent.up { color: var(--wl-mint); background: rgba(129, 199, 132, 0.1); }
.percent.down { color: var(--wl-brick); background: rgba(229, 115, 115, 0.1); }
.percent.neutral { color: var(--vp-c-text-3); background: rgba(139, 148, 158, 0.1); }
</style>
