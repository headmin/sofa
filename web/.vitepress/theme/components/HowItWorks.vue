<template>
  <div class="how-it-works-container">
    <!-- Header -->
    <div class="header-section">
      <h1 class="title">How SOFA Works</h1>
      <p class="subtitle">Real-time pipeline status and data flow visualization</p>
      
      <!-- Live Status Badge -->
      <div class="status-badge" :class="overallStatus.color">
        <component :is="overallStatus.icon" class="status-icon" />
        <span>{{ overallStatus.label }}</span>
        <span class="pulse" v-if="overallStatus.label === 'Live'"></span>
      </div>
    </div>

    <!-- Pipeline Flow Visualization -->
    <div class="pipeline-flow">
      <!-- Stage 1: Trigger -->
      <div class="pipeline-stage" :class="{ active: currentStage >= 1, complete: stageStatus.trigger }">
        <div class="stage-icon">
          <component :is="ClockIcon" />
        </div>
        <div class="stage-content">
          <h3>Schedule Trigger</h3>
          <p class="stage-description">Every 6 hours via GitHub Actions</p>
          <div class="stage-meta">
            <span class="next-run">Next run: {{ nextRun }}</span>
          </div>
        </div>
        <div class="stage-arrow">→</div>
      </div>

      <!-- Stage 2: Gather -->
      <div class="pipeline-stage" :class="{ active: currentStage >= 2, complete: stageStatus.gather }">
        <div class="stage-icon">
          <component :is="DownloadIcon" />
        </div>
        <div class="stage-content">
          <h3>Gather Data</h3>
          <p class="stage-description">Fetch from Apple APIs</p>
          <div class="stage-sources">
            <span v-for="source in dataSources" :key="source.name" 
                  class="source-badge" 
                  :class="source.status"
                  @click="openLink(source.url)"
                  :title="source.description">
              {{ source.name }}
            </span>
          </div>
        </div>
        <div class="stage-arrow">→</div>
      </div>

      <!-- Stage 3: Process -->
      <div class="pipeline-stage" :class="{ active: currentStage >= 3, complete: stageStatus.process }">
        <div class="stage-icon">
          <component :is="CpuIcon" />
        </div>
        <div class="stage-content">
          <h3>Process & Enrich</h3>
          <p class="stage-description">CVE analysis & security data</p>
          <div class="stage-stats">
            <span>{{ processStats.cves }} CVEs</span>
            <span>{{ processStats.releases }} Releases</span>
          </div>
        </div>
        <div class="stage-arrow">→</div>
      </div>

      <!-- Stage 4: Build -->
      <div class="pipeline-stage" :class="{ active: currentStage >= 4, complete: stageStatus.build }">
        <div class="stage-icon">
          <component :is="PackageIcon" />
        </div>
        <div class="stage-content">
          <h3>Build Feeds</h3>
          <p class="stage-description">Generate JSON & RSS feeds</p>
          <div class="stage-outputs">
            <button v-for="feed in feedOutputs" :key="feed.name"
                    @click="openLink(feed.url)"
                    class="feed-link"
                    :class="{ updated: feed.recent }">
              <component :is="FileJsonIcon" class="feed-icon" />
              <span>{{ feed.name }}</span>
              <span class="feed-time">{{ feed.time }}</span>
            </button>
          </div>
        </div>
        <div class="stage-arrow">→</div>
      </div>

      <!-- Stage 5: Deploy -->
      <div class="pipeline-stage" :class="{ active: currentStage >= 5, complete: stageStatus.deploy }">
        <div class="stage-icon">
          <component :is="RocketIcon" />
        </div>
        <div class="stage-content">
          <h3>Deploy & Update</h3>
          <p class="stage-description">Push to dashboard</p>
          <div class="stage-result">
            <span class="deploy-status" :class="deployStatus">
              {{ deployMessage }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Data Files Section -->
    <div class="data-files-section">
      <h2>Live Data Files</h2>
      <div class="files-grid">
        <!-- V2 Feeds -->
        <div class="file-group">
          <h3>
            <component :is="FolderIcon" class="group-icon" />
            V2 Feeds (Current)
          </h3>
          <div class="file-list">
            <a v-for="file in v2Files" :key="file.path"
               :href="getFileUrl(file.path)"
               target="_blank"
               class="file-item"
               :class="{ fresh: file.fresh }">
              <component :is="FileIcon" class="file-icon" />
              <div class="file-info">
                <span class="file-name">{{ file.name }}</span>
                <span class="file-meta">
                  <span class="file-size">{{ file.size }}</span>
                  <span class="file-time">{{ file.lastUpdate }}</span>
                  <span v-if="file.fresh" class="fresh-badge">Fresh</span>
                </span>
              </div>
              <component :is="ExternalLinkIcon" class="link-icon" />
            </a>
          </div>
        </div>

        <!-- V1 Feeds -->
        <div class="file-group">
          <h3>
            <component :is="FolderIcon" class="group-icon" />
            V1 Feeds (Legacy)
          </h3>
          <div class="file-list">
            <a v-for="file in v1Files" :key="file.path"
               :href="getFileUrl(file.path)"
               target="_blank"
               class="file-item">
              <component :is="FileIcon" class="file-icon" />
              <div class="file-info">
                <span class="file-name">{{ file.name }}</span>
                <span class="file-meta">
                  <span class="file-size">{{ file.size }}</span>
                  <span class="file-time">{{ file.lastUpdate }}</span>
                </span>
              </div>
              <component :is="ExternalLinkIcon" class="link-icon" />
            </a>
          </div>
        </div>

        <!-- Metadata Files -->
        <div class="file-group">
          <h3>
            <component :is="SettingsIcon" class="group-icon" />
            Metadata & Config
          </h3>
          <div class="file-list">
            <a v-for="file in metaFiles" :key="file.path"
               :href="getFileUrl(file.path)"
               target="_blank"
               class="file-item"
               :class="{ highlight: file.important }">
              <component :is="FileIcon" class="file-icon" />
              <div class="file-info">
                <span class="file-name">{{ file.name }}</span>
                <span class="file-meta">
                  <span class="file-size">{{ file.size }}</span>
                  <span class="file-time">{{ file.lastUpdate }}</span>
                  <span v-if="file.important" class="important-badge">Key</span>
                </span>
              </div>
              <component :is="ExternalLinkIcon" class="link-icon" />
            </a>
          </div>
        </div>
      </div>
    </div>

    <!-- Statistics Section -->
    <div class="stats-section">
      <h2>Pipeline Statistics</h2>
      <div class="stats-grid">
        <div class="stat-card">
          <component :is="ActivityIcon" class="stat-icon" />
          <div class="stat-value">{{ stats.runsToday }}</div>
          <div class="stat-label">Runs Today</div>
        </div>
        <div class="stat-card">
          <component :is="CheckCircleIcon" class="stat-icon success" />
          <div class="stat-value">{{ stats.successRate }}%</div>
          <div class="stat-label">Success Rate</div>
        </div>
        <div class="stat-card">
          <component :is="ClockIcon" class="stat-icon" />
          <div class="stat-value">{{ stats.avgDuration }}</div>
          <div class="stat-label">Avg Duration</div>
        </div>
        <div class="stat-card">
          <component :is="DatabaseIcon" class="stat-icon" />
          <div class="stat-value">{{ stats.totalSize }}</div>
          <div class="stat-label">Total Data</div>
        </div>
      </div>
    </div>

    <!-- Last Run Details -->
    <div class="last-run-section">
      <h2>Last Pipeline Run</h2>
      <div class="run-details">
        <div class="run-header">
          <span class="run-status" :class="lastRun.status">
            <component :is="lastRun.icon" class="run-icon" />
            {{ lastRun.statusText }}
          </span>
          <span class="run-time">{{ lastRun.timestamp }}</span>
        </div>
        <div class="run-log">
          <div v-for="(log, idx) in lastRun.logs" :key="idx" class="log-entry" :class="log.level">
            <span class="log-time">{{ log.time }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
        <div class="run-footer">
          <a :href="lastRun.actionUrl" target="_blank" class="action-link">
            View in GitHub Actions →
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  Clock as ClockIcon,
  Download as DownloadIcon,
  Cpu as CpuIcon,
  Package as PackageIcon,
  Rocket as RocketIcon,
  FileJson as FileJsonIcon,
  File as FileIcon,
  Folder as FolderIcon,
  Settings as SettingsIcon,
  ExternalLink as ExternalLinkIcon,
  Activity as ActivityIcon,
  CheckCircle as CheckCircleIcon,
  Database as DatabaseIcon,
  AlertCircle as AlertCircleIcon,
  XCircle as XCircleIcon
} from 'lucide-vue-next'

// Reactive data
const currentStage = ref(0)
const lastCheckTime = ref<Date>(new Date())
const feedData = ref<any>({})
const refreshInterval = ref<number | null>(null)

// Load feed metadata
const loadFeedData = async () => {
  try {
    const base = import.meta.env.BASE_URL || '/'
    const response = await fetch(`${base}data/feeds/v2/feed_metadata.json`)
    if (response.ok) {
      feedData.value = await response.json()
      updateFileTimestamps()
    }
  } catch (error) {
    console.error('Failed to load feed metadata:', error)
  }
}

// Update file timestamps from metadata
const updateFileTimestamps = () => {
  if (feedData.value.feeds) {
    lastCheckTime.value = new Date(feedData.value.generated || new Date())
  }
}

// Calculate time-based properties
const nextRun = computed(() => {
  const now = new Date()
  const nextRunTime = new Date(now)
  const hours = now.getUTCHours()
  const nextHour = Math.ceil(hours / 6) * 6
  nextRunTime.setUTCHours(nextHour % 24, 0, 0, 0)
  if (nextHour >= 24) {
    nextRunTime.setUTCDate(nextRunTime.getUTCDate() + 1)
  }
  
  const diff = nextRunTime.getTime() - now.getTime()
  const hoursLeft = Math.floor(diff / (1000 * 60 * 60))
  const minutesLeft = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  
  return `${hoursLeft}h ${minutesLeft}m`
})

const overallStatus = computed(() => {
  const now = new Date()
  const lastCheck = new Date(feedData.value.generated || 0)
  const hoursSince = (now.getTime() - lastCheck.getTime()) / (1000 * 60 * 60)
  
  if (hoursSince < 1) {
    return { label: 'Live', color: 'status-live', icon: CheckCircleIcon }
  } else if (hoursSince < 24) {
    return { label: 'Recent', color: 'status-recent', icon: AlertCircleIcon }
  } else {
    return { label: 'Stale', color: 'status-stale', icon: XCircleIcon }
  }
})

// Stage status
const stageStatus = ref({
  trigger: true,
  gather: true,
  process: true,
  build: true,
  deploy: true
})

// Data sources
const dataSources = ref([
  { name: 'GDMF', status: 'active', url: '#', description: 'macOS version catalog' },
  { name: 'IPSW', status: 'active', url: '#', description: 'iOS firmware data' },
  { name: 'KEV', status: 'active', url: '#', description: 'Known vulnerabilities' },
  { name: 'XProtect', status: 'active', url: '#', description: 'Security definitions' },
  { name: 'Beta', status: 'partial', url: '#', description: 'Beta releases' },
])

// Process statistics
const processStats = ref({
  cves: '2,451',
  releases: '847'
})

// Feed outputs with live data
const feedOutputs = computed(() => {
  const feeds = []
  if (feedData.value.feeds) {
    Object.entries(feedData.value.feeds).forEach(([platform, data]: [string, any]) => {
      feeds.push({
        name: `${platform}.json`,
        url: `/data/feeds/v2/${platform}_data_feed.json`,
        time: formatTime(data.last_check),
        recent: isRecent(data.last_check)
      })
    })
  }
  return feeds
})

// File lists
const v2Files = computed(() => {
  const files = []
  if (feedData.value.feeds) {
    Object.entries(feedData.value.feeds).forEach(([platform, data]: [string, any]) => {
      files.push({
        name: `${platform}_data_feed.json`,
        path: `/data/feeds/v2/${platform}_data_feed.json`,
        size: '~250KB',
        lastUpdate: formatTime(data.last_check),
        fresh: isRecent(data.last_check)
      })
    })
  }
  // Add metadata files
  files.push({
    name: 'feed_metadata.json',
    path: '/data/feeds/v2/feed_metadata.json',
    size: '2KB',
    lastUpdate: formatTime(feedData.value.generated),
    fresh: true
  })
  return files
})

const v1Files = ref([
  { name: 'macos_data_feed.json', path: '/data/feeds/v1/macos_data_feed.json', size: '180KB', lastUpdate: '5 min ago' },
  { name: 'ios_data_feed.json', path: '/data/feeds/v1/ios_data_feed.json', size: '165KB', lastUpdate: '5 min ago' },
  { name: 'rss_feed.xml', path: '/v1/rss_feed.xml', size: '45KB', lastUpdate: '5 min ago' }
])

const metaFiles = ref([
  { name: 'last_feed_timestamp.json', path: '/data/feeds/v2/last_feed_timestamp.json', size: '1KB', lastUpdate: '5 min ago', important: true },
  { name: 'bulletin_data.json', path: '/data/resources/bulletin_data.json', size: '12KB', lastUpdate: '5 min ago', important: true },
  { name: 'sofa-feeds.yml', path: '/.github/workflows/sofa-feeds.yml', size: '8KB', lastUpdate: '1 day ago' }
])

// Statistics
const stats = ref({
  runsToday: 3,
  successRate: 98.5,
  avgDuration: '6m 32s',
  totalSize: '4.2MB'
})

// Deployment status
const deployStatus = computed(() => overallStatus.value.label === 'Live' ? 'success' : 'pending')
const deployMessage = computed(() => overallStatus.value.label === 'Live' ? 'Dashboard Updated' : 'Waiting for next run')

// Last run details
const lastRun = ref({
  status: 'success',
  statusText: 'Completed Successfully',
  icon: CheckCircleIcon,
  timestamp: formatTime(feedData.value.generated),
  actionUrl: 'https://github.com/macadmins/sofa/actions',
  logs: [
    { time: '12:00:01', message: 'Pipeline started', level: 'info' },
    { time: '12:00:15', message: 'Gathering data from 6 sources', level: 'info' },
    { time: '12:01:32', message: 'Processing 2,451 CVE entries', level: 'info' },
    { time: '12:03:45', message: 'Building v2 feeds for 6 platforms', level: 'info' },
    { time: '12:05:12', message: 'Deploying to dashboard', level: 'info' },
    { time: '12:05:28', message: 'Pipeline completed successfully', level: 'success' }
  ]
})

// Helper functions
const formatTime = (timestamp: string | Date | undefined) => {
  if (!timestamp) return 'Never'
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  return date.toLocaleDateString()
}

const isRecent = (timestamp: string | undefined) => {
  if (!timestamp) return false
  const date = new Date(timestamp)
  const now = new Date()
  const hoursSince = (now.getTime() - date.getTime()) / (1000 * 60 * 60)
  return hoursSince < 1
}

const getFileUrl = (path: string) => {
  const base = import.meta.env.BASE_URL || '/'
  return `${base}${path}`.replace('//', '/')
}

const openLink = (url: string) => {
  if (url !== '#') {
    window.open(getFileUrl(url), '_blank')
  }
}

// Simulate pipeline animation
const animatePipeline = () => {
  let stage = 1
  const animate = () => {
    currentStage.value = stage
    stage++
    if (stage > 5) {
      stage = 0
      setTimeout(() => {
        currentStage.value = 0
      }, 2000)
    }
  }
  
  // Run animation every 3 seconds
  return setInterval(animate, 3000)
}

// Lifecycle
onMounted(() => {
  loadFeedData()
  // Refresh data every 30 seconds
  refreshInterval.value = setInterval(loadFeedData, 30000)
  // Start pipeline animation
  const animationInterval = animatePipeline()
  
  onUnmounted(() => {
    if (refreshInterval.value) clearInterval(refreshInterval.value)
    clearInterval(animationInterval)
  })
})
</script>

<style scoped>
.how-it-works-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

/* Header */
.header-section {
  text-align: center;
  margin-bottom: 3rem;
}

.title {
  font-size: 2.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: var(--vp-c-text-2);
  font-size: 1.125rem;
  margin-bottom: 1.5rem;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 2rem;
  font-weight: 600;
  position: relative;
}

.status-live {
  background: #10b981;
  color: white;
}

.status-recent {
  background: #f59e0b;
  color: white;
}

.status-stale {
  background: #ef4444;
  color: white;
}

.status-icon {
  width: 1.25rem;
  height: 1.25rem;
}

.pulse {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  height: 100%;
  border-radius: 2rem;
  background: inherit;
  opacity: 0.5;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 0.5;
  }
  100% {
    transform: translate(-50%, -50%) scale(1.5);
    opacity: 0;
  }
}

/* Pipeline Flow */
.pipeline-flow {
  display: flex;
  gap: 0;
  margin-bottom: 3rem;
  overflow-x: auto;
  padding: 2rem 0;
  background: var(--vp-c-bg-soft);
  border-radius: 1rem;
}

.pipeline-stage {
  flex: 1;
  min-width: 200px;
  padding: 1.5rem;
  position: relative;
  opacity: 0.5;
  transition: all 0.3s;
}

.pipeline-stage.active {
  opacity: 1;
}

.pipeline-stage.complete {
  opacity: 1;
}

.stage-icon {
  width: 3rem;
  height: 3rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-bottom: 1rem;
}

.stage-icon svg {
  width: 1.5rem;
  height: 1.5rem;
}

.stage-content h3 {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.stage-description {
  color: var(--vp-c-text-2);
  font-size: 0.875rem;
  margin-bottom: 0.75rem;
}

.stage-arrow {
  position: absolute;
  right: -1rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1.5rem;
  color: var(--vp-c-text-3);
}

.pipeline-stage:last-child .stage-arrow {
  display: none;
}

/* Data sources badges */
.stage-sources {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.source-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}

.source-badge:hover {
  transform: scale(1.05);
}

.source-badge.active {
  background: #10b981;
  color: white;
}

.source-badge.partial {
  background: #f59e0b;
  color: white;
}

/* Feed outputs */
.stage-outputs {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.feed-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-border);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.feed-link:hover {
  border-color: var(--vp-c-brand);
  transform: translateX(2px);
}

.feed-link.updated {
  border-color: #10b981;
  background: #10b98110;
}

.feed-icon {
  width: 1rem;
  height: 1rem;
  color: var(--vp-c-brand);
}

.feed-time {
  margin-left: auto;
  color: var(--vp-c-text-2);
  font-size: 0.75rem;
}

/* Data Files Section */
.data-files-section {
  margin-bottom: 3rem;
}

.data-files-section h2 {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
}

.files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 1.5rem;
}

.file-group {
  background: var(--vp-c-bg-soft);
  border-radius: 1rem;
  padding: 1.5rem;
}

.file-group h3 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.group-icon {
  width: 1.25rem;
  height: 1.25rem;
  color: var(--vp-c-brand);
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-border);
  border-radius: 0.5rem;
  text-decoration: none;
  color: inherit;
  transition: all 0.2s;
}

.file-item:hover {
  border-color: var(--vp-c-brand);
  transform: translateX(2px);
}

.file-item.fresh {
  border-color: #10b981;
}

.file-item.highlight {
  border-color: var(--vp-c-brand);
  background: var(--vp-c-brand-soft);
}

.file-icon {
  width: 1.25rem;
  height: 1.25rem;
  color: var(--vp-c-text-2);
}

.file-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.file-name {
  font-weight: 500;
}

.file-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.75rem;
  color: var(--vp-c-text-2);
}

.fresh-badge {
  padding: 0.125rem 0.375rem;
  background: #10b981;
  color: white;
  border-radius: 0.25rem;
  font-weight: 600;
}

.important-badge {
  padding: 0.125rem 0.375rem;
  background: var(--vp-c-brand);
  color: white;
  border-radius: 0.25rem;
  font-weight: 600;
}

.link-icon {
  width: 1rem;
  height: 1rem;
  color: var(--vp-c-text-3);
}

/* Statistics Section */
.stats-section {
  margin-bottom: 3rem;
}

.stats-section h2 {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  background: var(--vp-c-bg-soft);
  border-radius: 1rem;
  padding: 1.5rem;
  text-align: center;
}

.stat-icon {
  width: 2.5rem;
  height: 2.5rem;
  margin: 0 auto 0.75rem;
  color: var(--vp-c-brand);
}

.stat-icon.success {
  color: #10b981;
}

.stat-value {
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 0.25rem;
}

.stat-label {
  color: var(--vp-c-text-2);
  font-size: 0.875rem;
}

/* Last Run Section */
.last-run-section {
  margin-bottom: 3rem;
}

.last-run-section h2 {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
}

.run-details {
  background: var(--vp-c-bg-soft);
  border-radius: 1rem;
  overflow: hidden;
}

.run-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: var(--vp-c-bg);
  border-bottom: 1px solid var(--vp-c-border);
}

.run-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
}

.run-status.success {
  color: #10b981;
}

.run-icon {
  width: 1.25rem;
  height: 1.25rem;
}

.run-time {
  color: var(--vp-c-text-2);
  font-size: 0.875rem;
}

.run-log {
  padding: 1rem;
  max-height: 300px;
  overflow-y: auto;
  font-family: monospace;
  font-size: 0.875rem;
}

.log-entry {
  display: flex;
  gap: 1rem;
  padding: 0.25rem 0;
}

.log-entry.success {
  color: #10b981;
}

.log-entry.error {
  color: #ef4444;
}

.log-time {
  color: var(--vp-c-text-3);
  min-width: 80px;
}

.run-footer {
  padding: 1rem 1.5rem;
  background: var(--vp-c-bg);
  border-top: 1px solid var(--vp-c-border);
}

.action-link {
  color: var(--vp-c-brand);
  text-decoration: none;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.action-link:hover {
  text-decoration: underline;
}

/* Dark mode adjustments */
.dark .pipeline-stage {
  background: rgba(255, 255, 255, 0.02);
}

.dark .status-badge {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

/* Responsive */
@media (max-width: 768px) {
  .pipeline-flow {
    flex-direction: column;
  }
  
  .stage-arrow {
    display: none;
  }
  
  .files-grid {
    grid-template-columns: 1fr;
  }
}
</style>