
<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useSOFAData } from '../composables/useSOFAData'
import { useRoute } from 'vitepress'

const macOSData = ref({})
const iOSData = ref({})
const tvOSData = ref({})
const watchOSData = ref({})
const visionOSData = ref({})
const safariData = ref({})

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  platform: {
    type: String,
    required: true
  },
  stage: {
    type: String,
    default: 'release'
  }
})

const securityUpdates = ref([])
const loading = ref(true)
const error = ref(null)

const loadSecurityData = async () => {
  try {
    loading.value = true
    error.value = null
    
    // Select the correct data based on platform
    let data
    switch (props.platform.toLowerCase()) {
      case 'macos':
        data = macOSData.value
        break
      case 'ios':
      case 'ipados': // Handle iPadOS as iOS since they share the same feed
        data = iOSData.value
        break
      case 'tvos':
        data = tvOSData.value
        break
      case 'watchos':
        data = watchOSData.value
        break
      case 'visionos':
        data = visionOSData.value
        break
      case 'safari':
        data = safariData.value
        break
      default:
        throw new Error(`Unsupported platform: ${props.platform}`)
    }

    const version = props.title.split(' ')[1] // Gets version number

    let releaseData = []
    let latestRelease = null
    
    if (props.platform.toLowerCase() === 'safari') {
      // Handle Safari data structure
      const appVersionData = data.AppVersions?.find(
        app => app.AppVersion === `Safari ${version}`
      )
      releaseData = appVersionData?.SecurityReleases || []
      latestRelease = appVersionData?.Latest
    } else {
      // Handle OS data structure (macOS, iOS, etc)
      // For iOS/iPadOS, handle both "iOS 18" and "iPadOS 18" style searches
      const osVersionData = data.OSVersions?.find(
        os => {
          // Extract just the version number for iOS/iPadOS
          if (props.platform.toLowerCase() === 'ios' || props.platform.toLowerCase() === 'ipados') {
            // Version might be "18" from "iOS 18" or "iPadOS 18" 
            const versionNum = version.replace(/^(iOS|iPadOS)\s*/i, '')
            return os.OSVersion.includes(versionNum) || os.OSVersion === `iOS ${versionNum}`
          }
          return os.OSVersion.includes(version)
        }
      )
      releaseData = osVersionData?.SecurityReleases || []
      latestRelease = osVersionData?.Latest
    }

    // Check if Latest release should be added to the list
    if (latestRelease && latestRelease.ProductVersion) {
      // Check if Latest is already in SecurityReleases
      const latestInReleases = releaseData.some(
        release => release.ProductVersion === latestRelease.ProductVersion
      )
      
      if (!latestInReleases) {
        // Add Latest as the first item if it's not in the releases
        // Format it to match SecurityReleases structure
        const latestFormatted = {
          UpdateName: latestRelease.UpdateName || `${props.platform} ${latestRelease.ProductVersion}`,
          ProductName: latestRelease.ProductName || props.platform,
          ProductVersion: latestRelease.ProductVersion,
          Build: latestRelease.Build,
          AllBuilds: latestRelease.AllBuilds || [latestRelease.Build],
          ReleaseDate: latestRelease.ReleaseDate,
          SecurityInfo: latestRelease.SecurityInfo,
          SecurityInfoContext: latestRelease.SecurityInfoContext,
          // Latest typically has no CVEs if it's not in SecurityReleases
          CVEs: {},
          ActivelyExploitedCVEs: [],
          DaysSincePreviousRelease: 0
        }
        releaseData = [latestFormatted, ...releaseData]
      }
    }

    if (releaseData && releaseData.length > 0) {
      securityUpdates.value = processSecurityData(releaseData)
      
      // Auto-expand the latest version
      if (securityUpdates.value.length > 0) {
        const latestVersion = securityUpdates.value[0].version
        expandedVersions.value[latestVersion] = true
        
        // Also expand the CVE groups for the latest version if there are any
        const latestUpdate = securityUpdates.value[0]
        if (latestUpdate.cves && latestUpdate.cves.length > 0) {
          const groups = groupCVEs(latestUpdate.cves)
          const groupKeys = getSortedGroupKeys(groups)
          groupKeys.forEach(group => {
            const key = `${latestVersion}-${group}`
            expandedCVEGroups.value[key] = true
          })
        }
      }
    } else {
      throw new Error(`No security data found for ${props.platform} ${version}`)
    }
  } catch (err) {
    console.error('Error loading security data:', err)
    error.value = `Failed to load security data: ${err.message}`
  } finally {
    loading.value = false
  }
}

const route = useRoute()

// Check for version query parameter and auto-expand
const checkAndExpandVersion = async () => {
  // Check if we're in the browser (not SSR)
  if (typeof window === 'undefined') {
    return
  }
  
  // Check if there's a version query parameter
  const params = new URLSearchParams(window.location.search)
  const targetVersion = params.get('version')
  
  if (targetVersion && securityUpdates.value.length > 0) {
    // Find the matching version
    const matchingUpdate = securityUpdates.value.find(update => 
      update.version === targetVersion
    )
    
    if (matchingUpdate) {
      // Expand the version
      expandedVersions.value[matchingUpdate.version] = true
      
      // Wait for DOM update then scroll to it
      await nextTick()
      
      // Find the element and scroll to it
      const element = document.querySelector(`[data-version="${matchingUpdate.version}"]`)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' })
        
        // Add a highlight effect
        element.classList.add('highlight-version')
        setTimeout(() => {
          element.classList.remove('highlight-version')
        }, 2000)
      }
    }
  }
}

// Use composable for data fetching
const macosInfo = useSOFAData('v2/macos_data_feed.json')
const iosInfo = useSOFAData('v2/ios_data_feed.json')
const tvosInfo = useSOFAData('v2/tvos_data_feed.json')
const watchosInfo = useSOFAData('v2/watchos_data_feed.json')
const visionosInfo = useSOFAData('v2/visionos_data_feed.json')
const safariInfo = useSOFAData('v2/safari_data_feed.json')

// Track if initial load has happened
const hasLoadedInitially = ref(false)

// Watch for data changes and update local refs
watch(() => macosInfo.data.value, async (newData) => {
  if (newData) {
    macOSData.value = newData
    if (props.platform.toLowerCase() === 'macos' && !hasLoadedInitially.value) {
      hasLoadedInitially.value = true
      await loadSecurityData()
      await checkAndExpandVersion()
    }
  }
})
watch(() => iosInfo.data.value, async (newData) => {
  if (newData) {
    iOSData.value = newData
    if ((props.platform.toLowerCase() === 'ios' || props.platform.toLowerCase() === 'ipados') && !hasLoadedInitially.value) {
      hasLoadedInitially.value = true
      await loadSecurityData()
      await checkAndExpandVersion()
    }
  }
})
watch(() => tvosInfo.data.value, async (newData) => {
  if (newData) {
    tvOSData.value = newData
    if (props.platform.toLowerCase() === 'tvos' && !hasLoadedInitially.value) {
      hasLoadedInitially.value = true
      await loadSecurityData()
      await checkAndExpandVersion()
    }
  }
})
watch(() => watchosInfo.data.value, async (newData) => {
  if (newData) {
    watchOSData.value = newData
    if (props.platform.toLowerCase() === 'watchos' && !hasLoadedInitially.value) {
      hasLoadedInitially.value = true
      await loadSecurityData()
      await checkAndExpandVersion()
    }
  }
})
watch(() => visionosInfo.data.value, async (newData) => {
  if (newData) {
    visionOSData.value = newData
    if (props.platform.toLowerCase() === 'visionos' && !hasLoadedInitially.value) {
      hasLoadedInitially.value = true
      await loadSecurityData()
      await checkAndExpandVersion()
    }
  }
})
watch(() => safariInfo.data.value, async (newData) => {
  if (newData) {
    safariData.value = newData
    if (props.platform.toLowerCase() === 'safari' && !hasLoadedInitially.value) {
      hasLoadedInitially.value = true
      await loadSecurityData()
      await checkAndExpandVersion()
    }
  }
})

// Combined onMounted to ensure data loads first
onMounted(async () => {
  // Check if data is already available and load immediately
  if (props.platform.toLowerCase() === 'macos' && macosInfo.data.value) {
    macOSData.value = macosInfo.data.value
    hasLoadedInitially.value = true
    await loadSecurityData()
    await checkAndExpandVersion()
  } else if ((props.platform.toLowerCase() === 'ios' || props.platform.toLowerCase() === 'ipados') && iosInfo.data.value) {
    iOSData.value = iosInfo.data.value
    hasLoadedInitially.value = true
    await loadSecurityData()
    await checkAndExpandVersion()
  } else if (props.platform.toLowerCase() === 'tvos' && tvosInfo.data.value) {
    tvOSData.value = tvosInfo.data.value
    hasLoadedInitially.value = true
    await loadSecurityData()
    await checkAndExpandVersion()
  } else if (props.platform.toLowerCase() === 'watchos' && watchosInfo.data.value) {
    watchOSData.value = watchosInfo.data.value
    hasLoadedInitially.value = true
    await loadSecurityData()
    await checkAndExpandVersion()
  } else if (props.platform.toLowerCase() === 'visionos' && visionosInfo.data.value) {
    visionOSData.value = visionosInfo.data.value
    hasLoadedInitially.value = true
    await loadSecurityData()
    await checkAndExpandVersion()
  } else if (props.platform.toLowerCase() === 'safari' && safariInfo.data.value) {
    safariData.value = safariInfo.data.value
    hasLoadedInitially.value = true
    await loadSecurityData()
    await checkAndExpandVersion()
  }
  // If data is not available yet, the watchers will handle it
})

// State for expanded/collapsed sections with persistence
const getStateKey = () => `security-expanded-${props.platform}-${props.title}`.toLowerCase()

// Load saved state from sessionStorage
const loadSavedState = () => {
  // Check if we're in the browser (not SSR)
  if (typeof window === 'undefined' || typeof sessionStorage === 'undefined') {
    return { versions: {}, cveGroups: {} }
  }
  
  try {
    const key = getStateKey()
    const savedState = sessionStorage.getItem(key)
    if (savedState) {
      const parsed = JSON.parse(savedState)
      return {
        versions: parsed.versions || {},
        cveGroups: parsed.cveGroups || {}
      }
    }
  } catch (e) {
    console.warn('Failed to load saved state:', e)
  }
  return { versions: {}, cveGroups: {} }
}

// Initialize with saved state
const savedState = loadSavedState()
const expandedVersions = ref(savedState.versions)
const expandedCVEGroups = ref(savedState.cveGroups)

// Save state to sessionStorage whenever it changes
const saveState = () => {
  // Check if we're in the browser (not SSR)
  if (typeof window === 'undefined' || typeof sessionStorage === 'undefined') {
    return
  }
  
  try {
    const key = getStateKey()
    const state = {
      versions: expandedVersions.value,
      cveGroups: expandedCVEGroups.value
    }
    sessionStorage.setItem(key, JSON.stringify(state))
  } catch (e) {
    console.warn('Failed to save state:', e)
  }
}

// Watch for changes and save state
watch(expandedVersions, saveState, { deep: true })
watch(expandedCVEGroups, saveState, { deep: true })

// Function to extract numeric part from CVE ID for sorting
const extractCveNumber = (cve) => {
  const parts = cve.cve.split('-')
  if (parts.length >= 3) {
    return parseInt(parts[2], 10) || 0
  }
  return 0
}

// Function to extract year and prefix number for sorting groups
const extractYearAndPrefix = (prefix) => {
  const parts = prefix.split('-')
  if (parts.length >= 3) {
    return {
      year: parseInt(parts[1], 10) || 0,
      prefix: parseInt(parts[2].substring(0, 2), 10) || 0
    }
  }
  return { year: 0, prefix: 0 }
}

// Function to group CVEs by their prefix and sort them numerically within each group
const groupCVEs = (cves) => {
  const groups = {}
  
  cves.forEach(cve => {
    // Extract the prefix (e.g., "CVE-2025-31" from "CVE-2025-31194")
    const parts = cve.cve.split('-')
    if (parts.length >= 3) {
      const prefix = `${parts[0]}-${parts[1]}-${parts[2].substring(0, 2)}`
      
      if (!groups[prefix]) {
        groups[prefix] = []
      }
      
      groups[prefix].push(cve)
    }
  })
  
  // Sort CVEs numerically within each group (DESCENDING order)
  Object.keys(groups).forEach(prefix => {
    groups[prefix].sort((a, b) => extractCveNumber(b) - extractCveNumber(a))
  })
  
  return groups
}

// Get sorted group keys (latest year first, then highest prefix number)
const getSortedGroupKeys = (groups) => {
  return Object.keys(groups).sort((a, b) => {
    const aData = extractYearAndPrefix(a)
    const bData = extractYearAndPrefix(b)
    
    // First sort by year (descending)
    if (aData.year !== bData.year) {
      return bData.year - aData.year
    }
    
    // Then sort by prefix number (descending)
    return bData.prefix - aData.prefix
  })
}

// Check if a CVE is in the actively exploited list
const isActivelyExploited = (cve, activelyExploited) => {
  return activelyExploited.some(exploited => exploited.cve === cve.cve)
}

// Format date to be more user-friendly
const formatDate = (dateString) => {
  if (!dateString) return '';
  
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    }).format(date);
  } catch (e) {
    return dateString;
  }
}

// Determine if high risk based on KEV presence
const hasHighRisk = (update) => {
  if (!update) return false;
  
  const kevCount = update.activelyExploited?.length || 0;
  return kevCount > 0;
}

// Toggle functions
const toggleVersion = (version) => {
  expandedVersions.value[version] = !expandedVersions.value[version]
}

const toggleCVEGroup = (version, group) => {
  const key = `${version}-${group}`
  expandedCVEGroups.value[key] = !expandedCVEGroups.value[key]
}

const isVersionExpanded = (version) => {
  return expandedVersions.value[version] === true
}

const isCVEGroupExpanded = (version, group) => {
  const key = `${version}-${group}`
  return expandedCVEGroups.value[key] === true
}

// Functions to expand/collapse all versions
const expandAllVersions = () => {
  securityUpdates.value.forEach(update => {
    expandedVersions.value[update.version] = true
  })
}

const collapseAllVersions = () => {
  securityUpdates.value.forEach(update => {
    expandedVersions.value[update.version] = false
  })
}

// Functions to expand/collapse all CVE groups for a specific version
const expandAllCVEGroups = (version, groups) => {
  Object.keys(groups).forEach(group => {
    const key = `${version}-${group}`
    expandedCVEGroups.value[key] = true
  })
}

const collapseAllCVEGroups = (version, groups) => {
  Object.keys(groups).forEach(group => {
    const key = `${version}-${group}`
    expandedCVEGroups.value[key] = false
  })
}

// Check if all CVE groups for a version are expanded
const areAllCVEGroupsExpanded = (version, groups) => {
  return Object.keys(groups).every(group => {
    const key = `${version}-${group}`
    return expandedCVEGroups.value[key] === true
  })
}

// Format CVE data from different possible formats
const formatCVEData = (cveData) => {
  const base = import.meta.env.BASE_URL || '/'
  if (typeof cveData === 'string') {
    return { cve: cveData, link: `${base}cve-details?cveId=${cveData}` }
  } else if (typeof cveData === 'object' && cveData !== null) {
    const cveId = cveData.cve || cveData.id || ''
    return {
      cve: cveId,
      link: cveData.link || cveData.url || `${base}cve-details?cveId=${cveId}`
    }
  }
  return { cve: '', link: '' }
}

// Process security data to ensure consistent format
const processSecurityData = (data) => {
  const base = import.meta.env.BASE_URL || '/'
  return data.map(update => {
    // Process CVEs from v2 dict format
    const cves = Object.keys(update.CVEs || {}).map(cve => ({ cve, link: `${base}cve-details?cveId=${cve}` }))

    // Process actively exploited CVEs from v2 string array
    const activelyExploited = (update.ActivelyExploitedCVEs || []).map(cve => ({ cve, link: `${base}cve-details?cveId=${cve}` }))

    return {
      version: update.ProductVersion || '',
      releaseDate: update.ReleaseDate || '',
      isWarning: !!update.SecurityInfo,
      securityInfoLink: update.SecurityInfo || '',
      releaseNotes: update.ReleaseNotes || '',
      vulnerabilitiesCount: update.CVEs ? Object.keys(update.CVEs).length : 0,
      activelyExploited,
      cves,
      daysToPrevRelease: update.DaysSincePreviousRelease || 0,
      updateSummary: update.UpdateSummary || null,
      securityInfoContext: update.SecurityInfoContext || null
    }
  })
}

// Load data on component mount
onMounted(async () => {
  // If securityData prop is provided, use it
  if (props.securityData && props.securityData.length > 0) {
    securityUpdates.value = processSecurityData(props.securityData)
    // Expand the latest version by default
    if (securityUpdates.value.length > 0) {
      expandedVersions.value[securityUpdates.value[0].version] = true
    }
    return
  }
  
  // Otherwise, try to fetch from dataPath if provided
  if (props.dataPath) {
    try {
      const response = await fetch(props.dataPath)
      if (response.ok) {
        const data = await response.json()
        
        // Handle different possible data structures
        let securityData = data
        
        // If data is nested under a specific key, extract it
        if (data.SecurityReleases) {
          securityData = data.SecurityReleases
        } else if (data.OSVersions) {
          // Find the specific OS version
          const osVersion = data.OSVersions.find(os => 
            os.OSVersion.includes(props.title.split(' ')[0])
          )
          if (osVersion && osVersion.SecurityReleases) {
            securityData = osVersion.SecurityReleases
          }
        }
        
        securityUpdates.value = processSecurityData(securityData)
        
        // Expand the latest version by default
        if (securityUpdates.value.length > 0) {
          expandedVersions.value[securityUpdates.value[0].version] = true
        }
      }
    } catch (error) {
      console.error('Error loading security data:', error)
    }
  }
})
</script>

<template>
  <div class="security-info" :data-platform="platform.toLowerCase()">
    <h2 class="vp-doc-heading" :id="'security-information'" tabindex="-1">
      Security Information
      <a class="header-anchor" href="#security-information" aria-hidden="true">#</a>
    </h2>
    
    <div class="security-content">
      <div class="header-with-controls">
        <div class="controls">
          <button @click="expandAllVersions" class="control-button expand-all">
            <span class="button-icon">+</span>
            <span class="button-text">Expand All</span>
          </button>
          <button @click="collapseAllVersions" class="control-button collapse-all">
            <span class="button-icon">−</span>
            <span class="button-text">Collapse All</span>
          </button>
        </div>
      </div>
      
      <div v-if="securityUpdates.length === 0" class="no-data">
        <slot name="no-data">
          <p>No security information available.</p>
        </slot>
      </div>
      
      <div v-else class="security-updates">
        <div 
          v-for="update in securityUpdates" 
          :key="update.version" 
          class="security-update-card"
          :data-version="update.version"
        >
          <div class="update-header" @click="toggleVersion(update.version)">
            <div class="version-info">
              <div class="version-header">
                <h3>{{ platform === 'iOS' ? `iOS ${update.version} and iPadOS ${update.version}` : `${platform} ${update.version}` }}</h3>
                <span class="header-divider">•</span>
                <span class="header-date">{{ formatDate(update.releaseDate) }}</span>
                <span class="header-divider">•</span>
                <div class="header-stats">
                  <span class="stat-badge" :class="{ 'has-cves': update.vulnerabilitiesCount > 0 }">
                    {{ update.vulnerabilitiesCount }} {{ update.vulnerabilitiesCount === 1 ? 'CVE' : 'CVEs' }}
                  </span>
                  <span v-if="update.activelyExploited && update.activelyExploited.length > 0" class="stat-badge kev-badge">
                    {{ update.activelyExploited.length }} KEV
                  </span>
                  <span v-if="hasHighRisk(update)" class="risk-indicator high-risk">
                    Mitigates Critical Risk
                  </span>
                </div>
              </div>
              
              <!-- Additional summary when collapsed -->
              <div v-if="!isVersionExpanded(update.version) && update.daysToPrevRelease" class="collapsed-extra">
                <span class="extra-info">{{ update.daysToPrevRelease }} days since previous release</span>
              </div>
            </div>
            <div class="expand-icon">
              {{ isVersionExpanded(update.version) ? '−' : '+' }}
            </div>
          </div>
          
          <!-- v2 Update Summary and Context -->
          <div v-if="update.updateSummary || update.securityInfoContext" class="update-summary-section">
            <div v-if="update.updateSummary" class="update-summary">
              <div v-if="update.updateSummary.Summary" class="summary-text">
                <span class="summary-icon">⚠️</span>
                {{ update.updateSummary.Summary }}
              </div>
              <div v-if="update.updateSummary.Recommendation" class="recommendation-text">
                <strong>Recommendation:</strong> {{ update.updateSummary.Recommendation }}
              </div>
            </div>
            <div v-if="update.securityInfoContext" class="security-context">
              <span class="context-icon">ℹ️</span>
              {{ update.securityInfoContext }}
            </div>
          </div>
          
          <div v-if="isVersionExpanded(update.version)" class="update-details">
            <div v-if="update.securityInfoLink" class="update-section">
              <div class="section-label">Security Info:</div>
              <div class="section-content">
                <a :href="update.securityInfoLink" target="_blank" rel="noopener noreferrer">
                  {{ update.securityInfoLink }}
                </a>
              </div>
            </div>
            
            <div v-if="update.releaseNotes" class="update-section">
              <div class="section-label">Release Notes:</div>
              <div class="section-content">{{ update.releaseNotes }}</div>
            </div>
            
            <div class="update-section">
              <div class="section-label">Vulnerabilities Addressed:</div>
              <div class="section-content">{{ update.vulnerabilitiesCount }}</div>
            </div>

            <div v-if="update.daysToPrevRelease" class="update-section">
              <div class="section-label">Days to Prev. Release:</div>
              <div class="section-content">{{ update.daysToPrevRelease }}</div>
            </div>

            <div v-if="update.activelyExploited && update.activelyExploited.length > 0" class="update-section">
              <div class="section-label">Actively Exploited Vulnerabilities (KEV):</div>
              <div class="section-content">
                <div class="cve-list">
                  <a 
                    v-for="cve in update.activelyExploited" 
                    :key="cve.cve" 
                    :href="cve.link" 
                    class="cve-link exploited"
                  >
                    🔥 {{ cve.cve }}
                  </a>
                </div>
              </div>
            </div>
            
            <div v-if="update.cves && update.cves.length > 0" class="update-section">
              <div class="section-label">CVEs:</div>
              <div class="section-content">
                <template v-if="update.cves.length < 20">
                  <div class="cve-list">
                    <a 
                      v-for="cve in update.cves.sort((a, b) => extractCveNumber(b) - extractCveNumber(a))" 
                      :key="cve.cve" 
                      :href="cve.link" 
                      class="cve-link"
                    >
                      <span v-if="isActivelyExploited(cve, update.activelyExploited)" class="exploited-dot"></span>
                      {{ cve.cve }}
                    </a>
                  </div>
                </template>
                
                <template v-else>
                  <div class="cve-groups-header">
                    <div class="cve-groups-title">CVE Groups</div>
                    <div class="cve-groups-controls">
                      <button 
                        @click.stop="expandAllCVEGroups(update.version, groupCVEs(update.cves))" 
                        class="cve-control-button"
                        :class="{ 'disabled': areAllCVEGroupsExpanded(update.version, groupCVEs(update.cves)) }"
                      >
                        Expand All
                      </button>
                      <button 
                        @click.stop="collapseAllCVEGroups(update.version, groupCVEs(update.cves))" 
                        class="cve-control-button"
                      >
                        Collapse All
                      </button>
                    </div>
                  </div>
                  
                  <div class="cve-groups">
                    <div 
                      v-for="group in getSortedGroupKeys(groupCVEs(update.cves))" 
                      :key="group" 
                      class="cve-group"
                    >
                      <div 
                        class="group-header" 
                        @click.stop="toggleCVEGroup(update.version, group)"
                      >
                        <span class="group-name">{{ group }}xx</span>
                        <span class="group-count">({{ groupCVEs(update.cves)[group].length }} CVEs)</span>
                        <span class="group-toggle">
                          {{ isCVEGroupExpanded(update.version, group) ? '−' : '+' }}
                        </span>
                      </div>
                      
                      <div 
                        v-if="isCVEGroupExpanded(update.version, group)" 
                        class="group-cves"
                      >
                        <a 
                          v-for="cve in groupCVEs(update.cves)[group]" 
                          :key="cve.cve" 
                          :href="cve.link" 
                          class="cve-link"
                        >
                          <span v-if="isActivelyExploited(cve, update.activelyExploited)" class="exploited-dot"></span>
                          {{ cve.cve }}
                        </a>
                      </div>
                    </div>
                  </div>
                </template>
              </div>
            </div>

            <!-- Slot for custom content -->
            <slot name="update-extra" :update="update"></slot>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.security-info {
  margin-bottom: 2rem;
  font-size: 0.9375rem; /* Smaller typography */
}

.header-with-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.header-with-controls h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.controls {
  display: flex;
  gap: 0.5rem;
}

.control-button {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.875rem;
  border-radius: 8px;
  border: 1px solid #E2E8F0;
  background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
  font-size: 0.75rem;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.control-button:hover {
  background: linear-gradient(135deg, #F1F5F9 0%, #E2E8F0 100%);
  border-color: #CBD5E1;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.button-icon {
  font-size: 0.9375rem;
  font-weight: 600;
}

.expand-all .button-icon {
  color: #10B981;
}

.collapse-all .button-icon {
  color: #64748B;
}

.control-button:active {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.no-data {
  padding: 2rem;
  text-align: center;
  background-color: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  color: #6b7280;
  font-size: 0.875rem;
}

.security-updates {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Platform-specific security update cards */
.security-info[data-platform="macos"] .security-update-card:hover {
  border-color: #F472B6;
}

.security-info[data-platform="ios"] .security-update-card:hover,
.security-info[data-platform="ipados"] .security-update-card:hover {
  border-color: #60A5FA;
}

/* Default styling */
.security-update-card {
  background-color: #ffffff;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;
  overflow: hidden;
}

.security-update-card:hover {
  border-color: #A78BFA;
}

.security-update-card.highlight-version {
  animation: highlight-pulse 2s ease-in-out;
}

@keyframes highlight-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0);
  }
  20% {
    box-shadow: 0 0 0 6px rgba(59, 130, 246, 0.3);
    border-color: #3b82f6;
  }
  80% {
    box-shadow: 0 0 0 6px rgba(59, 130, 246, 0.3);
    border-color: #3b82f6;
  }
  100% {
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0);
  }
}

/* Dark mode security-update-card - with purple hover accent */
:root.dark .security-update-card,
.dark .security-update-card,
html.dark .security-update-card,
.security-info:where(.dark, :root.dark, html.dark) .security-update-card {
  background-color: rgba(31, 41, 55, 0.3) !important;
  border-color: rgba(55, 65, 81, 0.3) !important;
  backdrop-filter: none !important;
}

:root.dark .security-update-card:hover,
.dark .security-update-card:hover,
html.dark .security-update-card:hover,
.security-info:where(.dark, :root.dark, html.dark) .security-update-card:hover {
  background-color: rgba(31, 41, 55, 0.4) !important;
  border-color: rgba(147, 51, 234, 0.5) !important;
  backdrop-filter: none !important;
}

.update-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem;
  cursor: pointer;
  transition: all 0.15s ease;
  background-color: transparent;
}

.update-header:hover {
  background-color: transparent;
}

.version-header {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.version-info h3 {
  margin: 0;
  font-size: 0.9375rem;
  font-weight: 600;
  color: #111827;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

/* Platform-specific version header shield icons */
.security-info[data-platform="macos"] .version-info h3:before {
  content: "";
  width: 1.5rem;
  height: 1.5rem;
  background-color: #FCE7F3;
  border-radius: 0.375rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23BE185D' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z'/%3E%3C/svg%3E");
  background-size: 1rem;
  background-repeat: no-repeat;
  background-position: center;
}

.security-info[data-platform="ios"] .version-info h3:before,
.security-info[data-platform="ipados"] .version-info h3:before {
  content: "";
  width: 1.5rem;
  height: 1.5rem;
  background-color: #EBF4FF;
  border-radius: 0.375rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%231E40AF' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z'/%3E%3C/svg%3E");
  background-size: 1rem;
  background-repeat: no-repeat;
  background-position: center;
}

/* Default for other platforms */
.version-info h3:before {
  content: "";
  width: 1.5rem;
  height: 1.5rem;
  background-color: rgba(59, 130, 246, 0.1);
  border-radius: 0.375rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%233b82f6' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z'/%3E%3C/svg%3E");
  background-size: 1rem;
  background-repeat: no-repeat;
  background-position: center;
}

/* Dark mode shield icons */
:root.dark .security-info[data-platform="macos"] .version-info h3:before,
.dark .security-info[data-platform="macos"] .version-info h3:before,
html.dark .security-info[data-platform="macos"] .version-info h3:before {
  background-color: rgba(131, 24, 67, 0.4);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23F472B6' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z'/%3E%3C/svg%3E");
}

:root.dark .security-info[data-platform="ios"] .version-info h3:before,
.dark .security-info[data-platform="ios"] .version-info h3:before,
html.dark .security-info[data-platform="ios"] .version-info h3:before,
:root.dark .security-info[data-platform="ipados"] .version-info h3:before,
.dark .security-info[data-platform="ipados"] .version-info h3:before,
html.dark .security-info[data-platform="ipados"] .version-info h3:before {
  background-color: rgba(30, 41, 59, 0.4);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2360A5FA' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z'/%3E%3C/svg%3E");
}

:root.dark .version-info h3:before,
.dark .version-info h3:before,
html.dark .version-info h3:before {
  background-color: rgba(30, 41, 59, 0.4);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2360A5FA' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z'/%3E%3C/svg%3E");
}

.header-divider {
  color: #9ca3af;
  font-size: 0.75rem;
  user-select: none;
}

.header-date {
  color: #4B5563;
  font-size: 0.875rem;
  font-weight: 500;
}

.header-stats {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
}

.stat-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.125rem 0.375rem;
  background: #F1F5F9;
  border: 1px solid #E2E8F0;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 500;
  color: #64748B;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.stat-badge::before {
  content: '';
  width: 0.75rem;
  height: 0.75rem;
  display: inline-block;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%236b7280' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z'/%3E%3C/svg%3E");
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}

.stat-badge.has-cves {
  background: #EBF4FF;
  border: 1px solid #BFDBFE;
  color: #1E40AF;
  box-shadow: 0 1px 2px rgba(30, 64, 175, 0.1);
}

.stat-badge.has-cves::before {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%233b82f6' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z'/%3E%3C/svg%3E");
}

.stat-badge.kev-badge {
  background: #FEF2F2;
  border: 1px solid #FECACA;
  color: #DC2626;
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(220, 38, 38, 0.1);
}

.stat-badge.kev-badge::before {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23dc2626' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z'/%3E%3C/svg%3E");
}

.risk-indicator {
  display: inline-flex;
  align-items: center;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-size: 0.625rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.risk-indicator.high-risk {
  background: #E11D48;
  color: white;
  border: 1px solid #BE185D;
  box-shadow: 0 1px 2px rgba(225, 29, 72, 0.15);
}

.collapsed-extra {
  margin-top: 0.375rem;
  font-size: 0.75rem;
  color: #4B5563;
}

.extra-info {
  font-style: italic;
}


.expand-icon {
  font-size: 1.25rem;
  font-weight: 300;
  color: #6b7280;
}

:root.dark .expand-icon,
.dark .expand-icon,
html.dark .expand-icon {
  color: #9ca3af !important;
}

/* v2 Update Summary Styles */
.update-summary-section {
  padding: 0.75rem 1.25rem;
  background: rgba(59, 130, 246, 0.05);
  border-top: 1px solid rgba(59, 130, 246, 0.1);
}

.update-summary {
  margin-bottom: 0.5rem;
}

.summary-text {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #1f2937;
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.summary-icon {
  font-size: 1rem;
  margin-top: 0.075rem;
  flex-shrink: 0;
  line-height: 1;
}

.recommendation-text {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #dc2626;
  margin-left: 0;
  line-height: 1.4;
}

.recommendation-text strong {
  flex-shrink: 0;
  margin-top: 0.125rem;
}

.security-context {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  font-size: 0.8125rem;
  color: #374151;
  font-style: italic;
  font-weight: 500;
  line-height: 1.4;
}

.context-icon {
  font-size: 0.875rem;
  margin-top: 0.075rem;
  flex-shrink: 0;
  line-height: 1;
}

/* Dark mode for v2 summary */
:root.dark .update-summary-section,
.dark .update-summary-section,
html.dark .update-summary-section {
  background: rgba(59, 130, 246, 0.1);
  border-top-color: rgba(59, 130, 246, 0.2);
}

:root.dark .summary-text,
.dark .summary-text,
html.dark .summary-text {
  color: #e5e7eb;
}

:root.dark .recommendation-text,
.dark .recommendation-text,
html.dark .recommendation-text {
  color: #f87171;
}

:root.dark .security-context,
.dark .security-context,
html.dark .security-context {
  color: #9ca3af;
}

.update-details {
  padding: 0 1.25rem 1.25rem;
  border-top: 1px solid #f3f4f6;
  background: transparent;
}

.update-section {
  margin-top: 0.875rem;
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 0.75rem;
}

.section-label {
  color: #374151;
  font-weight: 600;
  font-size: 0.875rem;
}

:root.dark .section-label,
.dark .section-label,
html.dark .section-label {
  color: #9ca3af !important;
}

.section-content {
  color: #111827;
  font-size: 0.875rem;
  font-weight: 500;
}

.section-content a {
  color: #2563eb;
  text-decoration: none;
}

.section-content a:hover {
  text-decoration: underline;
}

:root.dark .section-content a,
.dark .section-content a {
  color: #60a5fa;
}

:root.dark .section-content a:hover,
.dark .section-content a:hover {
  color: #93c5fd;
}

.cve-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}

.cve-link {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.5rem;
  background: #EBF4FF;
  border: 1px solid #BFDBFE;
  border-radius: 6px;
  font-family: monospace;
  font-size: 0.75rem;
  font-weight: 600;
  color: #1E40AF;
  text-decoration: none;
  transition: all 0.15s ease;
  position: relative;
  box-shadow: 0 1px 2px rgba(30, 64, 175, 0.08);
}

.cve-link:hover {
  background: #DBEAFE;
  border-color: #93C5FD;
  color: #1D4ED8;
  box-shadow: 0 2px 4px rgba(30, 64, 175, 0.15);
}

/* Specific styling for the dedicated actively exploited section */
.cve-link.exploited {
  background: #fef2f2;
  border-color: #fecaca;
  color: #dc2626;
}

.cve-link.exploited:hover {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #b91c1c;
}

/* Red dot for actively exploited CVEs */
.exploited-dot {
  width: 6px;
  height: 6px;
  background-color: #ff3b30;
  border-radius: 50%;
  display: inline-block;
  margin-right: 4px;
}

/* CVE Groups Header with controls */
.cve-groups-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.cve-groups-title {
  font-weight: 600;
  font-size: 0.875rem;
  color: #111827;
}

:root.dark .cve-groups-title,
.dark .cve-groups-title,
html.dark .cve-groups-title {
  color: #e5e7eb !important;
}

.cve-groups-controls {
  display: flex;
  gap: 0.5rem;
}

.cve-control-button {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
  background-color: #f9fafb;
  color: #111827;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.cve-control-button:hover {
  background-color: #f3f4f6;
}

.cve-control-button.disabled {
  opacity: 0.5;
  cursor: default;
}

.cve-groups {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.cve-group {
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.group-header {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #F8FAFC;
  border-bottom: 1px solid #E2E8F0;
  cursor: pointer;
  transition: all 0.15s ease;
}

.group-header:hover {
  background: #F1F5F9;
  border-bottom-color: #CBD5E1;
}

.group-name {
  font-family: monospace;
  font-weight: 600;
  font-size: 0.875rem;
  color: #111827;
}

:root.dark .group-name,
.dark .group-name,
html.dark .group-name {
  color: #e5e7eb !important;
}

.group-count {
  margin-left: 0.375rem;
  color: #6b7280;
  font-size: 0.75rem;
}

:root.dark .group-count,
.dark .group-count,
html.dark .group-count {
  color: #9ca3af !important;
}

.group-toggle {
  margin-left: auto;
  font-size: 1.125rem;
  font-weight: 300;
  color: #6b7280;
}

:root.dark .group-toggle,
.dark .group-toggle,
html.dark .group-toggle {
  color: #9ca3af !important;
}

.group-cves {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  padding: 0.75rem;
  background-color: #ffffff;
}

/* Enhanced dark mode support */

:root.dark .version-info h3,
.dark .version-info h3,
html.dark .version-info h3 {
  color: #e2e8f0 !important;
}

:root.dark .update-details,
.dark .update-details,
html.dark .update-details {
  background: transparent !important;
  border-top-color: rgba(71, 85, 105, 0.3) !important;
}

:root.dark .cve-link,
.dark .cve-link,
html.dark .cve-link {
  background: rgba(75, 85, 99, 0.5) !important;
  border-color: rgba(107, 114, 128, 0.5) !important;
  color: #93c5fd !important;
  box-shadow: none;
}

:root.dark .cve-link:hover,
.dark .cve-link:hover,
html.dark .cve-link:hover {
  background: rgba(107, 114, 128, 0.7) !important;
  border-color: rgba(156, 163, 175, 0.7) !important;
  color: #dbeafe !important;
  box-shadow: none;
}

:root.dark .cve-link.exploited,
.dark .cve-link.exploited,
html.dark .cve-link.exploited {
  background: rgba(220, 38, 38, 0.5) !important;
  border-color: rgba(239, 68, 68, 0.5) !important;
  color: #fca5a5 !important;
  box-shadow: none;
}

:root.dark .cve-link.exploited:hover,
.dark .cve-link.exploited:hover,
html.dark .cve-link.exploited:hover {
  background: rgba(239, 68, 68, 0.7) !important;
  border-color: rgba(248, 113, 113, 0.7) !important;
  color: #fecaca !important;
  box-shadow: none;
}

/* Dark mode support for VitePress */
:root.dark .security-info,
.dark .security-info,
html.dark .security-info {
  /* Control buttons */
  --control-bg: rgba(31, 41, 55, 0.5);
  --control-border: rgba(55, 65, 81, 0.5);
  --control-text: #f5f5f7;
  --control-hover-bg: rgba(31, 41, 55, 0.7);
  --control-hover-border: rgba(75, 85, 99, 0.6);
  
  /* Card and sections */
  --card-bg: transparent;
  --card-header-bg: transparent;
  --card-header-hover: transparent;
  --card-border: rgba(55, 65, 81, 0.3);
  --card-text: #f5f5f7;
  --card-text-secondary: #8e8e93;
  
  /* CVE links */
  --cve-bg: rgba(75, 85, 99, 0.5);
  --cve-hover-bg: rgba(107, 114, 128, 0.7);
  --cve-text: #93c5fd;
  --cve-exploited-text: #fca5a5;
  --cve-dot: #ff453a;
  
  /* Group headers */
  --group-header-bg: rgba(31, 41, 55, 0.5);
  --group-header-hover: rgba(55, 65, 81, 0.7);
  
  /* No data */
  --no-data-bg: rgba(31, 41, 55, 0.3);
  --no-data-text: #8e8e93;
  
  /* CVE controls */
  --cve-control-bg: rgba(31, 41, 55, 0.5);
  --cve-control-hover-bg: rgba(31, 41, 55, 0.7);
  --cve-control-border: rgba(55, 65, 81, 0.5);
  --cve-control-text: #f5f5f7;
}

@media (prefers-color-scheme: dark) {
  .security-info {
    /* Control buttons */
    --control-bg: rgba(31, 41, 55, 0.5);
    --control-border: rgba(55, 65, 81, 0.5);
    --control-text: #f5f5f7;
    --control-hover-bg: rgba(31, 41, 55, 0.7);
    --control-hover-border: rgba(75, 85, 99, 0.6);
    
    /* Card and sections */
    --card-bg: transparent;
    --card-header-bg: transparent;
    --card-header-hover: transparent;
    --card-border: rgba(55, 65, 81, 0.3);
    --card-text: #f5f5f7;
    --card-text-secondary: #8e8e93;
    
    /* CVE links */
    --cve-bg: rgba(75, 85, 99, 0.5);
    --cve-hover-bg: rgba(107, 114, 128, 0.7);
    --cve-text: #93c5fd;
    --cve-exploited-text: #fca5a5;
    --cve-dot: #ff453a;
    
    /* Group headers */
    --group-header-bg: rgba(31, 41, 55, 0.5);
    --group-header-hover: rgba(55, 65, 81, 0.7);
    
    /* No data */
    --no-data-bg: rgba(31, 41, 55, 0.3);
    --no-data-text: #8e8e93;
    
    /* CVE controls */
    --cve-control-bg: rgba(31, 41, 55, 0.5);
    --cve-control-hover-bg: rgba(31, 41, 55, 0.7);
    --cve-control-border: rgba(55, 65, 81, 0.5);
    --cve-control-text: #f5f5f7;
  }
}

/* Apply dark mode variables */
:root.dark .control-button,
.dark .control-button,
html.dark .control-button,
.security-info:where(.dark, :root.dark, html.dark) .control-button {
  background: rgba(30, 41, 59, 0.5);
  border-color: rgba(51, 65, 85, 0.5);
  color: #f3f4f6;
  backdrop-filter: blur(10px);
}

:root.dark .control-button:hover,
.dark .control-button:hover,
html.dark .control-button:hover,
.security-info:where(.dark, :root.dark, html.dark) .control-button:hover {
  background: rgba(30, 41, 59, 0.7);
  border-color: rgba(71, 85, 105, 0.6);
}


:root.dark .update-header,
.dark .update-header,
html.dark .update-header,
.security-info:where(.dark, :root.dark, html.dark) .update-header {
  background-color: transparent !important;
}

:root.dark .update-header:hover,
.dark .update-header:hover,
html.dark .update-header:hover,
.security-info:where(.dark, :root.dark, html.dark) .update-header:hover {
  background-color: transparent !important;
}

:root.dark .version-info h3,
.dark .version-info h3,
html.dark .version-info h3,
.security-info:where(.dark, :root.dark, html.dark) .version-info h3 {
  color: var(--card-text, #f5f5f7);
}

:root.dark .section-content,
.dark .section-content,
html.dark .section-content,
.security-info:where(.dark, :root.dark, html.dark) .section-content {
  color: var(--card-text, #f5f5f7);
}

:root.dark .stat-badge,
.dark .stat-badge,
html.dark .stat-badge {
  background: rgba(51, 65, 85, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.6);
  color: #CBD5E1;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

:root.dark .stat-badge::before,
.dark .stat-badge::before,
html.dark .stat-badge::before {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23d1d5db' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z'/%3E%3C/svg%3E");
}

:root.dark .stat-badge.has-cves,
.dark .stat-badge.has-cves,
html.dark .stat-badge.has-cves {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

:root.dark .stat-badge.has-cves::before,
.dark .stat-badge.has-cves::before,
html.dark .stat-badge.has-cves::before {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2360a5fa' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z'/%3E%3C/svg%3E");
}

:root.dark .stat-badge.kev-badge,
.dark .stat-badge.kev-badge,
html.dark .stat-badge.kev-badge {
  background: rgba(220, 38, 38, 0.2);
  color: #f87171;
}

:root.dark .stat-badge.kev-badge::before,
.dark .stat-badge.kev-badge::before,
html.dark .stat-badge.kev-badge::before {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23f87171' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z'/%3E%3C/svg%3E");
}

:root.dark .risk-indicator.high-risk,
.dark .risk-indicator.high-risk,
html.dark .risk-indicator.high-risk {
  background: #B91C1C;
  border: 1px solid #991B1B;
  box-shadow: 0 1px 2px rgba(185, 28, 28, 0.3);
}

:root.dark .header-divider,
.dark .header-divider,
html.dark .header-divider {
  color: #4b5563;
}

:root.dark .header-date,
.dark .header-date,
html.dark .header-date {
  color: #9ca3af;
}

:root.dark .collapsed-extra,
.dark .collapsed-extra,
html.dark .collapsed-extra {
  color: #D1D5DB;
}



:root.dark .exploited-dot,
.dark .exploited-dot,
html.dark .exploited-dot,
.security-info:where(.dark, :root.dark, html.dark) .exploited-dot {
  background-color: var(--cve-dot, #ff453a);
}

:root.dark .group-header,
.dark .group-header,
html.dark .group-header,
.security-info:where(.dark, :root.dark, html.dark) .group-header {
  background: rgba(30, 41, 59, 0.6);
  border-bottom: 1px solid rgba(71, 85, 105, 0.6);
}

:root.dark .group-header:hover,
.dark .group-header:hover,
html.dark .group-header:hover,
.security-info:where(.dark, :root.dark, html.dark) .group-header:hover {
  background: rgba(51, 65, 85, 0.7);
  border-bottom-color: rgba(100, 116, 139, 0.7);
}

:root.dark .group-cves,
.dark .group-cves,
html.dark .group-cves,
.security-info:where(.dark, :root.dark, html.dark) .group-cves {
  background-color: var(--card-bg, #1c1c1e);
}

:root.dark .no-data,
.dark .no-data,
html.dark .no-data,
.security-info:where(.dark, :root.dark, html.dark) .no-data {
  background-color: var(--no-data-bg, #2c2c2e);
  color: var(--no-data-text, #8e8e93);
}

:root.dark .update-details,
.dark .update-details,
html.dark .update-details,
.security-info:where(.dark, :root.dark, html.dark) .update-details {
  border-top: 1px solid var(--card-border, #3c3c3e);
  background-color: var(--card-bg, #1c1c1e);
}

:root.dark .cve-group,
.dark .cve-group,
html.dark .cve-group,
.security-info:where(.dark, :root.dark, html.dark) .cve-group {
  border: 1px solid var(--card-border, #3c3c3e);
}

:root.dark .cve-control-button,
.dark .cve-control-button,
html.dark .cve-control-button,
.security-info:where(.dark, :root.dark, html.dark) .cve-control-button {
  background: rgba(30, 41, 59, 0.5);
  border-color: rgba(51, 65, 85, 0.5);
  color: #f3f4f6;
  backdrop-filter: blur(10px);
}

:root.dark .cve-control-button:hover,
.dark .cve-control-button:hover,
html.dark .cve-control-button:hover,
.security-info:where(.dark, :root.dark, html.dark) .cve-control-button:hover {
  background: rgba(30, 41, 59, 0.7);
  border-color: rgba(71, 85, 105, 0.6);
}

/* Mobile-specific styles */
@media (max-width: 480px) {
  /* CVE Groups header container */
  .cve-groups-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    text-align: left;
  }

  /* CVE Groups title */
  .cve-groups-title {
    text-align: left;
  }

  /* Container for all CVE groups */
  .cve-groups {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    width: 100%;
  }

  /* Individual CVE group */
  .cve-group {
    width: 100%;
    text-align: left;
  }

  /* Group header with CVE prefix and count */
  .group-header {
    display: flex;
    justify-content: flex-start;
    align-items: center;
    width: 100%;
    padding: 0.625rem 0.875rem;
  }

  .group-name {
    text-align: left;
    margin-right: 0.5rem;
  }

  .group-count {
    margin-right: auto;
  }

  /* Container for CVEs within a group */
  .group-cves {
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: flex-start;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 0.5rem;
    width: 100%;
  }

  /* Individual CVE links */
  .cve-link {
    text-align: left;
  }

  /* Controls container */
  .cve-groups-controls {
    display: flex;
    gap: 0.5rem;
    margin-left: auto;
  }
}

/* Enhanced Mobile UX - Optimized for excellent user experience */
@media (max-width: 480px) {
  /* Optimize container padding for better touch interaction */
  .update-content {
    padding: 1rem 0.75rem;
  }
  
  /* CVE Groups header - Clear visual hierarchy */
  .cve-groups-header {
    flex-direction: column;
    align-items: stretch;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--vp-c-divider-light);
  }
  
  /* Control buttons - Better touch targets */
  .cve-groups-controls {
    width: 100%;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
  }
  
  /* CVE links - Better touch targets with visual breathing room */
  .cve-link {
    padding: 0.375rem 0.5rem !important;
    font-size: 0.8125rem !important;
    margin: 0.125rem;
    display: inline-block;
    word-break: break-word;
    min-height: 32px;
    display: inline-flex;
    align-items: center;
    border-radius: 6px;
    transition: all 0.15s ease;
  }
  
  /* CVE groups container - Better spacing */
  .cve-groups {
    gap: 0.625rem;
    width: 100%;
  }
  
  /* Group headers - Better touch targets */
  .group-header {
    padding: 0.75rem !important;
    font-size: 0.875rem;
    min-height: 44px;
    display: flex;
    align-items: center;
  }
  
  /* Group CVEs container - Smooth scrolling with visual indicators */
  .group-cves {
    padding: 0.625rem !important;
    gap: 0.375rem !important;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: thin;
  }
  
  .group-cves::-webkit-scrollbar {
    height: 4px;
  }
  
  .group-cves::-webkit-scrollbar-track {
    background: var(--vp-c-divider-light);
    border-radius: 2px;
  }
  
  .group-cves::-webkit-scrollbar-thumb {
    background: var(--vp-c-text-3);
    border-radius: 2px;
  }
  
  /* Control buttons - Minimum 44px touch target */
  .cve-control-button {
    padding: 0.625rem 0.75rem !important;
    font-size: 0.75rem !important;
    min-height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    font-weight: 600;
  }
  
  /* Update header - Better touch target for expand/collapse */
  .update-header {
    padding: 1rem;
    min-height: 60px;
    display: flex;
    align-items: center;
  }
  
  /* Update sections - Clear visual separation */
  .update-section {
    padding: 0.875rem 0.75rem;
    display: flex;
    flex-direction: column !important;
    gap: 0.375rem;
    border-bottom: 1px solid var(--vp-c-divider-light);
  }
  
  .update-section:last-child {
    border-bottom: none;
  }
  
  .section-label {
    font-size: 0.6875rem;
    font-weight: 600;
    color: var(--vp-c-text-3);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 0.25rem;
  }
  
  .section-content {
    font-size: 0.9375rem;
    font-weight: 500;
    color: var(--vp-c-text-1);
    margin-left: 0 !important;
  }
  
  /* Fix overflow for entire update details */
  .update-details {
    overflow-x: hidden;
  }
  
  /* CVE group box - Better visual hierarchy */
  .cve-group {
    max-width: 100%;
    overflow: hidden;
    border-radius: 8px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  }
}

/* iPhone 12/13/14 Pro (390px) - Maintain good UX */
@media (max-width: 390px) {
  .cve-link {
    padding: 0.3rem 0.4rem !important;
    font-size: 0.75rem !important;
  }
  
  .update-content {
    padding: 0.875rem 0.625rem;
  }
  
  /* Control buttons still need 44px touch target */
  .cve-control-button {
    padding: 0.5rem 0.625rem !important;
    font-size: 0.7rem !important;
    min-height: 44px;
  }
  
  /* Stack expand/collapse buttons if needed */
  .controls {
    flex-direction: column;
    width: 100%;
  }
  
  .control-button {
    width: 100%;
    justify-content: center;
  }
}

/* iPhone SE and older (375px) - Prioritize usability */
@media (max-width: 375px) {
  .cve-link {
    padding: 0.25rem 0.375rem !important;
    font-size: 0.7rem !important;
    min-height: 30px;
  }
  
  /* CVE groups title */
  .cve-groups-title {
    font-size: 0.875rem;
    font-weight: 700;
  }
  
  /* Ensure minimum spacing */
  .update-section {
    padding: 0.75rem 0.625rem;
  }
}
</style>
