<template>
  <div class="feed-container">
    <div class="feed-header">
      <h2 class="feed-title">SOFA JSON Feed Endpoints</h2>
      <div class="feed-badge">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 5c7.18 0 13 5.82 13 13M6 11a7 7 0 017 7m-6 0a1 1 0 11-2 0 1 1 0 012 0z"/>
        </svg>
        Live Feeds
      </div>
    </div>

    <div class="feed-intro">
      <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
      </svg>
      <p>
        These JSON feeds provide up to date Apple software update data for integration into your tools and workflows.
        All feeds are publicly accessible and updated automatically every 6 hours.
      </p>
    </div>

    <!-- Main Feeds Section -->
    <div class="feeds-section">
      <h3 class="section-title">Platform Data Feeds</h3>
      <div class="feeds-grid">
        <div v-for="feed in mainFeeds" :key="feed.id" class="feed-card">
          <div class="feed-icon-wrapper">
            <component :is="feed.icon" class="feed-icon" />
          </div>
          <div class="feed-content">
            <h4 class="feed-name">{{ feed.name }}</h4>
            <p class="feed-description">{{ feed.description }}</p>
            <div class="feed-url-wrapper">
              <code class="feed-url">{{ feed.url }}</code>
              <button @click="copyToClipboard(feed.url, feed.id)" class="copy-btn">
                <svg v-if="copiedId !== feed.id" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                </svg>
                <svg v-else class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
              </button>
            </div>
            <div class="feed-meta">
              <span class="meta-item">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                Updates every 6 hrs
              </span>
              <span class="meta-item">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
                JSON format
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Beta Feed Section -->
    <div class="feeds-section">
      <h3 class="section-title">Beta & Special Feeds</h3>
      <div class="feeds-grid">
        <div v-for="feed in betaFeeds" :key="feed.id" class="feed-card special">
          <div class="feed-icon-wrapper special">
            <component :is="feed.icon" class="feed-icon" />
          </div>
          <div class="feed-content">
            <h4 class="feed-name">{{ feed.name }}</h4>
            <p class="feed-description">{{ feed.description }}</p>
            <div class="feed-url-wrapper">
              <code class="feed-url">{{ feed.url }}</code>
              <button @click="copyToClipboard(feed.url, feed.id)" class="copy-btn">
                <svg v-if="copiedId !== feed.id" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                </svg>
                <svg v-else class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Usage Examples -->
    <div class="usage-section">
      <h3 class="section-title">Usage Examples</h3>
      <div class="examples-grid">
        <div class="example-card">
          <div class="example-header">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v14a2 2 0 002 2z"/>
            </svg>
            <h4>Command Line (curl + jq)</h4>
          </div>
          <p class="example-desc">Get latest macOS version and security info</p>
          <pre><code># Get latest macOS release
curl -s ${apiBase}/v2/macos_data_feed.json | jq '.OSVersions[0].Latest'

# Check for actively exploited CVEs
curl -s ${apiBase}/v2/ios_data_feed.json | jq '.OSVersions[0].Latest.ActivelyExploitedCVEs'</code></pre>
        </div>
        
        <div class="example-card">
          <div class="example-header">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/>
            </svg>
            <h4>Python Integration</h4>
          </div>
          <p class="example-desc">Security update monitoring and alerting</p>
          <pre><code>import requests
from datetime import datetime

# Get security data
response = requests.get('${apiBase}/v2/ios_data_feed.json')
data = response.json()

# Check latest release
latest = data['OSVersions'][0]['Latest']
cve_count = latest.get('UniqueCVEsCount', 0)
exploited = len(latest.get('ActivelyExploitedCVEs', []))

print(f"iOS {latest['ProductVersion']} - {cve_count} CVEs, {exploited} exploited")</code></pre>
        </div>
        
        
        <div class="example-card">
          <div class="example-header">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 0V17m0 0a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"/>
            </svg>
            <h4>Excel/PowerBI</h4>
          </div>
          <p class="example-desc">Business intelligence and reporting</p>
          <pre><code># Power Query M Language
let
  Source = Json.Document(Web.Contents("${apiBase}/v2/macos_data_feed.json")),
  OSVersions = Source[OSVersions],
  Latest = OSVersions{0}[Latest],
  Version = Latest[ProductVersion],
  CVECount = Latest[UniqueCVEsCount]
in
  [Version = Version, CVECount = CVECount]</code></pre>
        </div>
      </div>
    </div>

    <!-- API Documentation -->
    <div class="docs-section">
      <h3 class="section-title">Feed Structure</h3>
      
      <!-- Feed Versions Tabs -->
      <div class="version-tabs">
        <button @click="selectedVersion = 'v2'" :class="['version-tab', { active: selectedVersion === 'v2' }]">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/>
          </svg>
          V2 (Current)
        </button>
        <button @click="selectedVersion = 'v1'" :class="['version-tab', { active: selectedVersion === 'v1' }]">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
          </svg>
          V1 (Legacy)
        </button>
      </div>

      <!-- V2 Structure -->
      <div v-if="selectedVersion === 'v2'" class="structure-content">
        <div class="structure-overview">
          <div class="overview-card">
            <h4>V2 Enhanced Structure</h4>
            <p>Comprehensive security intelligence with CVE details, device support, and actionable recommendations.</p>
          </div>
        </div>
        
        <div class="structure-sections">
          <div class="structure-section">
            <h4>Root Level Fields</h4>
            <div class="field-group">
              <div class="field-item"><code>OSName</code><span>Platform name (macOS, iOS, etc.)</span></div>
              <div class="field-item"><code>Version</code><span>Feed version (2.0)</span></div>
              <div class="field-item"><code>UpdateHash</code><span>Change detection hash</span></div>
              <div class="field-item"><code>LastCheck</code><span>Last update timestamp</span></div>
            </div>
          </div>

          <div class="structure-section">
            <h4>OSVersions Array</h4>
            <div class="field-group">
              <div class="field-item"><code>OSVersion</code><span>Version name (e.g., "macOS 15")</span></div>
              <div class="field-item"><code>Latest{}</code><span>Current release information</span></div>
              <div class="field-group nested">
                <div class="field-item"><code>ProductVersion</code><span>Version number</span></div>
                <div class="field-item"><code>Build</code><span>Build identifier</span></div>
                <div class="field-item"><code>ReleaseDate</code><span>ISO format release date</span></div>
                <div class="field-item"><code>SecurityInfo</code><span>Apple security bulletin URL</span></div>
                <div class="field-item"><code>SupportedDevices[]</code><span>Compatible device identifiers</span></div>
                <div class="field-item"><code>CVEs{}</code><span>Vulnerability details with NIST links</span></div>
                <div class="field-item"><code>ActivelyExploitedCVEs[]</code><span>CISA KEV list</span></div>
                <div class="field-item"><code>UpdateSummary{}</code><span>Priority and recommendations</span></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- V1 Structure -->
      <div v-if="selectedVersion === 'v1'" class="structure-content">
        <div class="structure-overview">
          <div class="overview-card legacy">
            <h4>V1 Legacy Structure</h4>
            <p>Basic version tracking without security intelligence. Maintained for compatibility only.</p>
            <div class="migration-note">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              Use V2 feeds for new projects
            </div>
          </div>
        </div>
        
        <div class="structure-sections">
          <div class="structure-section">
            <h4>Available Fields</h4>
            <div class="field-group">
              <div class="field-item"><code>UpdateHash</code><span>Change detection hash</span></div>
              <div class="field-item"><code>OSVersions[]</code><span>Array of OS version objects</span></div>
              <div class="field-group nested">
                <div class="field-item"><code>Latest{}</code><span>Current release information</span></div>
                <div class="field-group nested">
                  <div class="field-item"><code>ProductVersion</code><span>Version number</span></div>
                  <div class="field-item"><code>Build</code><span>Build identifier</span></div>
                  <div class="field-item"><code>ReleaseDate</code><span>Release date</span></div>
                </div>
              </div>
              <div class="field-item"><code>SecurityReleases[]</code><span>Historical security updates</span></div>
            </div>
          </div>

          <div class="structure-section">
            <h4>Missing in V1</h4>
            <div class="missing-features">
              <div class="missing-item">❌ CVE vulnerability details</div>
              <div class="missing-item">❌ Device compatibility lists</div>
              <div class="missing-item">❌ Security context and summaries</div>
              <div class="missing-item">❌ Update priority indicators</div>
              <div class="missing-item">❌ Actively exploited CVE tracking</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Usage Guidelines -->
      <div class="usage-guidelines">
        <h4>Integration Guidelines</h4>
        <div class="guidelines-grid">
          <div class="guideline-item">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
            </svg>
            <div>
              <h5>Authentication</h5>
              <p>No API keys required - publicly accessible</p>
            </div>
          </div>
          
          <div class="guideline-item">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <div>
              <h5>Update Frequency</h5>
              <p>Every 6 hours automatically via Cloudflare CDN</p>
            </div>
          </div>
          
          <div class="guideline-item">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            <div>
              <h5>Caching</h5>
              <p>Use UpdateHash to detect changes efficiently</p>
            </div>
          </div>
          
          <div class="guideline-item">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
            <div>
              <h5>Rate Limits</h5>
              <p>Reasonable use expected (&lt; 1000 requests/hour)</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Monitor, Smartphone, Tv, Watch as WatchIcon, Eye, Sparkles, Shield, Package } from 'lucide-vue-next'

const copiedId = ref(null)
const selectedVersion = ref('v2')

// Always use production URLs for copyable links
const apiBase = __API_BASE_PROD__ || 'https://sofa.macadmins.io'

const mainFeeds = computed(() => [
  {
    id: 'macos',
    name: 'macOS Data Feed',
    description: 'Complete macOS version data including security releases, CVEs, and installer information',
    url: `${apiBase}/v2/macos_data_feed.json`,
    icon: Monitor
  },
  {
    id: 'ios',
    name: 'iOS Data Feed',
    description: 'iOS and iPadOS version data with security updates and vulnerability information',
    url: `${apiBase}/v2/ios_data_feed.json`,
    icon: Smartphone
  },
  {
    id: 'tvos',
    name: 'tvOS Data Feed',
    description: 'tvOS version information and security updates',
    url: `${apiBase}/v2/tvos_data_feed.json`,
    icon: Tv
  },
  {
    id: 'watchos',
    name: 'watchOS Data Feed',
    description: 'watchOS version data and security releases',
    url: `${apiBase}/v2/watchos_data_feed.json`,
    icon: WatchIcon
  },
  {
    id: 'visionos',
    name: 'visionOS Data Feed',
    description: 'visionOS version information and updates',
    url: `${apiBase}/v2/visionos_data_feed.json`,
    icon: Eye
  },
  {
    id: 'safari',
    name: 'Safari Data Feed',
    description: 'Safari browser version data and security updates',
    url: `${apiBase}/v2/safari_data_feed.json`,
    icon: Shield
  }
])

const betaFeeds = [
  {
    id: 'beta',
    name: 'Apple Beta OS Feed',
    description: 'Beta releases across all Apple platforms with build numbers and release dates',
    url: 'https://beta-feed.macadmin.me/v1/apple-beta-os-feed.json',
    icon: Sparkles
  }
]

const copyToClipboard = async (text, id) => {
  try {
    await navigator.clipboard.writeText(text)
    copiedId.value = id
    setTimeout(() => {
      copiedId.value = null
    }, 2000)
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}
</script>

<style scoped>
.feed-container {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 1.5rem;
}

.feed-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.feed-title {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--vp-c-text-1);
  margin: 0;
}

.feed-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(34, 197, 94, 0.1));
  color: #10b981;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
}

.feed-intro {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: rgba(59, 130, 246, 0.05);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 8px;
  margin-bottom: 2rem;
}

.feed-intro svg {
  color: #3b82f6;
  flex-shrink: 0;
}

.feed-intro p {
  margin: 0;
  color: var(--vp-c-text-2);
  font-size: 0.9375rem;
  line-height: 1.6;
}

.feeds-section {
  margin-bottom: 2.5rem;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--vp-c-text-1);
  margin-bottom: 1rem;
}

.feeds-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 1.5rem;
}

.feed-card {
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  padding: 1.25rem;
  transition: all 0.2s ease;
}

.feed-card:hover {
  border-color: var(--vp-c-brand);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}

.feed-card.special {
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.03), rgba(236, 72, 153, 0.03));
  border-color: rgba(168, 85, 247, 0.2);
}

.feed-icon-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  background: rgba(59, 130, 246, 0.1);
  border-radius: 8px;
  margin-bottom: 1rem;
}

.feed-icon-wrapper.special {
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.15), rgba(236, 72, 153, 0.15));
}

.feed-icon {
  width: 1.25rem;
  height: 1.25rem;
  color: #3b82f6;
}

.feed-icon-wrapper.special .feed-icon {
  color: #a855f7;
}

.feed-name {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--vp-c-text-1);
  margin: 0 0 0.5rem 0;
}

.feed-description {
  font-size: 0.875rem;
  color: var(--vp-c-text-2);
  margin: 0 0 1rem 0;
  line-height: 1.5;
}

.feed-url-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.feed-url {
  flex: 1;
  padding: 0.5rem 0.75rem;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 6px;
  font-family: monospace;
  font-size: 0.75rem;
  color: var(--vp-c-text-1);
  overflow-x: auto;
  white-space: nowrap;
}

.copy-btn {
  padding: 0.5rem;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 6px;
  color: var(--vp-c-text-2);
  cursor: pointer;
  transition: all 0.2s ease;
}

.copy-btn:hover {
  background: var(--vp-c-bg-mute);
  color: var(--vp-c-text-1);
}

.feed-meta {
  display: flex;
  gap: 1rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: var(--vp-c-text-3);
}

.usage-section {
  margin-top: 4rem;
  padding-top: 3rem;
  border-top: 1px solid var(--vp-c-divider);
}

.examples-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
  gap: 2.5rem;
}

.example-card {
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  padding: 1rem;
}

.example-card h4 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--vp-c-text-1);
  margin: 0 0 0.75rem 0;
}

.example-card pre {
  margin: 0;
  padding: 0.75rem;
  background: var(--vp-c-bg);
  border-radius: 6px;
  overflow-x: auto;
}

.example-card code {
  font-size: 0.75rem;
  line-height: 1.5;
  color: var(--vp-c-text-1);
}

.docs-section {
  margin-top: 4rem;
}

.structure-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 2.5rem;
}

.structure-card {
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  padding: 0;
  overflow: hidden;
  transition: all 0.2s ease;
}

.structure-card:hover {
  border-color: var(--vp-c-brand);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: var(--vp-c-bg);
  border-bottom: 1px solid var(--vp-c-divider);
}

.card-header h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--vp-c-text-1);
}

.card-header svg {
  color: var(--vp-c-brand);
}

.field-list {
  list-style: none;
  padding: 1.25rem;
  margin: 0;
}

.field-list li {
  padding: 0.5rem 0;
  font-size: 0.875rem;
  color: var(--vp-c-text-2);
  border-bottom: 1px solid var(--vp-c-divider-light);
}

.field-list li.nested {
  padding-left: 1rem;
  color: var(--vp-c-text-3);
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
}

.field-list li.note {
  padding: 0.75rem 1rem;
  background: var(--vp-c-bg);
  border-radius: 6px;
  margin: 0.5rem 0;
  font-style: italic;
  color: var(--vp-c-text-2);
  border: none;
}

.field-list li:last-child {
  border-bottom: none;
}

.structure-card code {
  padding: 0.125rem 0.375rem;
  background: var(--vp-c-bg);
  border-radius: 4px;
  font-size: 0.8125rem;
  color: var(--vp-c-brand);
}

/* Dark mode enhancements */
:root.dark .feed-card {
  background: rgba(31, 41, 55, 0.3);
  border-color: rgba(55, 65, 81, 0.5);
}

:root.dark .feed-card:hover {
  background: rgba(31, 41, 55, 0.5);
}

:root.dark .feed-url {
  background: rgba(31, 41, 55, 0.5);
  border-color: rgba(55, 65, 81, 0.5);
}

:root.dark .copy-btn {
  background: rgba(31, 41, 55, 0.5);
  border-color: rgba(55, 65, 81, 0.5);
}

:root.dark .example-card,
:root.dark .structure-card {
  background: rgba(31, 41, 55, 0.3);
  border-color: rgba(55, 65, 81, 0.5);
}

:root.dark .example-card pre {
  background: rgba(0, 0, 0, 0.3);
}

/* Responsive design */
@media (max-width: 768px) {
  .feed-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .feeds-grid,
  .examples-grid,
  .structure-info {
    grid-template-columns: 1fr;
  }
}

/* New Feed Structure Styles */
.version-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
  border-bottom: 1px solid var(--vp-c-divider);
  padding-bottom: 1rem;
}

.version-tab {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  color: var(--vp-c-text-2);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.version-tab.active {
  background: var(--vp-c-brand);
  border-color: var(--vp-c-brand);
  color: white;
}

.version-tab:hover:not(.active) {
  background: var(--vp-c-bg);
  border-color: var(--vp-c-brand);
  color: var(--vp-c-text-1);
}

.structure-content {
  min-height: 400px;
}

.structure-overview {
  margin-bottom: 3rem;
}

.overview-card {
  background: linear-gradient(135deg, var(--vp-c-brand) 0%, var(--vp-c-brand-dark) 100%);
  color: white;
  padding: 2rem;
  border-radius: 12px;
  text-align: center;
}

.overview-card.legacy {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
}

.overview-card h4 {
  margin: 0 0 1rem 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.overview-card p {
  margin: 0 0 1rem 0;
  opacity: 0.9;
}

.migration-note {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
}

.structure-sections {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
}

.structure-section {
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  padding: 2rem;
}

.structure-section h4 {
  margin: 0 0 1.5rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--vp-c-text-1);
  border-bottom: 2px solid var(--vp-c-brand);
  padding-bottom: 0.5rem;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.field-group.nested {
  margin-left: 1.5rem;
  padding-left: 1.5rem;
  border-left: 2px solid var(--vp-c-divider);
  margin-top: 0.75rem;
}

.field-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: var(--vp-c-bg);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.field-item:hover {
  background: var(--vp-c-bg-mute);
  transform: translateX(4px);
}

.field-item code {
  flex-shrink: 0;
  min-width: 140px;
  padding: 0.25rem 0.5rem;
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand);
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.8rem;
}

.field-item span {
  color: var(--vp-c-text-2);
  font-size: 0.875rem;
}

.missing-features {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.missing-item {
  padding: 0.75rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 8px;
  color: var(--vp-c-text-1);
  font-size: 0.875rem;
}

.usage-guidelines {
  margin-top: 3rem;
  padding-top: 2rem;
  border-top: 1px solid var(--vp-c-divider);
}

.usage-guidelines h4 {
  margin: 0 0 2rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--vp-c-text-1);
  text-align: center;
}

.guidelines-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.guideline-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.5rem;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
}

.guideline-item svg {
  color: var(--vp-c-brand);
  margin-top: 0.25rem;
}

.guideline-item h5 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--vp-c-text-1);
}

.guideline-item p {
  margin: 0;
  color: var(--vp-c-text-2);
  font-size: 0.875rem;
  line-height: 1.5;
}
</style>