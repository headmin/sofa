# SOFA Device Manager Complete Manual

**`scripts/device_manager.py`** - Comprehensive device database management for SOFA pipeline.

## Quick Setup

```bash
# Install dependencies (one-time setup)
uv add rich typer

# Check current status
uv run scripts/device_manager.py status
```

## Command Reference

### Core Database Operations

#### `status` - Database Overview
```bash
uv run scripts/device_manager.py status
```

**Output:**
```
📊 SOFA Device Database Status
📂 Sources: data/models/sources
📁 Output: data/resources

Platform Files table showing devices, status counts, file sizes
📊 Totals: 111 devices (111 current, 0 vintage)
✅ Unified Files: JSON (44KB) | NDJSON (37KB)
```

**What it does:**
- Shows platform-by-platform breakdown
- Displays current/vintage device counts
- Shows source file sizes
- Checks unified output files exist

#### `rebuild` - Build Unified Database
```bash
uv run scripts/device_manager.py rebuild
```

**Output:**
```
🔨 Rebuilding from sources...
📂 Sources: data/models/sources
📁 Output: data/resources
🔨 Rebuilding unified database...
✅ Database rebuilt successfully
   📊 111 devices from 5 platforms
   📄 JSON: 44KB | NDJSON: 37KB
```

**What it does:**
- Loads all platform source files
- **Auto-corrects device_count metadata** where mismatched
- Builds hierarchical unified database: macOS → iPadOS → iOS → tvOS → watchOS
- Preserves device order within each platform
- Outputs to `data/resources/all_devices_enhanced.json` + `.ndjson`

#### `validate` - Data Consistency Check
```bash
uv run scripts/device_manager.py validate
```

**What it validates:**
- Required fields: Model, URL, marketingName, support_status, DeviceID
- DeviceID consistency (matches key)
- Valid support_status values (current/vintage/obsolete)
- **Device count metadata vs actual count**

#### `check` - Essential SOFA Fields
```bash
uv run scripts/device_manager.py check
uv run scripts/device_manager.py check --platform ios
```

**What it checks:**
- Essential SOFA fields: processorFamily, marketingName, supportedMajor, DeviceID
- No placeholder values like `["current"]` in supportedMajor
- No empty/missing critical data

### Device Creation

#### `add-device` - Quick Device Addition
```bash
uv run scripts/device_manager.py add-device ios iPhone19,1 "iPhone 18 Pro" "A20 Pro"
uv run scripts/device_manager.py add-device macos Mac17,1 "Mac Studio M5" "M5" --os-version "16.0"
```

**Features:**
- **Duplicate protection** - Won't overwrite existing devices
- **Smart URL detection** - Auto-assigns proper support URLs
- **Device type detection** - Laptop/Desktop/Phone/Tablet based on name
- **Apple Silicon detection** - Auto-sets processorType
- **Newest-first placement** - New devices go to top of platform file
- **Auto-rebuild** - Updates unified database

#### `add-guided` - Interactive Device Creation
```bash
uv run scripts/device_manager.py add-guided
```

**Interactive process:**
1. **Platform selection:** macOS/iOS/iPadOS/watchOS/tvOS
2. **Device ID:** Mac17,1, iPhone19,1, etc.
3. **Marketing name:** Full device name
4. **Processor suggestions:** Smart suggestions based on platform
5. **OS support suggestions:** Auto-suggests supportedMajor based on processor
6. **Preview & confirm:** Shows complete device entry
7. **Post-processing validation:** Ensures data quality

**Smart features:**
- **Processor-based OS suggestions:**
  - M4 → `["tahoe", "sequoia"]`
  - A18 → `["18", "17", "16"]`
  - S10 → `["11", "10"]`
- **Proper URL assignment**
- **Complete field population**
- **Validation after creation**

### Device Management

#### `fix-device` - Update Device Data
```bash
# Fix any field
uv run scripts/device_manager.py fix-device iPhone17,1 processorFamily "A18 Pro"
uv run scripts/device_manager.py fix-device Mac15,4 marketingName "iMac M3 Pro"

# Fix OS support (JSON array)
uv run scripts/device_manager.py fix-device iPhone16,1 supportedMajor '["18", "17", "16"]'
uv run scripts/device_manager.py fix-device Mac14,15 supportedMajor '["tahoe", "sequoia", "sonoma"]'
```

**Features:**
- **JSON array handling** - Properly parses supportedMajor arrays
- **Cross-platform** - Finds device across all platforms
- **Auto-rebuild** - Updates unified database
- **Validation** - Ensures changes are correct

#### `drop-support` - OS Lifecycle Management
```bash
# When new OS drops processor support
uv run scripts/device_manager.py drop-support ios "A12" "18.8.1"
uv run scripts/device_manager.py drop-support macos "Intel" "13.7.2"
uv run scripts/device_manager.py drop-support watchos "S6" "11.8.1"
```

**What happens:**
- Devices **stay in database** (not removed)
- `support_status` changes: `current` → `vintage`
- `systemLastRelease` set to final OS version
- Database rebuilds automatically

### Search & Discovery

#### `search` - Cross-Platform Device Search
```bash
uv run scripts/device_manager.py search "iPhone 15"
uv run scripts/device_manager.py search "M1" --platform macos
uv run scripts/device_manager.py search "Pro Max"
```

**Search scope:**
- Device ID, marketing name, processor family
- All platforms or specific platform
- **No result limits** - shows all matches

#### `list-platform` - Platform Device Listing
```bash
uv run scripts/device_manager.py list-platform ios
uv run scripts/device_manager.py list-platform macos --status current
uv run scripts/device_manager.py list-platform ipados --processor M2
```

**Display:**
- Device ID, Name, Processor, Status, **OS Versions**
- **No truncation** - shows all devices
- **OS Versions column** - Shows supportedMajor at a glance

### Maintenance Operations

#### `cleanup-vintage` - Remove Old Devices
```bash
uv run scripts/device_manager.py cleanup-vintage                # Dry run
uv run scripts/device_manager.py cleanup-vintage --no-dry-run  # Actually remove
uv run scripts/device_manager.py cleanup-vintage --platform ios
```

**Features:**
- **Dry run by default** - Shows what would be removed
- **Removes vintage/obsolete** devices only
- **Updates metadata** automatically
- **Rebuilds database** after cleanup

## File Structure

```
data/models/sources/          # Source platform files
├── ios_devices.json          # iPhone devices (25 devices, 9KB)
├── macos_devices.json        # Mac devices (37 devices, 18KB)  
├── ipados_devices.json       # iPad devices (22 devices, 9KB)
├── watchos_devices.json      # Apple Watch devices (22 devices, 8KB)
└── tvos_devices.json         # Apple TV devices (5 devices, 2KB)

data/resources/               # Unified output files
├── all_devices_enhanced.json # Complete database (44KB)
└── all_devices_enhanced.ndjson # Line-delimited format (37KB)
```

## Key Data Fields

Every device must have these **essential SOFA fields:**

### Required Fields
- `DeviceID`: Unique identifier (Mac17,1, iPhone19,1)
- `Model`: Device family (iPhone, MacBook Pro, iPad)
- `URL`: Apple support page URL
- `deviceType`: Phone/Tablet/Laptop/Desktop/Wearable/Set-Top Box
- `processorFamily`: **Critical** - M4, A18 Pro, S10, etc.
- `processorType`: Apple Silicon/Unknown
- `marketingName`: Full marketing name
- `support_status`: current/vintage/obsolete

### Essential for SOFA
- **`supportedMajor`**: **Critical SOFA field** - OS versions supported
  - **macOS**: `["tahoe", "sequoia", "sonoma"]`
  - **iOS**: `["18", "17", "16"]` 
  - **watchOS**: `["11", "10", "9"]`
  - **iPadOS**: `["18", "17", "16"]`
  - **tvOS**: `["18", "17", "16"]`

### Optional Fields
- `systemFirstRelease`: First OS version (11.0, 16.0)
- `systemLastRelease`: Final OS version (for vintage devices)
- `BoardID`: Hardware board identifier

## Common Workflows

### New Device Release Workflow
```bash
# Option 1: Quick addition
uv run scripts/device_manager.py add-device ios iPhone19,1 "iPhone 18 Pro" "A20 Pro"

# Option 2: Guided creation (recommended)
uv run scripts/device_manager.py add-guided
# Interactive prompts with smart suggestions

# Verification
uv run scripts/device_manager.py list-platform ios
uv run scripts/device_manager.py check --platform ios
```

### OS Lifecycle Management
```bash
# When iOS 19 drops iPhone 8 support
uv run scripts/device_manager.py drop-support ios "A11" "18.8.1"

# Verify changes
uv run scripts/device_manager.py list-platform ios --status vintage
uv run scripts/device_manager.py validate
```

### Database Maintenance
```bash
# Check for issues
uv run scripts/device_manager.py validate
uv run scripts/device_manager.py check

# Fix identified problems
uv run scripts/device_manager.py fix-device iPad14,6 processorFamily "M2"
uv run scripts/device_manager.py fix-device iPhone17,1 supportedMajor '["18", "17", "16"]'

# Clean up old devices (optional)
uv run scripts/device_manager.py cleanup-vintage --no-dry-run

# Rebuild unified database
uv run scripts/device_manager.py rebuild
```

### Data Quality Assurance
```bash
# Complete validation sequence
uv run scripts/device_manager.py validate     # Check consistency
uv run scripts/device_manager.py check       # Check essential fields
uv run scripts/device_manager.py rebuild     # Fix metadata & rebuild
uv run scripts/device_manager.py validate    # Verify all clean
```

## Advanced Features

### Duplicate Protection
- **add-device** and **add-guided** detect existing devices
- Shows existing device name for confirmation
- Suggests using `fix-device` for updates
- **Prevents data loss** from accidental overwrites

### Smart Suggestions
- **Processor-based OS support** suggestions
- **URL auto-assignment** based on device type
- **Device type detection** from marketing name
- **Apple Silicon detection** from processor

### Metadata Management
- **Auto-corrects device_count** during rebuild
- **Preserves order** in source files
- **Updates timestamps** on changes
- **Maintains data integrity**

### Hierarchical Database Building
- **Platform order:** macOS → iPadOS → iOS → tvOS → watchOS
- **Device order:** Preserves source file order (newest first within platform)
- **Stable ordering** - no fluctuation unless new devices added
- **Consistent structure** for SOFA pipeline consumption

## Error Handling

### Duplicate Device Addition
```
❌ Device Mac16,10 already exists in macos
   Existing: Mac mini (2024)
💡 Use 'fix-device Mac16,10 <field> <value>' to update existing device
```

### Missing Platform/Device
```
❌ Platform file not found: badplatform
❌ Device BadDevice99 not found in any platform file
```

### Validation Issues
```
⚠️  Found 1 validation issues:
   • watchos: device_count mismatch (metadata: 30, actual: 22)
```

## Testing

### Complete Test Suite
```bash
# Run comprehensive test suite
./test_device_manager_complete.sh
```

Tests all operations:
- Basic operations (status, validate, check)
- Search and listing
- Device addition with duplicate protection
- Device fixing with JSON arrays
- Drop support functionality
- Cleanup operations
- Error handling

## Best Practices

### Adding New Devices
1. **Use `add-guided`** for complete, correct entries
2. **Verify with `check`** after adding
3. **Include proper supportedMajor** - essential for SOFA

### Managing OS Updates
1. **Use `drop-support`** when OS drops processor support
2. **Keep devices in database** as vintage (don't delete)
3. **Validate after changes** with `validate` command

### Database Maintenance
1. **Run `validate`** regularly to catch issues
2. **Use `rebuild`** to fix metadata inconsistencies
3. **Backup source files** before major operations
4. **Keep vintage devices** for historical compatibility data

### Data Quality
- **supportedMajor is critical** - SOFA relies on this for OS filtering
- **Use specific OS versions** not placeholder values like "current"
- **Maintain processor accuracy** - essential for vulnerability classification
- **Complete marketing names** - important for user-facing displays

## Integration with SOFA Pipeline

The device manager integrates seamlessly with SOFA:

1. **Source files** (`data/models/sources/*.json`) contain clean, current device data
2. **Unified database** (`data/resources/all_devices_enhanced.json`) feeds SOFA pipeline
3. **Essential fields** ensure proper vulnerability classification and OS filtering
4. **Hierarchical ordering** provides predictable structure for processing
5. **NDJSON format** enables efficient data processing workflows

The device manager ensures SOFA always has high-quality, complete device data for accurate vulnerability assessment and OS compatibility analysis.