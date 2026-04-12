<template>
  <div class="installer-container">
    <div class="installer-header">
      <h2 class="installer-title">macOS Installer Downloads</h2>
      <div class="format-badges">
        <span class="format-badge ipsw">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"/>
          </svg>
          IPSW
        </span>
        <span class="format-badge pkg">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
          </svg>
          PKG
        </span>
      </div>
    </div>

    <div class="installer-info">
      <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
      </svg>
      <div>
        <strong>IPSW files</strong> are for Apple Silicon Macs (M1 and newer)
        <br>
        <strong>PKG files</strong> are Universal Mac Apps that work on all Macs
      </div>
    </div>

    <div class="table-wrapper">
      <table class="installer-table">
        <thead>
          <tr>
            <th class="title-col">
              <div class="th-content">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                </svg>
                macOS Version
              </div>
            </th>
            <th>Version</th>
            <th>Build</th>
            <th>Format</th>
            <th>Size</th>
            <th class="action-col">Download</th>
          </tr>
        </thead>
        <tbody>
          <!-- Latest Mac IPSW -->
          <tr v-if="latestMacIPSW" class="data-row featured">
            <td class="title-col">
              <div class="os-info">
                <span class="os-name">{{ latestMacIPSW.title }}</span>
                <span class="latest-badge">Latest</span>
              </div>
            </td>
            <td>
              <span class="version-text">{{ latestMacIPSW.version }}</span>
            </td>
            <td>
              <span class="build-badge">{{ latestMacIPSW.build }}</span>
            </td>
            <td>
              <span class="format-tag ipsw">IPSW</span>
            </td>
            <td>
              <span class="size-text">~13 GB</span>
            </td>
            <td class="action-col">
              <a :href="latestMacIPSW.url" target="_blank" class="download-btn primary">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"/>
                </svg>
                Download
              </a>
            </td>
          </tr>

          <!-- Latest UMA -->
          <tr v-if="latestUMA" class="data-row featured">
            <td class="title-col">
              <div class="os-info">
                <span class="os-name">{{ latestUMA.Title }}</span>
                <span class="latest-badge">Latest</span>
              </div>
            </td>
            <td>
              <span class="version-text">{{ latestUMA.Version }}</span>
            </td>
            <td>
              <span class="build-badge">{{ latestUMA.Build }}</span>
            </td>
            <td>
              <span class="format-tag pkg">PKG</span>
            </td>
            <td>
              <span class="size-text">~13 GB</span>
            </td>
            <td class="action-col">
              <a :href="latestUMA.URL" target="_blank" class="download-btn primary">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"/>
                </svg>
                Download
              </a>
            </td>
          </tr>

          <!-- Previous UMA Versions -->
          <tr v-for="(uma, index) in previousUMA" :key="index" class="data-row">
            <td class="title-col">
              <span class="os-name">{{ uma.Title }}</span>
            </td>
            <td>
              <span class="version-text">{{ uma.Version }}</span>
            </td>
            <td>
              <span class="build-badge">{{ uma.Build }}</span>
            </td>
            <td>
              <span class="format-tag pkg">PKG</span>
            </td>
            <td>
              <span class="size-text">~13 GB</span>
            </td>
            <td class="action-col">
              <a :href="uma.URL" target="_blank" class="download-btn">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"/>
                </svg>
                Download
              </a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Resource Links -->
    <div class="resource-section">
      <h3>Installation Resources</h3>
      <div class="resource-grid">
        <a href="https://support.apple.com/guide/mac-help/create-a-bootable-installer-mh27903/mac" target="_blank" class="resource-card">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V2"/>
          </svg>
          <div>
            <h4>Create Bootable Installer</h4>
            <p>Official guide for creating macOS installation media</p>
          </div>
        </a>
        <a href="https://mrmacintosh.com/apple-silicon-m1-full-macos-restore-ipsw-firmware-files-database/" target="_blank" class="resource-card">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"/>
          </svg>
          <div>
            <h4>IPSW Database</h4>
            <p>Complete archive of Apple Silicon restore images</p>
          </div>
        </a>
        <a href="https://dortania.github.io/OpenCore-Legacy-Patcher/" target="_blank" class="resource-card">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/>
          </svg>
          <div>
            <h4>Legacy Mac Support</h4>
            <p>Run newer macOS on unsupported Macs</p>
          </div>
        </a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

// Data will be loaded dynamically
let macOSData = {}


const latestUMA = ref(null)
const previousUMA = ref([])
const latestMacIPSW = ref(null)

const processData = () => {
  if (macOSData?.InstallationApps) {
    // Process Latest UMA
    latestUMA.value = macOSData.InstallationApps.LatestUMA || null
    
    // Process Previous UMA Versions (limit to 10 for display)
    previousUMA.value = (macOSData.InstallationApps.AllPreviousUMA || []).slice(0, 10)
    
    // Process Latest Mac IPSW
    if (macOSData.InstallationApps.LatestMacIPSW) {
      latestMacIPSW.value = {
        title: latestUMA.value?.Title || 'macOS Sequoia',
        version: macOSData.InstallationApps.LatestMacIPSW.MacOSIPSWVersion,
        build: macOSData.InstallationApps.LatestMacIPSW.MacOSIPSWBuild,
        url: macOSData.InstallationApps.LatestMacIPSW.MacOSIPSWURL
      }
    }
  }
}

onMounted(async () => {
  // Load data first
  try {
    const base = import.meta.env.BASE_URL || '/'
    const response = await fetch(`${base}v2/macos_data_feed.json`)
    macOSData = await response.json()
  } catch (e) {
    console.error('Failed to load installer data:', e)
  }
  processData()
})
</script>

<style scoped>
.installer-container {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 1.5rem;
}

.installer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.installer-title {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--vp-c-text-1);
  margin: 0;
}

.format-badges {
  display: flex;
  gap: 0.75rem;
}

.format-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
}

.format-badge.ipsw {
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
}

.format-badge.pkg {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.installer-info {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  background: rgba(59, 130, 246, 0.05);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 8px;
  margin-bottom: 1.5rem;
  color: var(--vp-c-text-2);
  font-size: 0.875rem;
  line-height: 1.5;
}

.installer-info svg {
  color: #3b82f6;
  flex-shrink: 0;
  margin-top: 2px;
}

.table-wrapper {
  overflow-x: auto;
  margin-bottom: 2rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  background: var(--vp-c-bg);
}

.installer-table {
  width: 100%;
  border-collapse: collapse;
}

.installer-table thead {
  background: var(--vp-c-bg-soft);
}

.installer-table th {
  padding: 0.875rem 1rem;
  text-align: left;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--vp-c-text-2);
  border-bottom: 1px solid var(--vp-c-divider);
}

.th-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.installer-table td {
  padding: 0.875rem 1rem;
  font-size: 0.875rem;
  color: var(--vp-c-text-1);
  border-bottom: 1px solid var(--vp-c-divider-light);
}

.data-row:hover {
  background: var(--vp-c-bg-soft);
}

.data-row.featured {
  background: linear-gradient(to right, rgba(59, 130, 246, 0.03), transparent);
}

.data-row:last-child td {
  border-bottom: none;
}

.os-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.os-name {
  font-weight: 500;
  color: var(--vp-c-text-1);
}

.latest-badge {
  padding: 0.125rem 0.5rem;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: white;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.version-text {
  font-weight: 500;
  font-family: monospace;
}

.build-badge {
  padding: 0.125rem 0.5rem;
  background: var(--vp-c-bg-mute);
  border-radius: 4px;
  font-size: 0.8125rem;
  font-family: monospace;
}

.format-tag {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.625rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.format-tag.ipsw {
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
}

.format-tag.pkg {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.size-text {
  color: var(--vp-c-text-3);
  font-size: 0.8125rem;
}

.download-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  color: var(--vp-c-text-1);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.download-btn:hover {
  background: var(--vp-c-brand);
  border-color: var(--vp-c-brand);
  color: white;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.download-btn.primary {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  border-color: transparent;
  color: white;
}

.download-btn.primary:hover {
  background: linear-gradient(135deg, #2563eb, #4f46e5);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
}

.resource-section {
  margin-top: 3rem;
  padding-top: 2rem;
  border-top: 1px solid var(--vp-c-divider);
}

.resource-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--vp-c-text-1);
  margin-bottom: 1rem;
}

.resource-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.resource-card {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  text-decoration: none;
  transition: all 0.2s ease;
}

.resource-card:hover {
  background: var(--vp-c-bg-mute);
  border-color: var(--vp-c-brand);
}

.resource-card svg {
  color: var(--vp-c-brand);
  flex-shrink: 0;
}

.resource-card h4 {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--vp-c-text-1);
  margin: 0 0 0.25rem 0;
}

.resource-card p {
  font-size: 0.8125rem;
  color: var(--vp-c-text-2);
  margin: 0;
  line-height: 1.4;
}

/* Responsive design */
@media (max-width: 768px) {
  .installer-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .table-wrapper {
    border-radius: 8px;
  }
  
  .installer-table {
    font-size: 0.8125rem;
  }
  
  .installer-table th,
  .installer-table td {
    padding: 0.625rem 0.5rem;
  }
  
  .action-col {
    min-width: 120px;
  }
  
  .resource-grid {
    grid-template-columns: 1fr;
  }
}

/* Dark mode enhancements */
:root.dark .table-wrapper {
  background: rgba(31, 41, 55, 0.3);
  border-color: rgba(55, 65, 81, 0.5);
}

:root.dark .installer-table thead {
  background: rgba(31, 41, 55, 0.5);
}

:root.dark .data-row:hover {
  background: rgba(31, 41, 55, 0.4);
}

:root.dark .data-row.featured {
  background: linear-gradient(to right, rgba(59, 130, 246, 0.08), transparent);
}

:root.dark .build-badge {
  background: rgba(55, 65, 81, 0.5);
}

:root.dark .download-btn {
  background: rgba(31, 41, 55, 0.5);
  border-color: rgba(55, 65, 81, 0.5);
}

:root.dark .download-btn:hover {
  background: var(--vp-c-brand);
  border-color: var(--vp-c-brand);
}

:root.dark .resource-card {
  background: rgba(31, 41, 55, 0.3);
  border-color: rgba(55, 65, 81, 0.5);
}

:root.dark .resource-card:hover {
  background: rgba(31, 41, 55, 0.5);
}

:root.dark .installer-info {
  background: rgba(59, 130, 246, 0.08);
  border-color: rgba(59, 130, 246, 0.3);
}
</style>