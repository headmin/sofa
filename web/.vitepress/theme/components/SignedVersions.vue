<script setup>
import { ref, computed, onMounted, watch } from 'vue'

const platforms = [
  { id: 'macos', label: 'macOS', feed: 'v2/macos_data_feed.json' },
  { id: 'ios', label: 'iOS / iPadOS', feed: 'v2/ios_data_feed.json' },
  { id: 'tvos', label: 'tvOS', feed: 'v2/tvos_data_feed.json' },
  { id: 'watchos', label: 'watchOS', feed: 'v2/watchos_data_feed.json' },
  { id: 'visionos', label: 'visionOS', feed: 'v2/visionos_data_feed.json' },
]

const selectedPlatform = ref('macos')
const feedData = ref(null)
const loading = ref(false)
const expandedDevices = ref({}) // osVersion → bool

const fetchFeed = async (platformId) => {
  loading.value = true
  const platform = platforms.find(p => p.id === platformId)
  if (!platform) return
  try {
    const base = import.meta.env.BASE_URL || '/'
    const res = await fetch(`${base}${platform.feed}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    feedData.value = await res.json()
  } catch (e) {
    console.error('Failed to load feed:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => fetchFeed(selectedPlatform.value))
watch(selectedPlatform, (id) => {
  expandedDevices.value = {}
  feedData.value = null
  fetchFeed(id)
})

const versions = computed(() => {
  if (!feedData.value?.OSVersions) return []
  const devices = feedData.value.Devices ?? {}

  return feedData.value.OSVersions.map(osv => {
    const latest = osv.Latest ?? {}
    const supported = (latest.SupportedDevices ?? []).map(code => {
      const d = devices[code]
      return d?.MarketingName ?? d?.DeviceID ?? code
    }).sort()

    const kevCount = latest.ActivelyExploitedCVEs?.length ?? 0

    return {
      osVersion: osv.OSVersion,
      productVersion: latest.ProductVersion ?? '—',
      build: latest.Build ?? '—',
      releaseDate: latest.ReleaseDate ?? '',
      cveCount: latest.UniqueCVEsCount ?? 0,
      kevCount,
      expiration: latest.ExpirationDate ?? '',
      deviceCount: (latest.SupportedDevices ?? []).length,
      deviceNames: supported,
      summary: latest.UpdateSummary ?? null,
    }
  })
})

function formatDate(dateString) {
  if (!dateString) return '—'
  try {
    const d = new Date(dateString)
    return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(d)
  } catch { return dateString }
}

function daysUntil(dateString) {
  if (!dateString) return null
  const diff = Math.ceil((new Date(dateString) - new Date()) / (1000 * 60 * 60 * 24))
  return diff > 0 ? diff : null
}

function toggleDevices(osVersion) {
  expandedDevices.value[osVersion] = !expandedDevices.value[osVersion]
}
</script>

<template>
  <div class="signed-versions">
    <!-- Platform tabs -->
    <div class="platform-tabs">
      <button
        v-for="p in platforms"
        :key="p.id"
        class="tab-btn"
        :class="{ active: selectedPlatform === p.id }"
        @click="selectedPlatform = p.id"
      >
        {{ p.label }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      Loading...
    </div>

    <!-- Version cards -->
    <div v-else class="version-list">
      <div v-for="v in versions" :key="v.osVersion" class="version-card">
        <!-- Header -->
        <div class="card-header">
          <div class="version-title">
            <h3>{{ v.osVersion }}</h3>
            <span class="version-badge">{{ v.productVersion }}</span>
            <span v-if="v.kevCount > 0" class="kev-badge">{{ v.kevCount }} Actively Exploited</span>
          </div>
          <div class="signing-status">
            <span class="signed-badge">Signed</span>
            <span v-if="daysUntil(v.expiration)" class="expiry-note">
              expires in {{ daysUntil(v.expiration) }} days
            </span>
          </div>
        </div>

        <!-- Details grid -->
        <div class="details-grid">
          <div class="detail">
            <span class="detail-label">Build</span>
            <span class="detail-value mono">{{ v.build }}</span>
          </div>
          <div class="detail">
            <span class="detail-label">Released</span>
            <span class="detail-value">{{ formatDate(v.releaseDate) }}</span>
          </div>
          <div class="detail">
            <span class="detail-label">CVEs Fixed</span>
            <span class="detail-value" :class="{ 'has-cves': v.cveCount > 0 }">{{ v.cveCount }}</span>
          </div>
          <div class="detail">
            <span class="detail-label">Supported Devices</span>
            <span class="detail-value">{{ v.deviceCount }}</span>
          </div>
        </div>

        <!-- Update summary -->
        <div v-if="v.summary?.Summary" class="summary-section">
          <p class="summary-text">{{ v.summary.Summary }}</p>
          <p v-if="v.summary.Recommendation" class="recommendation">
            <strong>Recommendation:</strong> {{ v.summary.Recommendation }}
          </p>
        </div>

        <!-- Device list (expandable) -->
        <div class="devices-section">
          <button class="devices-toggle" @click="toggleDevices(v.osVersion)">
            {{ expandedDevices[v.osVersion] ? 'Hide' : 'Show' }} supported devices ({{ v.deviceCount }})
          </button>
          <div v-if="expandedDevices[v.osVersion]" class="device-list">
            <span v-for="name in v.deviceNames" :key="name" class="device-chip">
              {{ name }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.signed-versions {
  max-width: 900px;
  margin: 0 auto;
}

.platform-tabs {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
  margin-bottom: 1.5rem;
}

.tab-btn {
  padding: 0.5rem 1rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  background: var(--vp-c-bg-soft);
  color: var(--vp-c-text-2);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.tab-btn:hover { background: var(--vp-c-bg-mute); color: var(--vp-c-text-1); }

.tab-btn.active {
  background: var(--vp-c-brand);
  border-color: var(--vp-c-brand);
  color: white;
}

.loading {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 2rem;
  color: var(--vp-c-text-2);
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--vp-c-divider);
  border-top-color: var(--vp-c-brand);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.version-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.version-card {
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  padding: 1.25rem;
  background: var(--vp-c-bg);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.version-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.version-title h3 {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--vp-c-text-1);
}

.version-badge {
  padding: 0.125rem 0.5rem;
  background: var(--vp-c-brand);
  color: white;
  border-radius: 9999px;
  font-size: 0.8125rem;
  font-weight: 600;
  font-family: monospace;
}

.kev-badge {
  padding: 0.125rem 0.5rem;
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.signing-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.signed-badge {
  padding: 0.125rem 0.5rem;
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.expiry-note {
  font-size: 0.75rem;
  color: var(--vp-c-text-3);
}

.details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.detail {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.detail-label {
  font-size: 0.6875rem;
  color: var(--vp-c-text-3);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.detail-value {
  font-size: 0.9375rem;
  color: var(--vp-c-text-1);
  font-weight: 500;
}

.detail-value.mono { font-family: monospace; }

.detail-value.has-cves { color: var(--vp-c-brand); }

.summary-section {
  padding: 0.75rem;
  background: var(--vp-c-bg-soft);
  border-radius: 8px;
  margin-bottom: 1rem;
}

.summary-text {
  font-size: 0.875rem;
  color: var(--vp-c-text-2);
  margin: 0 0 0.25rem 0;
}

.recommendation {
  font-size: 0.8125rem;
  color: var(--vp-c-text-3);
  margin: 0;
}

.devices-section {
  border-top: 1px solid var(--vp-c-divider-light);
  padding-top: 0.75rem;
}

.devices-toggle {
  background: none;
  border: none;
  color: var(--vp-c-brand);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  padding: 0;
}

.devices-toggle:hover { text-decoration: underline; }

.device-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  margin-top: 0.75rem;
}

.device-chip {
  padding: 0.25rem 0.625rem;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 6px;
  font-size: 0.75rem;
  color: var(--vp-c-text-2);
}

/* Dark mode */
:root.dark .kev-badge {
  background: rgba(220, 38, 38, 0.1);
  border-color: rgba(220, 38, 38, 0.3);
}

:root.dark .signed-badge {
  background: rgba(22, 163, 74, 0.1);
  border-color: rgba(22, 163, 74, 0.3);
}

:root.dark .version-card {
  background: rgba(31, 41, 55, 0.3);
  border-color: rgba(55, 65, 81, 0.5);
}

@media (max-width: 768px) {
  .details-grid {
    grid-template-columns: 1fr 1fr;
  }
  .card-header {
    flex-direction: column;
  }
}
</style>
