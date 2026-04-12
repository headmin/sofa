<script setup>
import { ref, computed, watch, onMounted } from 'vue'

// Layout constants
const LANE_WIDTH = 60
const ROW_HEIGHT = 100
const NODE_RADIUS = 8
const SVG_LEFT_PADDING = 40
const SVG_TOP_PADDING = 30
const RIGHT_LABEL_WIDTH = 500

const platforms = [
  { id: 'macos', label: 'macOS', feed: 'v2/macos_data_feed.json' },
  { id: 'ios', label: 'iOS', feed: 'v2/ios_data_feed.json' },
  { id: 'tvos', label: 'tvOS', feed: 'v2/tvos_data_feed.json' },
  { id: 'watchos', label: 'watchOS', feed: 'v2/watchos_data_feed.json' },
  { id: 'visionos', label: 'visionOS', feed: 'v2/visionos_data_feed.json' },
]

const selectedPlatform = ref('macos')
const selectedOSVersion = ref(null)
const feedData = ref(null)
const loading = ref(false)
const error = ref(null)
const expandedVersion = ref(null)
const hoveredVersion = ref(null)

// Fetch feed data
const fetchFeed = async (platformId) => {
  loading.value = true
  error.value = null
  const platform = platforms.find(p => p.id === platformId)
  if (!platform) return

  try {
    const base = import.meta.env.BASE_URL || '/'
    const res = await fetch(`${base}${platform.feed}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    feedData.value = await res.json()
    // Auto-select first OS version
    if (feedData.value?.OSVersions?.length) {
      selectedOSVersion.value = feedData.value.OSVersions[0].OSVersion
    }
  } catch (e) {
    error.value = e
    console.error('Failed to load feed:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => fetchFeed(selectedPlatform.value))
watch(selectedPlatform, (id) => {
  expandedVersion.value = null
  fetchFeed(id)
})

// Available OS versions for the filter
const availableOSVersions = computed(() => {
  if (!feedData.value?.OSVersions) return []
  return feedData.value.OSVersions.map(osv => osv.OSVersion)
})

// Build the graph from feed data
const graphGroups = computed(() => {
  if (!feedData.value) return []
  try {
  const data = feedData.value
  const devices = data.Devices ?? {}

  return data.OSVersions
    .filter(osv => !selectedOSVersion.value || osv.OSVersion === selectedOSVersion.value)
    .map(osv => {
      // Extract major version for BSI lookup
      const parts = osv.OSVersion.split(' ')
      const majorVersion = parts[parts.length - 1]
      const bsiList = data.BackgroundSecurityImprovements?.[majorVersion] ?? []

      // Deduplicate releases by ProductVersion + Build
      const seen = new Set()
      const uniqueReleases = osv.SecurityReleases.filter(sr => {
        const key = `${sr.ProductVersion}-${sr.Build}`
        if (seen.has(key)) return false
        seen.add(key)
        return true
      })

      // Build unified list: releases + BSIs, each with a normalized date
      const releaseItems = uniqueReleases.map(sr => ({
        type: 'release',
        sortDate: new Date(sr.ReleaseDate).getTime(),
        data: sr,
      }))

      const bsiItems = bsiList.map(bsi => ({
        type: 'bsi',
        sortDate: new Date(bsi.PostingDate).getTime(),
        data: bsi,
      }))

      // Merge and sort reverse-chronologically (latest on top)
      const allItems = [...releaseItems, ...bsiItems]
        .sort((a, b) => b.sortDate - a.sortDate)

      // Assign lanes — track active branch slots
      const activeBranches = []

      const nodes = allItems.map((item, rowIndex) => {
        if (item.type === 'bsi') {
          const bsi = item.data
          const bsiScope = bsi.DeviceScope || 'universal'

          // BSIs sit on trunk (lane 0) — they're OS-wide patches
          return {
            type: 'bsi',
            version: `${bsi.Version}${bsi.VersionExtra || ''}`,
            build: bsi.Build,
            releaseDate: bsi.PostingDate,
            scope: bsiScope,
            supportedDevices: bsi.SupportedDevices ?? [],
            deviceNames: [],
            deviceCount: 0,
            supersededBy: bsi.SupersededBy?.ProductVersion ?? null,
            mergedInto: null,
            daysLater: bsi.SupersededBy?.DaysLater ?? null,
            cveCount: (bsi.CVEs ?? []).length,
            cveList: bsi.CVEs ?? [],
            activelyExploitedCount: 0,
            securityInfo: bsi.SecurityInfo ?? null,
            updateSummary: null,
            patchesRelease: bsi.PatchesRelease?.ProductVersion ?? null,
            osVersion: osv.OSVersion,
            lane: 0,
            branchesFrom: null,
            rowIndex,
            cx: SVG_LEFT_PADDING,
            cy: SVG_TOP_PADDING + rowIndex * ROW_HEIGHT,
          }
        }

        // Regular release
        const sr = item.data
        let lane = 0
        let branchesFrom = null

        if (sr.DeviceScope === 'device-specific') {
          const now = sr.ReleaseDate
          const mergeDate = sr.MergedInto?.ReleaseDate ?? sr.SupersededBy?.ReleaseDate ?? now
          const freeSlot = activeBranches.findIndex(b => b.endsAt <= now)

          if (freeSlot >= 0) {
            lane = activeBranches[freeSlot].slot
            activeBranches[freeSlot].endsAt = mergeDate
          } else {
            lane = activeBranches.length + 1
            activeBranches.push({ slot: lane, endsAt: mergeDate })
          }

          // Find the nearest universal release before this one by date
          const releases = allItems.filter(i => i.type === 'release')
          const preceding = releases
            .filter(i => i.data.DeviceScope === 'universal' && new Date(i.data.ReleaseDate).getTime() <= new Date(sr.ReleaseDate).getTime())
            .sort((a, b) => b.sortDate - a.sortDate)
          branchesFrom = preceding.length ? preceding[0].data.ProductVersion : null
        }

        // Resolve device names
        const deviceNames = (sr.SupportedDevices ?? []).slice(0, 5).map(code => {
          const d = devices[code]
          return d?.MarketingName ?? d?.DeviceID ?? code
        })

        return {
          type: 'release',
          version: sr.ProductVersion,
          build: sr.Build,
          releaseDate: sr.ReleaseDate,
          scope: sr.DeviceScope || 'universal',
          supportedDevices: sr.SupportedDevices ?? [],
          deviceNames,
          deviceCount: (sr.SupportedDevices ?? []).length,
          supersededBy: sr.SupersededBy?.ProductVersion ?? null,
          mergedInto: sr.MergedInto?.ProductVersion ?? null,
          daysLater: sr.SupersededBy?.DaysLater ?? null,
          cveCount: sr.CVEs ? Object.keys(sr.CVEs).length : 0,
          cveList: null,
          activelyExploitedCount: sr.ActivelyExploitedCVEs?.length ?? 0,
          securityInfo: sr.SecurityInfo ?? null,
          updateSummary: sr.UpdateSummary ?? null,
          patchesRelease: null,
          osVersion: osv.OSVersion,
          lane,
          branchesFrom,
          rowIndex,
          cx: SVG_LEFT_PADDING + lane * LANE_WIDTH,
          cy: SVG_TOP_PADDING + rowIndex * ROW_HEIGHT,
        }
      })

      // Use unique key: BSI nodes get "bsi-" prefix to avoid collision with release versions
      const nk = (n) => n.type === 'bsi' ? `bsi-${n.version}` : n.version
      const nodeMap = Object.fromEntries(nodes.map(n => [nk(n), n]))
      const maxLane = Math.max(0, ...nodes.map(n => n.lane))

      // Build edges
      const trunkEdges = []
      const branchEdges = []
      const mergeEdges = []

      // Trunk: connect consecutive lane-0 nodes (releases + BSIs)
      const trunkNodes = nodes.filter(n => n.lane === 0)
      for (let i = 0; i < trunkNodes.length - 1; i++) {
        trunkEdges.push({
          x: trunkNodes[i].cx,
          y1: trunkNodes[i].cy,
          y2: trunkNodes[i + 1].cy,
        })
      }

      // Branch-out and merge-in
      for (const node of nodes) {
        if (node.scope === 'device-specific') {
          if (node.branchesFrom && nodeMap[node.branchesFrom]) {
            const parent = nodeMap[node.branchesFrom]
            branchEdges.push({
              path: cubicBezier(parent.cx, parent.cy, node.cx, node.cy),
            })
          }
          const mergeTarget = node.mergedInto || node.supersededBy
          if (mergeTarget && nodeMap[mergeTarget]) {
            const target = nodeMap[mergeTarget]
            mergeEdges.push({
              path: cubicBezier(node.cx, node.cy, target.cx, target.cy),
            })
          }
        }
      }

      // DaysLater labels between consecutive release nodes on trunk
      const releaseNodes = nodes.filter(n => n.type === 'release' && n.lane === 0)
      const daysLabels = []
      for (let i = 0; i < releaseNodes.length - 1; i++) {
        const curr = releaseNodes[i]
        if (curr.daysLater) {
          daysLabels.push({
            x: curr.cx - 24,
            y: (curr.cy + releaseNodes[i + 1].cy) / 2 + 4,
            text: `${curr.daysLater}d`,
          })
        }
      }

      const svgWidth = SVG_LEFT_PADDING + (maxLane + 1) * LANE_WIDTH + RIGHT_LABEL_WIDTH
      const svgHeight = SVG_TOP_PADDING * 2 + nodes.length * ROW_HEIGHT

      return {
        osVersion: osv.OSVersion,
        nodes,
        nodeMap,
        trunkEdges,
        branchEdges,
        mergeEdges,
        daysLabels,
        svgWidth,
        svgHeight,
        maxLane,
      }
    })
  } catch (e) {
    console.error('Graph build error:', e)
    return []
  }
})

function cubicBezier(x1, y1, x2, y2) {
  const midY = (y1 + y2) / 2
  return `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`
}

function formatDate(dateString) {
  if (!dateString) return ''
  try {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }).format(date)
  } catch {
    return dateString
  }
}

function pillWidth(name) {
  return name.length * 6.5 + 16
}

function bsiDiamond(cx, cy, idx) {
  const ox = cx + NODE_RADIUS + 4 + idx * 14
  const oy = cy
  const s = 5
  return `${ox},${oy - s} ${ox + s},${oy} ${ox},${oy + s} ${ox - s},${oy}`
}

function nodeKey(n) {
  return n.type === 'bsi' ? `bsi-${n.version}` : n.version
}

function toggleExpanded(key) {
  expandedVersion.value = expandedVersion.value === key ? null : key
}

function switchPlatform(id) {
  selectedPlatform.value = id
  selectedOSVersion.value = null
  feedData.value = null
}

// Map OSVersion + platform to the security page URL with ?version= deep link
const osPageRoutes = {
  macos: {
    'Tahoe 26': '/macos/tahoe', 'Sequoia 15': '/macos/sequoia',
    'Sonoma 14': '/macos/sonoma', 'Ventura 13': '/macos/ventura',
    'Monterey 12': '/macos/monterey',
  },
  ios: {
    '26': '/ios/ios26', '18': '/ios/ios18', '17': '/ios/ios17',
  },
  tvos: {
    '26': '/tvos/tvos26', '18': '/tvos/tvos18',
  },
  watchos: {
    '26': '/watchos/watchos26', '11': '/watchos/watchos11',
  },
  visionos: {
    '26': '/visionos/visionos26', '2': '/visionos/visionos2',
  },
  safari: {
    '26': '/safari/safari26', '18': '/safari/safari18',
  },
}

function getSecurityPageUrl(osVersion, version) {
  const base = import.meta.env.BASE_URL || '/'
  const routes = osPageRoutes[selectedPlatform.value] || {}
  const pagePath = routes[osVersion]
  if (!pagePath) return null
  return `${base}${pagePath.replace(/^\//, '')}?version=${version}`
}

function navigateToSecurity(osVersion, version, event) {
  const url = getSecurityPageUrl(osVersion, version)
  if (url) {
    event.stopPropagation()
    window.location.href = url
  }
}

// --- Markdown / Mermaid export ---

const copyFeedback = ref(null) // group osVersion currently showing "Copied!"

function generateMermaid(group) {
  // Mermaid gitGraph needs chronological order (oldest first)
  const chronological = [...group.nodes].reverse()
  const lines = ['gitGraph']

  const activeBranches = new Set()
  let onMain = true

  for (const node of chronological) {
    if (node.type === 'bsi') {
      if (!onMain) {
        lines.push('  checkout main')
        onMain = true
      }
      lines.push(`  commit id: "BSI ${node.version}" type: HIGHLIGHT`)
      continue
    }

    if (node.scope === 'device-specific') {
      const branchName = node.deviceNames[0]
        ? node.deviceNames[0].replace(/[^a-zA-Z0-9]/g, '-').replace(/-+/g, '-').substring(0, 30)
        : `device-${node.version}`

      if (!activeBranches.has(branchName)) {
        if (!onMain) {
          lines.push('  checkout main')
          onMain = true
        }
        lines.push(`  branch ${branchName}`)
        activeBranches.add(branchName)
        onMain = false
      } else {
        lines.push(`  checkout ${branchName}`)
        onMain = false
      }
      lines.push(`  commit id: "${node.version}"`)
    } else {
      if (!onMain) {
        lines.push('  checkout main')
        onMain = true
      }

      // Merge any device branches that merge into this version
      for (const other of chronological) {
        if (other.type === 'release' && other.mergedInto === node.version) {
          const mergeBranch = other.deviceNames[0]
            ? other.deviceNames[0].replace(/[^a-zA-Z0-9]/g, '-').replace(/-+/g, '-').substring(0, 30)
            : `device-${other.version}`
          if (activeBranches.has(mergeBranch)) {
            lines.push(`  merge ${mergeBranch}`)
            activeBranches.delete(mergeBranch)
          }
        }
      }

      const tag = node.activelyExploitedCount > 0 ? ` tag: "${node.activelyExploitedCount} KEV"` : ''
      lines.push(`  commit id: "${node.version}"${tag}`)
    }
  }

  return lines.join('\n')
}

function generateMarkdown(group) {
  const platform = platforms.find(p => p.id === selectedPlatform.value)
  const title = `${platform?.label || ''} ${group.osVersion}`
  const mermaid = generateMermaid(group)

  // Table: latest first (same order as group.nodes which is reverse-chronological)
  const tableHeader = '| Version | Build | Date | Type | CVEs | KEV | Superseded By |'
  const tableSep    = '|---------|-------|------|------|------|-----|---------------|'
  const tableRows = group.nodes.map(node => {
    const date = formatDate(node.releaseDate)
    const type = node.type === 'bsi' ? 'BSI'
      : node.scope === 'device-specific' ? `Device (${node.deviceNames[0] || '?'})`
      : 'Universal'
    const kev = node.activelyExploitedCount || ''
    const sup = node.supersededBy || ''
    return `| ${node.version} | \`${node.build}\` | ${date} | ${type} | ${node.cveCount} | ${kev} | ${sup} |`
  })

  return [
    `## ${title} — Release Timeline`,
    '',
    '```mermaid',
    mermaid,
    '```',
    '',
    '### Release Summary',
    '',
    tableHeader,
    tableSep,
    ...tableRows,
    '',
    `> Generated from [SOFA](https://sofa.macadmins.io/release-timeline) on ${new Date().toISOString().split('T')[0]}`,
  ].join('\n')
}

async function copyMarkdown(group) {
  const md = generateMarkdown(group)
  try {
    await navigator.clipboard.writeText(md)
    copyFeedback.value = group.osVersion
    setTimeout(() => { copyFeedback.value = null }, 2000)
  } catch {
    // Fallback: prompt user
    console.warn('Clipboard API not available')
  }
}

function downloadMarkdown(group) {
  const md = generateMarkdown(group)
  const platform = platforms.find(p => p.id === selectedPlatform.value)
  const filename = `${platform?.id || 'release'}-${group.osVersion.replace(/\s+/g, '-').toLowerCase()}-timeline.md`
  const blob = new Blob([md], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="timeline-page">
    <!-- Controls -->
    <div class="controls">
      <div class="platform-tabs">
        <button
          v-for="p in platforms"
          :key="p.id"
          class="tab-btn"
          :class="{ active: selectedPlatform === p.id }"
          @click="switchPlatform(p.id)"
        >
          {{ p.label }}
        </button>
      </div>
      <div v-if="availableOSVersions.length > 1" class="os-filter">
        <button
          v-for="osv in availableOSVersions"
          :key="osv"
          class="filter-btn"
          :class="{ active: selectedOSVersion === osv }"
          @click="selectedOSVersion = osv"
        >
          {{ osv }}
        </button>
      </div>
    </div>

    <!-- Legend -->
    <div class="legend">
      <span class="legend-item">
        <span class="legend-dot universal"></span> Universal release
      </span>
      <span class="legend-item">
        <span class="legend-dot device-specific"></span> Device-specific branch
      </span>
      <span class="legend-item">
        <span class="legend-diamond"></span> Background Security Improvement
      </span>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading release data...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-state">
      <p>Failed to load feed data: {{ error.message }}</p>
    </div>

    <!-- Graph groups -->
    <div v-else v-for="group in graphGroups" :key="group.osVersion" class="graph-group">
      <div class="group-header">
        <h3 class="group-title">{{ group.osVersion }}</h3>
        <div class="export-buttons">
          <button class="export-btn" @click="copyMarkdown(group)" :title="'Copy as Markdown with Mermaid diagram'">
            {{ copyFeedback === group.osVersion ? 'Copied!' : 'Copy Markdown' }}
          </button>
          <button class="export-btn" @click="downloadMarkdown(group)" title="Download .md file">
            Download .md
          </button>
        </div>
      </div>

      <div class="graph-scroll-wrapper">
        <svg
          :width="group.svgWidth"
          :height="group.svgHeight"
          class="timeline-svg"
        >
          <!-- Trunk edges -->
          <line
            v-for="(edge, i) in group.trunkEdges"
            :key="'trunk-' + i"
            :x1="edge.x"
            :y1="edge.y1"
            :x2="edge.x"
            :y2="edge.y2"
            class="trunk-edge"
          />

          <!-- Branch-out curves -->
          <path
            v-for="(edge, i) in group.branchEdges"
            :key="'branch-' + i"
            :d="edge.path"
            class="branch-edge"
          />

          <!-- Merge-in curves -->
          <path
            v-for="(edge, i) in group.mergeEdges"
            :key="'merge-' + i"
            :d="edge.path"
            class="merge-edge"
          />

          <!-- DaysLater labels -->
          <text
            v-for="(label, i) in group.daysLabels"
            :key="'days-' + i"
            :x="label.x"
            :y="label.y"
            class="days-label"
          >
            {{ label.text }}
          </text>

          <!-- Nodes -->
          <g
            v-for="node in group.nodes"
            :key="nodeKey(node)"
            class="node-group"
            :class="{
              hovered: hoveredVersion === nodeKey(node),
              expanded: expandedVersion === nodeKey(node),
              'is-device-specific': node.scope === 'device-specific',
            }"
            @click="toggleExpanded(nodeKey(node))"
            @mouseenter="hoveredVersion = nodeKey(node)"
            @mouseleave="hoveredVersion = null"
            style="cursor: pointer"
          >
            <!-- Commit dot (circle for releases, diamond for BSI) -->
            <circle
              v-if="node.type === 'release'"
              :cx="node.cx"
              :cy="node.cy"
              :r="NODE_RADIUS"
              :class="['commit-dot', node.scope]"
            />
            <rect
              v-else
              :x="node.cx - 7"
              :y="node.cy - 7"
              width="14"
              height="14"
              rx="2"
              class="commit-dot bsi"
              :transform="`rotate(45 ${node.cx} ${node.cy})`"
            />

            <!-- Labels: different layout per node type -->

            <!-- BSI node -->
            <g v-if="node.type === 'bsi'">
              <text
                :x="node.cx + NODE_RADIUS + 12"
                :y="node.cy - 4"
                class="version-label bsi-label"
              >
                BSI {{ node.version }}
              </text>
              <text
                :x="node.cx + NODE_RADIUS + 12"
                :y="node.cy + 12"
                class="date-label"
              >
                {{ formatDate(node.releaseDate) }}
                <tspan v-if="node.patchesRelease" class="bsi-patches-label">
                  · patches {{ node.patchesRelease }}
                </tspan>
                <tspan v-if="node.cveCount" class="cve-count-label">
                  · {{ node.cveCount }} CVEs
                </tspan>
              </text>
            </g>

            <!-- Universal release -->
            <g v-else-if="node.scope === 'universal'">
              <text
                :x="node.cx + NODE_RADIUS + 12"
                :y="node.cy - 4"
                class="version-label version-link"
                @click.stop="navigateToSecurity(node.osVersion, node.version, $event)"
              >
                {{ node.version }} →
              </text>
              <text
                :x="node.cx + NODE_RADIUS + 12"
                :y="node.cy + 12"
                class="date-label"
              >
                {{ formatDate(node.releaseDate) }}
                <tspan v-if="node.cveCount" class="cve-count-label">
                  · {{ node.cveCount }} CVEs
                </tspan>
                <tspan v-if="node.activelyExploitedCount" class="kev-count-label">
                  · {{ node.activelyExploitedCount }} KEV
                </tspan>
              </text>
            </g>

            <!-- Device-specific: version above, pill at center, date below -->
            <g v-else>
              <text
                :x="node.cx + NODE_RADIUS + 12"
                :y="node.cy - 18"
                class="version-label version-link"
                @click.stop="navigateToSecurity(node.osVersion, node.version, $event)"
              >
                {{ node.version }} →
              </text>
              <!-- Device pill next to dot -->
              <g v-if="node.deviceNames.length">
                <rect
                  :x="node.cx + NODE_RADIUS + 6"
                  :y="node.cy - 10"
                  :width="pillWidth(node.deviceCount <= 2 ? node.deviceNames.join(', ') : node.deviceNames[0] + ' +' + (node.deviceCount - 1))"
                  height="20"
                  rx="10"
                  class="device-pill-bg"
                />
                <text
                  :x="node.cx + NODE_RADIUS + 14"
                  :y="node.cy + 4"
                  class="device-pill-text"
                >
                  {{ node.deviceCount <= 2 ? node.deviceNames.join(', ') : node.deviceNames[0] + ' +' + (node.deviceCount - 1) }}
                </text>
                <title>{{ node.deviceNames.join('\n') }}</title>
              </g>
              <text
                :x="node.cx + NODE_RADIUS + 12"
                :y="node.cy + 26"
                class="date-label"
              >
                {{ formatDate(node.releaseDate) }}
                <tspan v-if="node.cveCount" class="cve-count-label">
                  · {{ node.cveCount }} CVEs
                </tspan>
                <tspan v-if="node.activelyExploitedCount" class="kev-count-label">
                  · {{ node.activelyExploitedCount }} KEV
                </tspan>
              </text>
            </g>

            <!-- BSI markers removed — BSIs are a separate concept from device branches -->
          </g>
        </svg>
      </div>

      <!-- Expanded detail panel -->
      <Transition name="slide">
        <div
          v-if="expandedVersion && group.nodeMap[expandedVersion]"
          class="detail-panel"
        >
          <div class="detail-header">
            <h4>{{ group.nodeMap[expandedVersion].type === 'bsi' ? 'BSI ' : '' }}{{ group.nodeMap[expandedVersion].version }}</h4>
            <span v-if="group.nodeMap[expandedVersion].type === 'bsi'" class="detail-scope bsi">BSI</span>
            <span v-else class="detail-scope" :class="group.nodeMap[expandedVersion].scope">
              {{ group.nodeMap[expandedVersion].scope === 'device-specific' ? 'Device-specific' : 'Universal' }}
            </span>
            <button class="detail-close" @click="expandedVersion = null">×</button>
          </div>

          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">Build</span>
              <span class="detail-value mono">{{ group.nodeMap[expandedVersion].build }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Release Date</span>
              <span class="detail-value">{{ formatDate(group.nodeMap[expandedVersion].releaseDate) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">CVEs Addressed</span>
              <span class="detail-value">{{ group.nodeMap[expandedVersion].cveCount }}</span>
            </div>
            <div v-if="group.nodeMap[expandedVersion].activelyExploitedCount" class="detail-item">
              <span class="detail-label">Actively Exploited</span>
              <span class="detail-value kev">{{ group.nodeMap[expandedVersion].activelyExploitedCount }}</span>
            </div>
            <div v-if="group.nodeMap[expandedVersion].daysLater" class="detail-item">
              <span class="detail-label">Superseded After</span>
              <span class="detail-value">{{ group.nodeMap[expandedVersion].daysLater }} days</span>
            </div>
            <div v-if="group.nodeMap[expandedVersion].supersededBy" class="detail-item">
              <span class="detail-label">Superseded By</span>
              <span class="detail-value">{{ group.nodeMap[expandedVersion].supersededBy }}</span>
            </div>
            <div v-if="group.nodeMap[expandedVersion].mergedInto" class="detail-item">
              <span class="detail-label">Merged Into</span>
              <span class="detail-value">{{ group.nodeMap[expandedVersion].mergedInto }}</span>
            </div>
            <div v-if="group.nodeMap[expandedVersion].patchesRelease" class="detail-item">
              <span class="detail-label">Patches Release</span>
              <span class="detail-value">{{ group.nodeMap[expandedVersion].patchesRelease }}</span>
            </div>
            <div v-if="group.nodeMap[expandedVersion].cveList?.length" class="detail-item full-width">
              <span class="detail-label">CVEs</span>
              <span class="detail-value">{{ group.nodeMap[expandedVersion].cveList.join(', ') }}</span>
            </div>
            <div v-if="group.nodeMap[expandedVersion].scope === 'device-specific' && group.nodeMap[expandedVersion].type === 'release'" class="detail-item full-width">
              <span class="detail-label">Supported Devices ({{ group.nodeMap[expandedVersion].deviceCount }})</span>
              <span class="detail-value">{{ group.nodeMap[expandedVersion].deviceNames.join(', ') }}</span>
            </div>
          </div>

          <!-- Update Summary -->
          <div v-if="group.nodeMap[expandedVersion].updateSummary" class="detail-summary">
            <div v-if="group.nodeMap[expandedVersion].updateSummary.Summary" class="summary-text">
              {{ group.nodeMap[expandedVersion].updateSummary.Summary }}
            </div>
            <div v-if="group.nodeMap[expandedVersion].updateSummary.Recommendation" class="recommendation-text">
              <strong>Recommendation:</strong> {{ group.nodeMap[expandedVersion].updateSummary.Recommendation }}
            </div>
          </div>

          <!-- Security info link -->
          <a
            v-if="group.nodeMap[expandedVersion].securityInfo"
            :href="group.nodeMap[expandedVersion].securityInfo"
            target="_blank"
            class="detail-link"
          >
            View Apple Security Notes →
          </a>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.timeline-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

/* Controls */
.controls {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.platform-tabs {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
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

.tab-btn:hover {
  background: var(--vp-c-bg-mute);
  color: var(--vp-c-text-1);
}

.tab-btn.active {
  background: var(--vp-c-brand);
  border-color: var(--vp-c-brand);
  color: white;
}

.os-filter {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
}

.filter-btn {
  padding: 0.375rem 0.75rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 6px;
  background: transparent;
  color: var(--vp-c-text-3);
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.filter-btn:hover {
  color: var(--vp-c-text-1);
  border-color: var(--vp-c-text-3);
}

.filter-btn.active {
  background: var(--vp-c-bg-mute);
  border-color: var(--vp-c-brand);
  color: var(--vp-c-brand);
  font-weight: 500;
}

/* Legend */
.legend {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
  font-size: 0.8125rem;
  color: var(--vp-c-text-2);
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-dot.universal {
  background: var(--vp-c-brand);
}

.legend-dot.device-specific {
  background: #f59e0b;
}

.legend-diamond {
  width: 10px;
  height: 10px;
  background: #a78bfa;
  transform: rotate(45deg);
}

/* Loading / Error */
.loading-state,
.error-state {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 2rem;
  color: var(--vp-c-text-2);
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--vp-c-divider);
  border-top-color: var(--vp-c-brand);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Graph */
.graph-group {
  margin-bottom: 2rem;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.group-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--vp-c-text-1);
  margin: 0;
}

.export-buttons {
  display: flex;
  gap: 0.375rem;
}

.export-btn {
  padding: 0.25rem 0.625rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 6px;
  background: var(--vp-c-bg-soft);
  color: var(--vp-c-text-3);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.export-btn:hover {
  color: var(--vp-c-text-1);
  border-color: var(--vp-c-brand);
}

.graph-scroll-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  background: var(--vp-c-bg);
  padding: 0.5rem;
}

/* SVG elements */
.trunk-edge {
  stroke: var(--vp-c-brand);
  stroke-width: 2.5;
}

.branch-edge,
.merge-edge {
  stroke: #f59e0b;
  stroke-width: 2;
  fill: none;
  stroke-dasharray: 6 3;
}

.commit-dot.universal {
  fill: var(--vp-c-brand);
  transition: filter 0.15s ease;
}

.commit-dot.device-specific {
  fill: #f59e0b;
  transition: filter 0.15s ease;
}

.commit-dot.bsi {
  fill: #a78bfa;
  transition: filter 0.15s ease;
}

.node-group.hovered .commit-dot.bsi {
  filter: drop-shadow(0 0 6px #a78bfa);
}

.node-group.hovered .commit-dot.universal {
  filter: drop-shadow(0 0 6px var(--vp-c-brand));
}

.node-group.hovered .commit-dot.device-specific {
  filter: drop-shadow(0 0 6px #f59e0b);
}

.node-group.expanded .commit-dot {
  stroke: var(--vp-c-text-1);
  stroke-width: 2;
}

.version-label {
  fill: var(--vp-c-text-1);
  font-size: 13px;
  font-weight: 600;
  font-family: var(--vp-font-family-base);
}

.version-link {
  cursor: pointer;
  transition: fill 0.15s ease;
}

.version-link:hover {
  fill: var(--vp-c-brand);
  text-decoration: underline;
}

.bsi-label {
  fill: #7c3aed;
  font-weight: 500;
}

.bsi-patches-label {
  fill: #7c3aed;
}

.date-label {
  fill: var(--vp-c-text-2);
  font-size: 11px;
  font-family: var(--vp-font-family-base);
}

.cve-count-label {
  fill: var(--vp-c-text-1);
}

.kev-count-label {
  fill: #ef4444;
}

.days-label {
  fill: var(--vp-c-text-2);
  font-size: 10px;
  font-style: italic;
  font-family: var(--vp-font-family-base);
}

.device-pill-bg {
  fill: rgba(245, 158, 11, 0.15);
  stroke: rgba(245, 158, 11, 0.4);
  stroke-width: 1;
}

.device-pill-text {
  fill: #b45309;
  font-size: 10px;
  font-weight: 500;
  font-family: var(--vp-font-family-base);
}

.bsi-marker {
  fill: #a78bfa;
  opacity: 0.8;
  transition: opacity 0.15s ease;
}

.bsi-marker:hover {
  opacity: 1;
}

/* Detail panel */
.detail-panel {
  margin-top: 0.75rem;
  padding: 1.25rem;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.detail-header h4 {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--vp-c-text-1);
  margin: 0;
}

.detail-scope {
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.detail-scope.universal {
  background: rgba(59, 130, 246, 0.1);
  color: var(--vp-c-brand);
}

.detail-scope.device-specific {
  background: rgba(245, 158, 11, 0.1);
  color: #b45309;
}

.detail-scope.bsi {
  background: rgba(167, 139, 250, 0.1);
  color: #7c3aed;
}

.detail-close {
  margin-left: auto;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--vp-c-text-3);
  font-size: 1.25rem;
  cursor: pointer;
}

.detail-close:hover {
  background: var(--vp-c-bg-mute);
  color: var(--vp-c-text-1);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.detail-item.full-width {
  grid-column: 1 / -1;
}

.detail-label {
  font-size: 0.75rem;
  color: var(--vp-c-text-3);
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.detail-value {
  font-size: 0.875rem;
  color: var(--vp-c-text-1);
  font-weight: 500;
}

.detail-value.mono {
  font-family: monospace;
}

.detail-value.kev {
  color: #ef4444;
  font-weight: 600;
}

.detail-summary {
  padding: 0.75rem;
  background: var(--vp-c-bg);
  border-radius: 8px;
  margin-bottom: 0.75rem;
}

.summary-text {
  font-size: 0.875rem;
  color: var(--vp-c-text-2);
  margin-bottom: 0.375rem;
}

.recommendation-text {
  font-size: 0.8125rem;
  color: var(--vp-c-text-3);
}

.detail-bsi {
  margin-bottom: 0.75rem;
}

.detail-bsi h5 {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--vp-c-text-2);
  margin: 0 0 0.5rem 0;
}

.bsi-entry {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  padding: 0.375rem 0;
  font-size: 0.8125rem;
  border-bottom: 1px solid var(--vp-c-divider-light);
}

.bsi-version {
  font-weight: 500;
  color: #7c3aed;
}

.bsi-build {
  font-family: monospace;
  color: var(--vp-c-text-3);
  font-size: 0.75rem;
}

.bsi-cves {
  color: var(--vp-c-text-2);
  font-size: 0.75rem;
}

.detail-link {
  display: inline-block;
  font-size: 0.875rem;
  color: var(--vp-c-brand);
  text-decoration: none;
  font-weight: 500;
}

.detail-link:hover {
  text-decoration: underline;
}

/* Transition */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.2s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Dark mode */
:root.dark .device-pill-bg {
  fill: rgba(245, 158, 11, 0.1);
  stroke: rgba(245, 158, 11, 0.3);
}

:root.dark .device-pill-text {
  fill: #fbbf24;
}

:root.dark .graph-scroll-wrapper {
  background: rgba(31, 41, 55, 0.3);
  border-color: rgba(55, 65, 81, 0.5);
}

:root.dark .detail-scope.device-specific {
  color: #fbbf24;
}

/* Mobile */
@media (max-width: 768px) {
  .platform-tabs {
    gap: 0.25rem;
  }

  .tab-btn {
    padding: 0.375rem 0.75rem;
    font-size: 0.8125rem;
  }

  .legend {
    gap: 1rem;
    font-size: 0.75rem;
  }

  .detail-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
