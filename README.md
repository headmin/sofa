# SOFA 
**S**imple **O**rganized **F**eed for **A**pple Software Updates

![Sofa logo](./docs/custom_logo.png "Optional title")

Hello 👋,

**SOFA** supports MacAdmins by efficiently tracking and surfacing information on updates for macOS and iOS. It consists of a machine-readable feed and user-friendly web interface, providing continuously up-to-date information on XProtect data, OS updates, and the details bundled in those releases.

Updated automatically via GitHub Actions, the SOFA feed is a dynamic, centralized, and accessible source of truth. It can be self-hosted, giving you complete assurances as to the provenance of the data your fleet and coworkers can consume. The goal is to streamline the monitoring of Apple's software releases, thereby boosting security awareness and administrative efficiency.

## Key Features

### Machine-Readable Feed, RSS Feed, and Web UI

- **JSON Feed**: Provides detailed, machine-readable data optimized for automated tools and scripts
- **RSS Feed**: Provides RSS Feed for use with entries sorted by date released
- **Web Interface**: Divided between the major version tabs at the top and organized into sections that cover the latest OS information, XProtect updates, and security details for each OS, SOFA facilitates both quick summaries and deep dives into relevant data points

**IMPORTANT NOTE:** 
- Implement a USER-AGENT in Custom Tools
To optimize hosting and caching for SOFA, please implement a user-agent in your integrations, tools, and workflows. This enhances performance and user interactions with SOFA.
- Update to the New Feed Location
Please update your scripts that are utilising the SOFA macOS and iOS feeds to point to **https://sofafeed.macadmins.io/v1/macos_data_feed.json** and **https://sofafeed.macadmins.io/v1/ios_data_feed.json** respectively.

The old feed addresses of https://sofa.macadmins.io/v1/macos_data_feed.json and https://sofa.macadmins.io/v1/ios_data_feed.json are **deprecated** and have been removed.

### Use Cases

SOFA supports a wide array of practical applications, whether for MacAdmin tooling directly or discussing the state of security on Apple platforms with security personnel.

- **Xprotect Monitoring**: Keep track of the latest XProtect updates centrally so agents running on your fleet can verify compliance with CIS/mSCP standards, ensuring Apple's tooling is up-to-date
- **Security Overviews**: Surface information on vulnerabilities (CVEs) and their exploitation status (KEV).
- **Track Countdowns**: Know both a timestamp and the days since a release was posted so you can track when management that delays the update being visible will elapse, or just use it to remind users that the clock is ticking on an update that addresses 'critical' issues
- **Documentation Access**: Use links to quickly view relevant Apple documentation and check detailed CVE information CVE.org, CISA.gov and NVD, and correlate those CVE's across platforms or major versions
- **Download Universal Mac Assistant**: Access the latest and all 'active' (currently signed) IPSW/Universal Mac Assistant (UMA) download links. These can be integrated into your custom reprovisioning workflows, such as EraseAndInstall, to streamline and enhance your device re-purpose/deployment processes
- **Self-Hosting**: Take control of the SOFA feed by self-hosting. Establish your fork as the authoritative source in your environment. Tailor the feed to meet your specific needs and maintain complete autonomy over its data

## SOFA 2.0 Overview

SOFA 2.0 provides enhanced data feeds with richer security information and improved API access:

### Feed Versions

- **V1 Feeds** (`/v1/`): Legacy format with basic CVE boolean flags and essential OS data
- **V2 Feeds** (`/v2/`): Enhanced format with detailed CVE metadata, NIST URLs, KEV status, severity ratings, and enriched security context

### API Access

- **Primary Feed URLs**: `https://site.com/v2/macos_data_feed.json` (cleaner root-level access)
- **Fallback URLs**: `https://site.com/data/feeds/v2/macos_data_feed.json` (backward compatibility)
- **Supported Platforms**: macOS, iOS/iPadOS, Safari, tvOS, watchOS, visionOS
- **Additional Data**: Security releases, XProtect information, beta releases, CVE search, model identifiers

### Technical Implementation

- **Safe Build Process**: Stable build to `data/feeds` with post-build copying to root directories
- **Path Resolution**: Uses absolute paths for reliable execution without dangerous directory changes
- **Config Accessibility**: Maintains access to `config/` directory for proper binary operation
- **Deployment Flexibility**: Environment-configurable URLs for GitHub repository and branch targeting

## Web UI Overview

## SOFA 2.0 (BETA) Overview

SOFA 2.0 provides enhanced data feeds with richer security information and improved API access:

### Feed Versions

- **V1 Feeds** (`/v1/`): Legacy format with basic CVE boolean flags and essential OS data
- **V2 Feeds** (`/v2/`): Enhanced format with detailed CVE metadata, NIST URLs, KEV status, severity ratings, and enriched security context

### API Access

- **Primary Feed URLs**: `https://sofafeed.macadmins.io/v2/macos_data_feed.json` (cached, root-level access)
- **Supported Platform Feeds**: macOS, iOS/iPadOS, Safari, tvOS, watchOS, visionOS
- **Additional Data**: Security releases, XProtect information, beta releases, CVE search, model identifiers

### Technical Implementation

- **GitHub Workers**: GitHub Actions workers execute the build pipeline script `scripts/sofa_pipeline.py` utilizing the `sofa-core` CLI tools. The RSS feed is generated by `scripts/generate_rss.py`, which is called from the main pipeline script.

- **Safe Build Process**: Feeds are build and committed to `v1/` or `v2/`, present in root directory on GitHub
- **Config Visibility**: Visible access to `config/` directory thats is setting operational guardrails for sofa-core CLIs used in pipeline
- **Deployment Flexibility**: Option for self-hosted deployment with  configurable URLs remians, either by useage of the legacy build script in `legacy-sofa-files/` or based of the approach of the new pipeline in `scripts/`.


### Access the Web UI

Visit the [SOFA Web UI](https://sofa.macadmins.io) to start exploring SOFA's features

### Use the Feed Data

Access the feed directly for integration with automated tools or scripts. For production use, we strongly recommend self-hosting the feed to enhance reliability and security. For guidance on how to utilize and implement the feed, explore examples in the [Tools](./tool-scripts) section. For details on self-hosting, please refer to the section below.

## Self-Hosting SOFA

Organizations needing tight control and ownership of the data they rely on can consider self-hosting SOFA. The process of cloning the repository into your own GitHub account or implementing a similar setup on platforms like GitLab is beyond scope of what we can provide here. The legacy `build-sofa-feed.py` file is a great source of adapting the process.
