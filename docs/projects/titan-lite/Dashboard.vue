<template>
  <div class="wl-canvas" style="padding-top: 2rem; min-height: 100vh;">
    <!-- Hero Header -->
    <header style="text-align: center; margin-bottom: 4rem;">
      <h1 class="wl-heading-1" style="font-size: 3rem; font-weight: 300; letter-spacing: -0.05em; text-transform: uppercase;">TITAN-LITE COCKPIT</h1>
    </header>

    <!-- 3-Column Dashboard -->
    <div class="dashboard-grid">
      <!-- Left: Engine Controls (Includes 3 research modes & Terminal) -->
      <div class="wl-dashboard-panel">
        <ControlPanel />
      </div>

      <!-- Middle: Market Orbit (New Minimalist 2D Orbit) -->
      <div class="wl-dashboard-panel" style="display: flex; justify-content: center; align-items: flex-start; padding-top: 2rem;">
        <WorldMarketOrbit />
      </div>

      <!-- Right: Portfolio Stats -->
      <div class="wl-dashboard-panel">
        <FundManager :mini="true" />
      </div>
    </div>
  </div>
</template>

<script setup>
import ControlPanel from './ControlPanel.vue'
import WorldMarketOrbit from './WorldMarketOrbit.vue'
import FundManager from './FundManager.vue'
</script>
