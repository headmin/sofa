# SOFA 
**S**imple **O**rganized **F**eed for **A**pple Software Updates

![SOFA logo](./images/custom_logo.png)

## What is SOFA?

SOFA (Simple Organized Feed for Apple Software Updates) is a community-driven solution for tracking Apple security updates and software releases. It provides MacAdmins and security professionals with reliable, up-to-date information about macOS, iOS, and other Apple platform updates in both machine-readable and human-friendly formats.

### The Problem SOFA Solves

Managing Apple devices at scale requires staying current with security updates, but Apple's update information is scattered across multiple sources and formats. SOFA centralizes this information, making it easy to:

- Monitor security updates across all Apple platforms
- Track vulnerability (CVE) information and exploitation status
- Automate update management workflows
- Maintain security compliance and awareness

## Key Features

### Multiple Data Formats
- **JSON Feeds**: Machine-readable data optimized for automated tools and scripts
- **RSS Feed**: Chronologically sorted updates for RSS readers and notification systems
- **Web Interface**: User-friendly dashboard with detailed security information and platform-specific pages

### Summarized Security Data
- **CVE Tracking**: Detailed vulnerability information with exploitation status
- **XProtect Monitoring**: Apple's built-in security framework updates
- **KEV Cross-Checking**: Known Exploited Vulnerabilities from CISA
- **Security Timeline**: Historical view of security releases and OS versions

### Multi-Apple Platform Coverage
- **macOS**: All supported versions with security updates
- **iOS/iPadOS**: Mobile platform security information
- **Safari**: Browser security updates
- **tvOS, watchOS, visionOS**: Complete Apple ecosystem coverage

### Flexible Utilization
- **Hosted Service**: Ready-to-use feeds at `sofafeed.macadmins.io`
- **Self-Hosting**: Complete control over your data and infrastructure
- **API Access**: Cloudflare Cached static JSON feeds to be consumed for custom integration

## Quick Start

### Web Interface
Visit [sofa.macadmins.io](https://sofa.macadmins.io) to explore SOFA's dashboard and browse security information.

### API Access
Access feeds directly for automation:

**V2 Feeds (BETA, Enhanced Security Context)**:
- macOS: `https://sofafeed.macadmins.io/v2/macos_data_feed.json`
- iOS: `https://sofafeed.macadmins.io/v2/ios_data_feed.json`
- Safari: `https://sofafeed.macadmins.io/v2/safari_data_feed.json`

**RSS Feed**:
- Updates: `https://sofafeed.macadmins.io/v1/rss_feed.xml`

### Integration Examples
Check the [Tools](./tool-scripts) section for example scripts and integration patterns.

## Feed Versions

### V1 Feeds (Legacy)
- **Location**: `/v1/` directory
- **Format**: Basic CVE boolean flags and essential OS data
- **Use Case**: Backward compatibility with existing tools

### V2 Feeds (Enhanced)
- **Location**: `/v2/` directory  
- **Format**: Detailed CVE metadata, NIST URLs, KEV status, severity ratings
- **Features**: Enriched security context, exploitation indicators, comprehensive platform data
- **Recommendation**: Use V2 for new integrations

## Common Use Cases

### Security Monitoring
- **XProtect Compliance**: Verify fleet compliance with CIS/mSCP security standards
- **Vulnerability Tracking**: Monitor CVEs and their exploitation status (KEV)
- **Security Overviews**: Generate reports on platform security posture

### Update Management
- **Release Tracking**: Monitor days since security updates were released
- **Countdown Timers**: Track management visibility delays for critical updates
- **Automated Workflows**: Integrate with deployment and notification systems

### Documentation & Research
- **CVE Research**: Access detailed vulnerability information from CVE.org, CISA, and NVD
- **Cross-Platform Analysis**: Correlate security issues across Apple platforms
- **Apple Documentation**: Direct links to official Apple security documentation

### Admin tasks & device management
- **IPSW Downloads**: Access Universal Mac Assistant (UMA) download links
- **Reprovisioning Workflows**: Integrate with EraseAndInstall and deployment processes
- **Model Identification**: Device model and compatibility information

## Important Updates

### Feed URL Migration
**Action Required**: Update your integrations to use the new feed URLs:

**New URLs (Use These)**:
- `https://sofafeed.macadmins.io/v1/macos_data_feed.json`
- `https://sofafeed.macadmins.io/v1/ios_data_feed.json`

**Deprecated URLs (Will Be Removed)**:
- `https://sofa.macadmins.io/v1/macos_data_feed.json`
- `https://sofa.macadmins.io/v1/ios_data_feed.json`

### User-Agent Requirement
Please implement a User-Agent header in your tools and scripts. This helps optimize caching and improves performance for all users.

Example:
```bash
curl -H "User-Agent: MyTool/1.0" https://sofafeed.macadmins.io/v2/macos_data_feed.json
```

## Technical Architecture

### Build Pipeline
- **Automation**: GitHub Actions execute the build pipeline using `scripts/sofa_pipeline.py`
- **Data Processing**: Utilizes `sofa-core` CLI tools for data aggregation and processing
- **RSS Generation**: Automated RSS feed creation via `scripts/generate_rss.py`
- **Safe Deployment**: Feeds are built and committed to `v1/` and `v2/` directories

### Configuration
- **Transparent Config**: Gather > Fetch > Build configuration visible in `config/` directory
- **Customizable**: Self-hosting option based on `sofa-core` or `legacy-sofa-files/` allows independent configuration control

### Deployment Options
- **Hosted Service**: Production-ready feeds with CDN caching
- **Self-Hosting**: Deploy using the new pipeline in `scripts/` directory
- **Legacy Support**: Backward compatibility with `legacy-sofa-files/` build script `build-sofa-feed.py`

## Self-Hosting

SOFA can be self-hosted for enhanced reliability, security, and customization. Self-hosting gives you:

- **Complete Data Control**: Full ownership of your security data
- **Custom Scheduling**: Update feeds on your preferred schedule  
- **Network Isolation**: Keep sensitive data within your infrastructure
- **Customization**: Tailor feeds to your specific requirements


## Contributing

SOFA is an open-source project maintained by the MacAdmins community. Contributions are welcome in many forms:

- **Code**: Submit improvements and new features
- **Documentation**: Help improve guides and examples
- **Testing**: Report issues and test new releases
- **Feedback**: Share use cases and feature requests

## Support

- **Documentation**: Overview guides in the `docs/` directory
- **Community**: MacAdmins Slack and community forums
- **Issues**: GitHub Issues for bug reports and feature requests
- **Examples**: Sample integrations in the `tool-scripts/` directory

---

SOFA is developed and maintained by the MacAdmins Open Source community. Learn more about supporting the project at [MacAdmins.io](https://macadmins.io).

You can support the MacAdmins Open Source community through [GitHub Sponsors](https://github.com/sponsors/macadmins?o=esb). Contributions of any size help sustain the community's efforts and ensure continued development of essential tools.

