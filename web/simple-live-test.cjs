const puppeteer = require('puppeteer');

async function testLiveMetrics() {
  console.log('🔥 Live Dashboard Metrics Test\n');
  
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  
  await page.setViewport({ width: 375, height: 667, isMobile: true });
  
  console.log('📊 Testing: http://localhost:5174/\n');
  
  const startTime = Date.now();
  await page.goto('http://localhost:5174/', { waitUntil: 'networkidle0' });
  const loadTime = Date.now() - startTime;
  
  // Analyze data sources and performance
  const analysis = await page.evaluate(() => {
    return {
      // Check what data sources are being fetched
      dataSources: {
        metricsUrl: '/data/resources/metrics.json',
        bulletinUrl: performance.getEntriesByName('/data/resources/bulletin_data.json').length > 0,
        macosUrl: performance.getEntriesByName('/v2/macos_data_feed.json').length > 0,
        iosUrl: performance.getEntriesByName('/v2/ios_data_feed.json').length > 0
      },
      
      // Check loading states
      loadingStates: {
        metricsLoading: !!document.querySelector('.loading-skeleton-container'),
        hasMetricsData: !!document.querySelector('.cloudflare-metric'),
        hasLiveStatus: document.querySelector('[class*="status-green"]')?.textContent?.includes('Live')
      },
      
      // Check mobile spacing
      spacing: (() => {
        const container = document.querySelector('.dashboard-container');
        if (container) {
          const rect = container.getBoundingClientRect();
          return {
            left: rect.left,
            right: window.innerWidth - rect.right,
            balanced: Math.abs(rect.left - (window.innerWidth - rect.right)) <= 5
          };
        }
        return null;
      })(),
      
      // Check optimization results
      optimizations: {
        lazyImages: Array.from(document.querySelectorAll('img')).filter(img => img.loading === 'lazy').length,
        totalImages: document.querySelectorAll('img').length,
        hasTransitions: !!getComputedStyle(document.querySelector('.platform-btn')).transition,
        skeletonPresent: !!document.querySelector('.skeleton-info-box')
      },
      
      // Performance metrics
      performance: {
        domNodes: document.querySelectorAll('*').length,
        memoryUsage: performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1024 / 1024) : 'N/A'
      }
    };
  });
  
  console.log('🚀 Performance Results:');
  console.log(`   Load Time: ${loadTime}ms`);
  console.log(`   DOM Nodes: ${analysis.performance.domNodes}`);
  console.log(`   Memory: ${analysis.performance.memoryUsage}MB`);
  
  console.log('\n📊 Data Sources:');
  console.log(`   Metrics: ${analysis.dataSources.metricsUrl}`);
  console.log(`   Bulletin Data: ${analysis.dataSources.bulletinUrl ? '✅' : '❌'}`);
  console.log(`   macOS Feed: ${analysis.dataSources.macosUrl ? '✅' : '❌'}`);
  console.log(`   iOS Feed: ${analysis.dataSources.iosUrl ? '✅' : '❌'}`);
  
  console.log('\n📱 Mobile Spacing:');
  if (analysis.spacing) {
    console.log(`   Left: ${analysis.spacing.left}px`);
    console.log(`   Right: ${analysis.spacing.right}px`);
    console.log(`   Balanced: ${analysis.spacing.balanced ? '✅' : '❌'}`);
  }
  
  console.log('\n⚡ Optimizations Active:');
  console.log(`   Lazy Images: ${analysis.optimizations.lazyImages}/${analysis.optimizations.totalImages}`);
  console.log(`   Smooth Transitions: ${analysis.optimizations.hasTransitions ? '✅' : '❌'}`);
  console.log(`   Skeleton Loading: ${analysis.optimizations.skeletonPresent ? '✅' : '❌'}`);
  
  console.log('\n📈 Loading States:');
  console.log(`   Metrics Loaded: ${analysis.loadingStates.hasMetricsData ? '✅' : '❌'}`);
  console.log(`   Live Status: ${analysis.loadingStates.hasLiveStatus ? '✅' : '❌'}`);
  
  console.log('\n🎯 Metrics Data Source for Last Updated Dashboard:');
  console.log('   Local: /data/resources/metrics.json');
  console.log('   Live: https://sofa-beta.macadmin.me/data/resources/metrics.json');
  
  await browser.close();
}

testLiveMetrics().catch(console.error);