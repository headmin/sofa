"""SOFA feed builder, majority of heavy lifting is in process_os_type"""

import argparse
import glob
import hashlib
import io
import json
import gzip
import os
import plistlib
import re
import ssl
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.request import urlopen
from urllib.parse import urljoin
import packaging.version

import certifi  # included in requests, as provided in requirements.txt
import requests
from bs4 import BeautifulSoup, NavigableString  # pylint: disable=import-error
from feedgen.feed import FeedGenerator  # pylint: disable=import-error

current_dir = os.getcwd()
sys.path.insert(0, current_dir)
import process_ipsw  # noqa: E402
import process_uma  # noqa: E402


def main(os_types: list):
    """The main function to process OS version information based on the provided OS types"""
    feed_results: list = []  # instantiate end result
    # config.json mostly instructs what OS versions to parse, text elements/color for GUI
    with open("config.json", "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
    gdmf_data = fetch_gdmf_data()
    if not gdmf_data:
        print("Failed to fetch GDMF data and no valid cached data available.")
        return
    rss_cache = load_rss_data_cache()
    for os_type in os_types:  # TODO: handle macOS separately to remove weight
        result = process_os_type(os_type, config, gdmf_data)
        feed_results.extend(result)
    rss_data = diff_rss_data(feed_results, rss_cache)
    write_data_to_rss(rss_data, "rss_feed.xml")

    # Load supported devices and macOS data feed
    supported_devices_data = load_supported_devices_data()
    macos_data_feed = load_macos_data_feed()

    # save_original_macos_data_feed(macos_data_feed)

    # Update macos data feed with supported devices data if necessary
    updated_feed_data = update_supported_devices_in_feed(macos_data_feed, supported_devices_data)

    # Save the updated macOS data feed
    save_updated_macos_data_feed(updated_feed_data)


def fetch_gdmf_data() -> dict:
    """Fetches latest GDMF data, if succeeds update the cache & return, otherwise use cache"""
    live_data = {}
    cache_file_path: str = "cache/gdmf_cached.json"
    log_file_path = "cache/gdmf_log.json"
    max_log_entries = 10
    # Check if the cache file exists, is valid JSON, and output its content
    cached_data, cached_etag = check_cache_file(cache_file_path)
    if cached_data:
        print("Validated local cached GDMF data.")
    else:
        cached_data = {}
    # TODO: shift to only fetching header for etag first
    url = "https://gdmf.apple.com/v2/pmv"
    pemname = "AppleRoot.pem"
    abs_file_path = os.path.abspath(pemname)
    headers = {"User-Agent": "macadmins-sofa"}
    try:
        response = requests.get(
            url, headers=headers, verify=abs_file_path
        )
        response.raise_for_status()  # This will raise class HTTPError if the response was an HTTP code 4xx or 5xx  # noqa: E501 pylint: disable=line-too-long
        live_data = response.json()
        if live_data:  # Only update the cache if the data is not empty
            live_etag = compute_hash(live_data)
            if live_etag != cached_etag:
                update_cache(cache_file_path, live_data, live_etag)
                print("Using live gathered GDMF data and updating cache.")
            else:
                print(
                    "Live gathered GDMF data is identical to cached data. No update needed."
                )
            write_gdmf_log(
                log_file_path, response.status_code, live_data, max_log_entries
            )
    except requests.RequestException as gdmf_fetch_err:
        print(f"Request failed: {gdmf_fetch_err}")
        # If fetching live data fails, use the cached data if available
    if not live_data:
        print("Attempting to use cached GDMF data due to live fetch failure.")
        if cached_data:
            write_gdmf_log(
                log_file_path,
                response.status_code if "response" in locals() else 666,
                cached_data,
                max_log_entries,
            )
            live_data = cached_data
        else:
            print("No cached GDMF data available.")
            write_gdmf_log(
                log_file_path,
                response.status_code if "response" in locals() else 666,
                {},
                max_log_entries,
            )
    return live_data


def check_cache_file(cache_file_path: str, verbose: bool = True) -> tuple:
    """Check if the cache file exists and does not fail JSON decode.
    Return the data and 'etag' if valid."""
    
    if os.path.exists(cache_file_path):
        try:
            with open(cache_file_path, "r", encoding="utf-8") as cache_file:
                cache_content = json.load(cache_file)
                
                if "etag" in cache_content and "data" in cache_content:
                    if verbose:
                        print("Cache file", cache_file_path, "is valid JSON.")
                        print("Cache content:", cache_content["data"])
                    if cache_content["data"] == {} and verbose:
                        print("Cache content is empty.")
                    return cache_content["data"], cache_content["etag"]
                
                if verbose:
                    print("Cache file structure is invalid.")
        except (json.JSONDecodeError, IOError) as check_cache_err:
            if verbose:
                print(f"Failed to read cache file: {check_cache_err}")
    else:
        if verbose:
            print(f"Cache file {cache_file_path} does not exist.")
    
    return None, None


def compute_hash(data: dict) -> str:
    """Computes SHA-256 hash of the given data, typically a dict. Returns a hexadecimal str"""
    json_str = json.dumps(
        data, sort_keys=True
    ).encode()  # sorts to always produce consistent result
    return hashlib.sha256(json_str).hexdigest()


def update_cache(cache_file_path: str, data: dict, etag: str):
    """Update the cache file with the provided data and hash as 'etag'"""
    try:
        os.makedirs(os.path.dirname(cache_file_path), exist_ok=True)
        cache_data = {"etag": etag, "data": data}
        with open(cache_file_path, "w", encoding="utf-8") as cache_file:
            json.dump(cache_data, cache_file, indent=4)
        print(f"Cache updated successfully at {cache_file_path}.")
    except Exception as cache_err:
        print(f"Failed to update cache: {cache_err}")


def write_gdmf_log(
    log_file_path: str, status_code: int, data: dict, max_log_entries: int
):
    """(gdmf) data is only used for etag calculation"""
    current_time = datetime.now(timezone.utc).replace(microsecond=0).isoformat() + "Z"
    new_etag = compute_hash(data)
    log_entry = {
        "timestamp": current_time,
        "new_etag": new_etag,
        "status": (
            f"success ({status_code})"
            if status_code in {200, 201, 202, 301}
            else f"failed ({status_code})"
        ),
        "previous_etag": "",
    }
    if os.path.exists(log_file_path):
        with open(log_file_path, "r", encoding="utf-8") as file:
            try:
                log_data = json.load(file)
            except json.JSONDecodeError:
                log_data = {"latest_etag": {}, "log": []}
    else:
        log_data = {"latest_etag": {}, "log": []}
    if "log" in log_data:
        log_entry["previous_etag"] = log_data["log"][0]["new_etag"]
    log_data["latest_etag"] = {"LastCheck": current_time, "UpdateHash": new_etag}
    log_data["log"].insert(0, log_entry)
    log_data["log"] = sorted(
        log_data["log"], key=lambda x: x["timestamp"], reverse=True
    )[
        :max_log_entries
    ]  # TODO: confirm sorting every time is most obvious/best, vs just keeping most recent 10
    with open(log_file_path, "w", encoding="utf-8") as log_file:
        json.dump(log_data, log_file, indent=4)


def load_rss_data_cache() -> list:
    """Load RSS data from cache files and return combined data"""
    rss_cache_dir = "cache"  # TODO: consider making this a global, since used for gdmf
    combined_data = []
    cache_files = glob.glob(os.path.join(rss_cache_dir, "*_rss_data.json"))
    for cache_file in cache_files:
        try:
            with open(cache_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                combined_data.extend(data)
        except (FileNotFoundError, json.JSONDecodeError) as rss_cache_err:
            print(f"Error reading cache file - {cache_file}: {rss_cache_err}")
    return combined_data


def process_os_type(os_type: str, config: dict, gdmf_data: dict) -> list:
    """Process the given OS type (macOS, iOS) and update the feed structure"""
    software_releases = [
        release
        for release in config["softwareReleases"]
        if release["osType"] == os_type
    ]
    print(
        f"Software releases for {os_type}: {software_releases}"
    )  # TODO: as per below, this is weird, revisit  noqa: E501 pylint: disable=line-too-long
    feed_structure: dict = {
        "OSVersions": [],
    }
    if os_type == "macOS":
        catalog_url: str = (
            "https://swscan.apple.com/content/catalogs/others/index-15-14-13-12-10.16-10.15-10.14-10.13-10.12-10.11-10.10-10.9-mountainlion-lion-snowleopard-leopard.merged-1.sucatalog"
    # noqa: E501 pylint: disable=line-too-long
        )
        catalog_content = fetch_content(catalog_url)
        # Find all URLs for XProtectPlistConfigData
        config_matches = re.findall(
            r"https.*XProtectPlistConfigData.*?\.pkm", catalog_content
        )
        plist_info = None

        if config_matches:
            # Iterate over all matched URLs and extract version information
            plist_versions = [
                extract_xprotect_versions_and_post_date(catalog_content, url)
                for url in config_matches
            ]

            # Sort the plist versions by date (or version) to get the latest
            plist_versions.sort(key=lambda x: x["ReleaseDate"], reverse=True)
            # Retrieve the latest version info
            plist_info = plist_versions[0]

        # Find all URLs for XProtectPayloads
        payload_matches = re.findall(
            r"https.*XProtectPayloads.*?\.pkm", catalog_content
        )
        payloads_info = None

        if payload_matches:
            # Iterate over all matched URLs and extract version information
            payload_versions = [
                extract_xprotect_versions_and_post_date(catalog_content, url)
                for url in payload_matches
            ]

            # Sort the payload versions by date to get the latest
            payload_versions.sort(key=lambda x: x["ReleaseDate"], reverse=True)
            # Retrieve the latest version info
            payloads_info = payload_versions[0]

        # Update the feed structure with the latest information
        feed_structure["XProtectPayloads"] = payloads_info
        feed_structure["XProtectPlistConfigData"] = plist_info
        # Load and tag model data
        model_files = [
            ("model_identifier_tahoe.json", "macOS Tahoe 26"),
            ("model_identifier_sequoia.json", "macOS Sequoia 15"),
            ("model_identifier_sonoma.json", "macOS Sonoma 14"),
            ("model_identifier_ventura.json", "macOS Ventura 13"),
            ("model_identifier_monterey.json", "macOS Monterey 12"),
        ]
        models_info = load_and_tag_model_data(model_files)
        feed_structure["Models"] = models_info
        # UMA parsing
        unrefined_products = process_uma.initial_uma_parse(catalog_content.encode())
        print(f"Extracted {len(unrefined_products)} potential UMA packages")
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.load_verify_locations(cafile=certifi.where())
        filtered_dict = {}
        for slug, prod_dict in unrefined_products.items():
            title, build, version = process_uma.get_metadata(
                ctx, prod_dict.get("dist_url")
            )
            if title:
                filtered_dict[slug] = {
                    "title": title,
                    "version": version,
                    "build": build,
                    "apple_slug": slug,
                    "url": prod_dict.get("URL"),
                }
        latest, rest = process_uma.sort_installers(filtered_dict)
        uma_list = {
            "LatestUMA": latest,
            "AllPreviousUMA": rest,
        }  # TODO: flatten all this down into the one call and subsequent assignment  # noqa: E501 pylint: disable=line-too-long
        feed_structure["InstallationApps"] = uma_list
        # ipsw (latest/'most prevalent' in mesu only as of v1) parsing
        mesu_url: str = (
            "https://mesu.apple.com/assets/macos/com_apple_macOSIPSW/com_apple_macOSIPSW.xml"  # noqa: E501 pylint: disable=line-too-long
        )
        try:
            with urlopen(mesu_url, context=ctx) as response:
                mesu_cat = response.read()
        except (Exception, OSError) as error:  # pylint: disable=broad-exception-caught
            print(f"Error fetching mesu assets, {error}")
            raise
        mesu_catalog: dict = plistlib.loads(mesu_cat)
        restore_datas = process_ipsw.extract_ipsw_raw(mesu_catalog)
        prevalent_url, prevalent_build, prevalent_version = (
            process_ipsw.process_ipsw_data(restore_datas)
        )
        apple_slug = process_ipsw.process_slug(prevalent_url)
        print(f"Extracted IPSW\n{prevalent_url}")
        feed_structure["InstallationApps"]["LatestMacIPSW"] = (
            {  # TODO: flatten all this down into the one call and subsequent assignment, too  # noqa: E501 pylint: disable=line-too-long
                "macos_ipsw_url": prevalent_url,
                "macos_ipsw_build": prevalent_build,
                "macos_ipsw_version": prevalent_version,
                "macos_ipsw_apple_slug": apple_slug,
            }
        )
    elif os_type == "iOS":
        # Initialize os_versions dynamically for iOS
        os_versions = [
            ("iOS", release["name"], None) for release in software_releases
        ]  # Populates "iOS 18" when config only has "18" # noqa: E501 pylint: disable=line-too-long
        print(f"OS versions for {os_type}: {os_versions}")
        print(f"Skipping fetching XProtect and 'Models' data for {os_type}.")
    else:
        print(
            "Invalid OS type specified."
        )  # TODO: should probably raise/exit if this happens
    latest_versions: dict = {}
    latest_version_info: dict = {}
    for release in software_releases:
        os_version_name = release["name"]
        latest_version_info = fetch_latest_os_version_info(
            os_type, os_version_name, gdmf_data
        )
        if latest_version_info:
            latest_versions[os_version_name] = latest_version_info
    print("Fetching OS version information...")
    for release in software_releases:
        os_version_name = release["name"]
        latest_version_info = latest_versions.get(os_version_name, {})
        if latest_version_info is not None:
            # Format dates, handle missing 'ReleaseDate'
            if "ReleaseDate" in latest_version_info:
                latest_version_info["ReleaseDate"] = format_iso_date(latest_version_info["ReleaseDate"])
            else:
                print(f"Warning: 'ReleaseDate' missing for {os_version_name}")
                latest_version_info["ReleaseDate"] = "Unknown"

            if "ExpirationDate" in latest_version_info:
                latest_version_info["ExpirationDate"] = format_iso_date(latest_version_info["ExpirationDate"])

            # Handle missing 'ProductVersion'
            if "ProductVersion" in latest_version_info:
                product_version = latest_version_info["ProductVersion"]
            else:
                print(f"Warning: 'ProductVersion' missing for {os_version_name}")
                product_version = "Unknown"  # Set a default value or handle accordingly

            if os_type == "macOS":
                latest_security_info = fetch_security_releases(
                    os_type, product_version, gdmf_data
                )
                if latest_security_info:
                    latest_version_info["SecurityInfo"] = latest_security_info[0][
                        "SecurityInfo"
                    ]
                    latest_version_info["CVEs"] = latest_security_info[0]["CVEs"]
                    latest_version_info["ActivelyExploitedCVEs"] = latest_security_info[
                        0
                    ]["ActivelyExploitedCVEs"]
                    latest_version_info["UniqueCVEsCount"] = latest_security_info[0][
                        "UniqueCVEsCount"
                    ]
                compatible_machines = add_compatible_machines(os_version_name)
                feed_structure["OSVersions"].append(
                    {
                        "OSVersion": os_version_name,
                        "Latest": latest_version_info,
                        "SecurityReleases": fetch_security_releases(  # TODO: second instance of fetching HT201222 # noqa: E501 pylint: disable=line-too-long
                            os_type, os_version_name, gdmf_data
                        ),
                        "SupportedModels": compatible_machines,  # Add compatible machines here
                    }
                )
            elif os_type == "iOS":
                # For iOS, append without compatible machines
                feed_structure["OSVersions"].append(
                    {
                        "OSVersion": os_version_name,
                        "Latest": latest_version_info,
                        "SecurityReleases": fetch_security_releases(  # TODO: potentially 3rd instance of fetching HT201222 # noqa: E501 pylint: disable=line-too-long
                            os_type, os_version_name, gdmf_data
                        ),  # Note: 'SupportedModels' is not included for iOS
                    }
                )
    hash_value = compute_hash(feed_structure)
    feed_structure = {
        "UpdateHash": hash_value,  # Insert hash first
        **feed_structure,  # Unpack other content after the hash
    }
    data_feed_filename = f"{os_type.lower()}_data_feed.json"
    write_data_to_json(feed_structure, data_feed_filename)
    data_feed = create_rss_json_data(feed_structure)
    write_timestamp_and_hash(os_type, hash_value)
    read_and_validate_json(data_feed_filename)
    return data_feed


def fetch_content(url: str) -> str:
    """Fetch content from the given URL, basic checking for errors"""
    response = requests.get(url)
    if response.ok:
        if response.headers.get('Content-Encoding') == 'gzip' or url.endswith('.gz'):
            try:
                with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gz_file:
                    return gz_file.read().decode('utf-8')
            except gzip.BadGzipFile:
                return response.text
        else:
            return response.text
    else:
        raise Exception(f"Error fetching data from {url}: HTTP {response.status_code}")


def extract_xprotect_versions_and_post_date(catalog_content: str, pkm_url: str) -> dict:
    """Extract XProtect versions and post date from the catalog content"""
    pkm_content = fetch_content(pkm_url)
    version_info = {}
    if pkm_content:
        root = ET.fromstring(pkm_content)
        for bundle in root.findall(".//bundle"):
            id_attr = bundle.get("id")
            version = bundle.get("CFBundleShortVersionString")
            if id_attr is not None and (
                "XProtect" in id_attr or "PluginService" in id_attr
            ):
                version_info[id_attr] = version
        post_date_regex = rf"<string>{re.escape(pkm_url)}</string>.*?<date>(.*?)</date>"
        post_date_match = re.search(post_date_regex, catalog_content, re.DOTALL)
        if post_date_match:
            # Ensure the release date is formatted in ISO 8601 format
            release_date = post_date_match.group(1)
            version_info["ReleaseDate"] = format_iso_date(
                release_date
            )  # Assumes format_iso_date is implemented
    return version_info


def load_and_tag_model_data(filenames: list) -> dict:
    """Load model data from tuple of JSON files and corresponding OS versions string,
    merge into a dict mapping each model to its details including supported OS versions
    """
    model_info = {}
    for file_path, os_version in filenames:
        with open(file_path, "r", encoding="utf-8") as model_json:
            data = json.load(model_json)
            for model in data:
                for identifier, name in model["Identifiers"].items():
                    formatted_os_version = " ".join(os_version.split()[1:]).strip()
                    if identifier not in model_info:
                        model_info[identifier] = {
                            "MarketingName": name,
                            "SupportedOS": [formatted_os_version],
                            "OSVersions": [int(formatted_os_version.split()[-1])],
                        }
                    else:
                        if (
                            formatted_os_version
                            not in model_info[identifier]["SupportedOS"]
                        ):
                            model_info[identifier]["SupportedOS"].append(
                                formatted_os_version
                            )
                            model_info[identifier]["OSVersions"].append(
                                int(formatted_os_version.split()[-1])
                            )
    return model_info


def load_supported_devices_data():
    """Load the supported devices data from the cache"""
    supported_devices_file = os.path.join('cache', 'supported_devices.json')
    with open(supported_devices_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Map OSVersion to SupportedDevices for easy lookup
    return {str(entry["OSVersion"]): entry["SupportedDevices"] for entry in data}


def load_macos_data_feed():
    """Load the macOS data feed from the root directory"""
    macos_data_feed_file = 'macos_data_feed.json'
    with open(macos_data_feed_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def merge_device_lists(current_devices, additional_devices):
    """Merge two lists of devices, remove duplicates, and return them sorted."""
    return sorted(set(current_devices).union(additional_devices))


def extract_versions(data):
    """Extract versions from the primary data, gathering SupportedDevices for each ProductVersion."""
    result = []
    for os_version in data.get("OSVersions", []):
        if isinstance(os_version, dict):
            for release_type in ["Latest", "SecurityReleases"]:
                releases = os_version.get(release_type)
                if releases:
                    releases = releases if isinstance(releases, list) else [releases]
                    for release in releases:
                        product_version = release.get("ProductVersion")
                        if isinstance(product_version, str):
                            devices = release.get("SupportedDevices", [])
                            result.append({product_version: devices})
    return sorted(result, key=lambda x: tuple(map(int, next(iter(x)).split("."))))


def inject_supported_devices(versions, supported_devices_data):
    """Inject supported devices into each OS version based on major version."""
    for version_dict in versions:
        version_str, devices = next(iter(version_dict.items()))
        major_version = version_str.split(".")[0]
        if major_version in supported_devices_data and not devices:
            devices.extend(supported_devices_data[major_version])
            print(f"Injected supported devices for {version_str}: {supported_devices_data[major_version]}")
    return versions


def layer_supported_devices(versions):
    """Layer supported devices within each major version."""
    layered_versions = {}
    for version_dict in versions:
        version_str, devices = next(iter(version_dict.items()))
        major_version = version_str.split(".")[0]
        if major_version not in layered_versions:
            layered_versions[major_version] = []
        if devices and not layered_versions[major_version]:
            layered_versions[major_version] = devices.copy()
        else:
            devices = merge_device_lists(layered_versions[major_version], devices)
        layered_versions[major_version] = devices
        version_dict[version_str] = devices
    return versions


def merge_devices_from_cached_data(final_versions_data, cached_data):
    """Update `final_versions_data` with missing devices from `cached_data` for matching ProductVersion entries."""
    cached_macos_versions = []
    for asset_set in ["PublicAssetSets", "AssetSets"]:
        cached_macos_versions.extend(cached_data.get(asset_set, {}).get("macOS", []))
    
    for version_data in final_versions_data:
        version_str, current_devices = next(iter(version_data.items()))
        for cached_version in cached_macos_versions:
            if cached_version["ProductVersion"] == version_str:
                cached_devices = cached_version.get("SupportedDevices", [])
                missing_devices = [device for device in cached_devices if device not in current_devices]
                if missing_devices:
                    version_data[version_str] = merge_device_lists(current_devices, cached_devices)
                    print(f"Updated {version_str} with missing devices from cached data: {missing_devices}")
    return final_versions_data


def update_supported_devices_in_feed(data, supported_devices_data):
    """Update the 'SupportedDevices' in `data` by consolidating data from multiple sources."""
    extracted_sorted_data = extract_versions(data)
    injected_versions_data = inject_supported_devices(extracted_sorted_data, supported_devices_data)
    layered_versions_data = layer_supported_devices(injected_versions_data)
    
    cached_data, _ = check_cache_file("cache/gdmf_cached.json", verbose=False)
    if cached_data:
        final_versions_data = merge_devices_from_cached_data(layered_versions_data, cached_data)
    else:
        final_versions_data = layered_versions_data

    final_versions_lookup = {version_str: devices for entry in final_versions_data for version_str, devices in entry.items()}

    # Sort OSVersions based on ProductVersion in chronological order
    sorted_os_versions = []
    for os_version_data in data.get("OSVersions", []):
        for release_type in ["Latest", "SecurityReleases"]:
            releases = os_version_data.get(release_type)
            if releases:
                releases = releases if isinstance(releases, list) else [releases]
                for release in releases:
                    product_version = release.get("ProductVersion")
                    if product_version:
                        sorted_os_versions.append((packaging.version.parse(product_version), release))

    # Sort the consolidated list of versions
    sorted_os_versions.sort(key=lambda x: x[0])

    # Track cumulative devices for each major version
    cumulative_devices_by_major = {}

    # Now loop through the sorted versions and update SupportedDevices
    for _, release in sorted_os_versions:
        product_version = release.get("ProductVersion")
        major_version = product_version.split(".")[0]
        
        # Initialize cumulative devices for this major version if not present
        if major_version not in cumulative_devices_by_major:
            cumulative_devices_by_major[major_version] = set()

        # Get current devices from release, default to empty if none
        current_devices = set(release.get("SupportedDevices", []))

        # Merge cumulative devices with current devices for this release
        consolidated_devices = merge_device_lists(
            cumulative_devices_by_major[major_version],  # cumulative up to this version
            final_versions_lookup.get(product_version, [])  # additional devices from final lookup
        )

        # Update the release's SupportedDevices with the consolidated devices
        added_devices = sorted(set(consolidated_devices) - current_devices)
        release["SupportedDevices"] = sorted(consolidated_devices)
        
        # Update cumulative devices for this major version
        cumulative_devices_by_major[major_version].update(consolidated_devices)

        # Log added devices if any were added
        if added_devices:
            print(f"Final update for {product_version} with added SupportedDevices: {added_devices}")
    
    return data


def pretty_print_json(data):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=4))


def save_updated_macos_data_feed(macos_data_feed):
    """Save the updated macOS data feed to the file"""
    macos_data_feed_file = 'macos_data_feed.json'
    with open(macos_data_feed_file, 'w', encoding='utf-8') as f:
        json.dump(macos_data_feed, f, indent=4)


def save_original_macos_data_feed(macos_data_feed):
    """Save the updated macOS data feed to the file"""
    macos_data_feed_file = 'macos_data_feed_original.json'
    with open(macos_data_feed_file, 'w', encoding='utf-8') as f:
        json.dump(macos_data_feed, f, indent=4)


def fetch_latest_os_version_info(
    os_type: str, os_version_name: str, gdmf_data: dict
) -> dict:
    """Fetch the latest version information for the given OS type&version name using provided GDMF data"""  # noqa: E501 pylint: disable=line-too-long
    # TODO: split this as indicated above in main() to process alongside a forked process_os_type()
    print(f"Fetching latest: {os_type} {os_version_name}")
    os_versions_key = (
        "macOS" if os_type == "macOS" else "iOS"
    )  # TODO: why is this just not using os_type?
    filtered_versions = [  # TODO: add example expected data to explain filtering
        version
        for version in gdmf_data.get("PublicAssetSets", {}).get(os_versions_key, [])
        if version.get("ProductVersion", "").startswith(
            os_version_name.split(" ")[-1] if os_type == "macOS" else os_version_name
        )
    ]
    if os_type == "iOS":
        filtered_versions = [  # TODO: add example expected data to explain filtering
            iversion
            for iversion in filtered_versions
            if "SupportedDevices" in iversion
            and any(
                device.startswith("iPad") or device.startswith("iPhone")
                for device in iversion["SupportedDevices"]
            )
        ]
    if filtered_versions:
        # Sort by device count (descending) and then by PostingDate (latest first)
        latest_version = max(
            filtered_versions,
            key=lambda version: (
                len(version.get("SupportedDevices", [])),  # Prioritize larger device counts
                datetime.strptime(version["PostingDate"], "%Y-%m-%d")  # Then by latest date
            )
        )
        return {
            "ProductVersion": latest_version.get("ProductVersion"),
            "Build": latest_version.get("Build"),
            "ReleaseDate": latest_version.get("PostingDate"),
            "ExpirationDate": latest_version.get("ExpirationDate", ""),
            "SupportedDevices": latest_version.get("SupportedDevices", []),
        }
    print(f"No versions matched the criteria for {os_type} {os_version_name}.")
    return {}


def format_iso_date(date_str: str) -> str:
    """Format the date string to ISO 8601 format
    or a hardcoded date if the input is 'Preinstalled'"""
    if date_str == "Preinstalled":
        # Return October 25th, 2021 in ISO 8601 format TODO: why that day?
        return "2021-10-25T00:00:00Z"
    formats = ["%Y-%m-%d", "%d %b %Y", "%B %d, %Y"]  # TODO: why?
    for fmt in formats:
        try:
            return (
                datetime.strptime(date_str, fmt).replace(microsecond=0).isoformat()
                + "Z"
            )
        except ValueError:
            pass
    return date_str

def fetch_security_releases(os_type: str, os_version: str, gdmf_data: dict) -> list:
    """Fetch security releases for the given OS type and version, sourced from multiple Apple Support pages."""

    # Updated URLs to include multiple sources
    urls = [
        "https://support.apple.com/en-ca/100100",  # Current info
        "https://support.apple.com/en-ca/121012",  # 2022 to 2023
        #"https://support.apple.com/en-ca/120989",  # 2020 to 2021
        #"https://support.apple.com/en-ca/103179",  # 2018 to 2019
    ]

    security_releases = []
    release_dates = []

    # Loop through each URL to gather security release data
    for url in urls:
        print(f"Fetching data from {url}")
        response = requests.get(url)

        if response.ok:
            html_content = response.text
            soup = BeautifulSoup(html_content, "lxml")
            rows = soup.find_all("tr")

            for row in rows:
                cells = row.find_all("td")
                if cells:
                    name_info = cells[0].get_text(strip=True)
                    os_version_info = process_os_version(os_type, os_version, name_info)
                    # Ensure os_version_info non-empty/matches the targeted version before proceeding
                    if os_version_info and os_version in os_version_info:  # Filter based on the targeted OS version
                        link = cells[0].find("a", href=True)
                        if link:
                            link_info = urljoin("https://support.apple.com", link["href"])
                            cves_exploitation_status = fetch_cves(link_info)
                        else:
                            link_info = None
                            cves_exploitation_status = {}
                        # extract ProductVersion from the name_info, any digit(s), dot, any digit(s)
                        version_match = re.search(r"\d+(\.\d+)*", name_info)
                        product_version = version_match.group() if version_match else "Unknown"
                        # Ensure that product_version includes the minor version or add .0 see GH issue #174
                        if '.' not in product_version:
                            product_version += '.0'
                        print(f"Processing security release {product_version}, source {name_info}")
                        # Handling the case when the page indicates no published CVE entries
                        if link_info and "no published CVE entries" in fetch_content(link_info).lower():
                            cves_exploitation_status = {}
                        date = cells[-1].get_text(strip=True)
                        release_dates.append(date)
                        # Extract actively exploited CVEs if any
                        actively_exploited_cves = [
                            cve for cve, exploited in cves_exploitation_status.items() if exploited
                        ]
                        os_info = fetch_latest_os_version_info(os_type, product_version, gdmf_data)
                        if not os_info:
                            os_info = {}
                        # Handle RSR releases by grabbing letter in ()
                        rsr_release = None
                        if "Rapid Security Response" in os_version_info:
                            rsr_vers = re.search(r"\((\w)\)", os_version_info)
                            if rsr_vers:
                                rsr_release = rsr_vers.group(1)
                        security_releases.append(
                            {
                                "UpdateName": os_version_info,
                                "ProductName": os_type,
                                "ProductVersion": product_version,
                                "ReleaseDate": date,
                                "ReleaseType": (
                                    f"RSR_{rsr_release}" if rsr_release else "OS"
                                ),
                                "SecurityInfo": (
                                    link_info
                                    if link_info
                                    else "This update has no published CVE entries."
                                ),
                                "SupportedDevices": os_info.get("SupportedDevices", []),
                                "CVEs": cves_exploitation_status,
                                "ActivelyExploitedCVEs": actively_exploited_cves,
                                "UniqueCVEsCount": len(cves_exploitation_status),
                            }
                        )
            days_since_previous_release = calculate_days_since_previous_release(release_dates)
            for release in security_releases:
                release_date = release["ReleaseDate"]
                if release_date in days_since_previous_release:
                    release["DaysSincePreviousRelease"] = days_since_previous_release[release_date]
                else:
                    release["DaysSincePreviousRelease"] = 0
        else:
            print(f"Failed to retrieve data from {url}")
            continue  # Skip to the next URL if the current one fails

    return security_releases if security_releases else print("Failed to retrieve security releases.") or []



def process_os_version(os_type: str, os_version: str, name_info: str) -> str:
    """Process the OS version information from the given name_info.
    Needed to scrape CVE/rapid response info"""
    print(f"Processing data - {os_type}: {os_version}, Searching in: {name_info} ")
    rapid_response_prefix = "Rapid Security Response"
    pattern = rf"({rapid_response_prefix})?\s*"  # Cool f-string, brosif
    pattern += r"(macOS\s+\w+\s*\d+(?:\.\d+)*(?:\.\d+)*(?:\s*\([a-z]\))?)?\s*"
    pattern += r"((iOS|iPadOS)\s+(\d+(?:\.\d+)?(?:\.\d+)?)(?:\s*\([a-z]\))?)?"
    pattern += r"(\s+and\s+)?"  # TODO: What's this one for?
    pattern += r"((iOS|iPadOS)\s+(\d+(?:\.\d+)?(?:\.\d+)?)(?:\s*\([a-z]\))?)?"  # TODO: Duplicate-looking, but needed, yes?  # noqa: E501 pylint: disable=line-too-long
    match = re.search(pattern, name_info, re.IGNORECASE)
    if match:
        rapid_response = match.group(1) or ""
        macos_part = match.group(2) or ""
        first_os_part = match.group(3) or ""
        second_os_connector = match.group(6) or ""
        second_os_part = match.group(7) or ""
        # Ensure proper spacing after "Rapid Security Response" if it's present
        version_str = f"{rapid_response} " if rapid_response else ""
        # Concatenating OS parts with appropriate spacing
        if macos_part:
            version_str += f"{macos_part} "
        if first_os_part:
            version_str += f"{first_os_part} "
        if second_os_connector and second_os_part:
            version_str += f"and {second_os_part}"
        return version_str.strip()
    return ""


def fetch_cves(url: str) -> dict:
    """Fetch CVEs from the security release URL, as sourced from HT201222 page"""
    response = requests.get(url)
    if not response.ok:
        return {}  # Indicate failure to fetch or process CVEs
    html_content = response.text
    soup = BeautifulSoup(html_content, "html.parser")
    if "no published CVE entries" in html_content:  # Simplistic check; refine as needed
        return {}  # Explicitly indicate no CVEs without error
    exploited = re.compile(
        r"Impact:.*Apple is aware.*may have been .*exploited", re.DOTALL
    )
    cves_info = {}
    text_blocks = []
    processed_cves = set()
    for child in soup.recursiveChildGenerator():  # TODO: explain rest of this...
        if isinstance(child, NavigableString) and child.strip():
            text_blocks.append(child.strip())
            cve_ids = re.findall(r"\bCVE-\d{4,}-\d{4,}\b", child)
            for cve_id in cve_ids:
                if cve_id not in processed_cves:
                    cves_info[cve_id] = bool(exploited.search(" ".join(text_blocks)))
                    processed_cves.add(cve_id)
            if (
                len(text_blocks) > 5
            ):  # TODO: explain why this/what 'Maintain recent context' means
                text_blocks.pop(0)
    return cves_info


def calculate_days_since_previous_release(release_dates: list) -> dict:
    """Calculate the days between each release date and the previous sequentially"""
    days_between_releases = {}
    try:
        date_objects = [parse_flexible_date(date) for date in release_dates]
        date_objects.sort(reverse=True)
        for i in range(len(date_objects) - 1):
            days_difference = (date_objects[i] - date_objects[i + 1]).days
            days_between_releases[release_dates[i]] = days_difference
        # Handle the last element which will always have 0 days since previous release
        if release_dates:
            days_between_releases[release_dates[-1]] = 0
    except ValueError as e:
        print(f"Error parsing date: {e}")
    return days_between_releases

def parse_flexible_date(date_str: str) -> datetime:
    """Parse a date string with flexible formats to sanitize data scraped from the webpage"""
    formats = ["%Y-%m-%d", "%d %b %Y", "%B %d, %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Date format not recognized: {date_str}")

def add_compatible_machines(current_macos_full_version: str) -> list:
    """Add compatible machines for the given macOS version, only processed for macOS"""
    # Extract lowercase OS 'name' to find file of compatible machines
    current_macos_name = current_macos_full_version.split(" ")[
        0
    ].lower()  # This will get "ventura" from "Ventura 13"
    filename = f"model_identifier_{current_macos_name}.json"
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return []
    compatible_machines = []
    for entry in data:
        model = entry["Model"]
        url = entry["URL"]
        identifiers = entry["Identifiers"]
        compatible_machines.append(
            {"Model": model, "URL": url, "Identifiers": identifiers}
        )
    return compatible_machines


def write_data_to_json(feed_structure: dict, filename: str):
    """Writes the fully populated feed structure to JSON filename"""
    latest_versions = {}

    for os_version in feed_structure["OSVersions"]:
        if "Latest" in os_version:
            latest_dict = os_version["Latest"]

            # Ensure all required keys are present with default values
            latest_dict["ProductVersion"] = latest_dict.get("ProductVersion", "")
            latest_dict["ReleaseDate"] = latest_dict.get("ReleaseDate", "")
            latest_dict["ExpirationDate"] = latest_dict.get("ExpirationDate", "")
            latest_dict["Build"] = latest_dict.get("Build", "")
            latest_dict["SecurityInfo"] = latest_dict.get("SecurityInfo", "")
            latest_dict["UniqueCVEsCount"] = latest_dict.get("UniqueCVEsCount", 0)
            latest_dict["ActivelyExploitedCVEs"] = latest_dict.get("ActivelyExploitedCVEs", [])
            latest_dict["CVEs"] = latest_dict.get("CVEs", {})
            latest_dict["SupportedDevices"] = latest_dict.get("SupportedDevices", [])

            # Convert dates to ISO format
            latest_dict["ReleaseDate"] = format_iso_date(latest_dict.get("ReleaseDate", ""))
            latest_dict["ExpirationDate"] = format_iso_date(latest_dict.get("ExpirationDate", ""))

            product_version = latest_dict["ProductVersion"]

            # Store the latest version info for comparison
            latest_versions[product_version] = {
                "latest_date": latest_dict["ReleaseDate"],
                "os_version_dict": os_version
            }

        # Handle SecurityReleases similarly if present
        if "SecurityReleases" in os_version and isinstance(os_version["SecurityReleases"], list):
            for release in os_version["SecurityReleases"]:
                release["ProductVersion"] = release.get("ProductVersion", "")
                release["ReleaseDate"] = release.get("ReleaseDate", "")
                release["ReleaseDate"] = format_iso_date(release.get("ReleaseDate", ""))

                product_version = release["ProductVersion"]
                if product_version in latest_versions:
                    # Update security date if the product version matches
                    latest_versions[product_version]["security_date"] = release["ReleaseDate"]

    # Update all relevant Latest entries with their respective security dates
    for product_version, version_info in latest_versions.items():
        if "security_date" in version_info:
            latest_dict = version_info["os_version_dict"]["Latest"]
            original_date = latest_dict.get("ReleaseDate", "")
            new_date = version_info["security_date"]
            latest_dict["ReleaseDate"] = new_date
            print(f"Updated {product_version} ReleaseDate from {original_date} to {new_date}")

    # Write the updated feed structure back to a file
    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump(
            feed_structure, json_file, indent=4, ensure_ascii=False
        )  # TODO: ascii false because we might have utf8 in it?


def create_rss_json_data(feed_structure: dict) -> list:
    """Pull all data parsed/processed on this run as per os_type(s)"""
    feed_list = []
    try:
        # For each OS Version, retrieve SecurityReleases, populate list
        for os_version in feed_structure["OSVersions"]:
            security_releases = os_version.get("SecurityReleases", [])
            feed_list.extend(security_releases)
        # Handle XProtect data separately and create entries to be cached.
        if "XProtectPlistConfigData" in feed_structure:
            config_datas = feed_structure["XProtectPlistConfigData"]
            config_data_version = config_datas.get("com.apple.XProtect", "")
            config_date = config_datas.get("ReleaseDate", "")
            feed_list.extend(
                [
                    {
                        "UpdateName": f"XProtect Plist Config {config_data_version}",
                        "ProductName": "XProtect",
                        "ProductVersion": config_data_version,
                        "ReleaseType": "Config",
                        "ReleaseDate": config_date,
                    }
                ]
            )
        if "XProtectPayloads" in feed_structure:
            payload_data = feed_structure.get("XProtectPayloads", {})
            remediator_version = payload_data.get(
                "com.apple.XProtectFramework.XProtect", ""
            )
            plugin_service = payload_data.get(
                "com.apple.XprotectFramework.PluginService", ""
            )
            payload_date = payload_data.get("ReleaseDate", "")
            feed_list.extend(
                [
                    {
                        "UpdateName": f"XProtect Remediator {remediator_version}",
                        "ProductName": "XProtect",
                        "ProductVersion": remediator_version,
                        "ReleaseType": "Remediator",
                        "ReleaseDate": payload_date,
                    },
                    {
                        "UpdateName": f"XProtect Plug-in Service {plugin_service}",
                        "ProductName": "XProtect",
                        "ProductVersion": plugin_service,
                        "ReleaseType": "Plug-in",
                        "ReleaseDate": payload_date,
                    },
                ]
            )
    except Exception as feed_populate_err:
        print(f"Error creating list for RSS of JSON data: {feed_populate_err}")
    return feed_list


def write_timestamp_and_hash(os_type: str, hash_value: str, filename=None):
    """Record timestamp and hash value for each os_type in a timestamp.json file
    {
        "macOS": {
            "LastCheck": "timestamp",
            "UpdateHash": "hash_value"
        },
        "iOS": { ...
        can be overridden by environment variable 'TIMESTAMP_FILE_PATH' if 'filename' is None
    """
    if filename is None:
        # Default to current directory or when run in docker we can specify custom default path
        filename = os.getenv("TIMESTAMP_FILE_PATH", "timestamp.json")
    last_check = datetime.now(timezone.utc).replace(microsecond=0).isoformat() + "Z"
    timestamp_data: dict = {"macOS": {}, "iOS": {}}
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                timestamp_data = json.load(file)
        except json.JSONDecodeError:
            # If JSON decode fails, continue and overwrite
            pass
    timestamp_data[os_type] = {"LastCheck": last_check, "UpdateHash": hash_value}
    with open(filename, "w", encoding="utf-8") as timestamp_file:
        json.dump(timestamp_data, timestamp_file, indent=4)


def read_and_validate_json(filename: str):
    """Read and validate the JSON file. Print verbose output"""
    try:
        with open(filename, "r", encoding="utf-8") as file:  # TODO: leverage jsonschema
            data = json.load(file)
            # Adjusted required keys for a more generic approach
            required_keys = [  # Additional keys like "XProtectPlistConfigData" and "XProtectPayloads" may not be relevant for all OS types # noqa: E501 pylint: disable=line-too-long
                "OSVersions",
                # "Latest",  # Generic key for latest OS version info
                # "SecurityReleases",
            ]
            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                print(f"Validation error: Missing keys {missing_keys} in {filename}")
            else:
                print(f"Validation passed for {filename}.")
                print(json.dumps(data, indent=4))
    except FileNotFoundError:
        print(f"File not found: {filename}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON from the file: {filename}")
    except Exception as e:
        print(f"An error occurred: {e}")


def diff_rss_data(feed_results: list, rss_cache: list):
    """Diffs feed results & cache, updates cache for each OS type, and returns
    a combined list of updated data"""
    data: list = []
    try:
        new_entries: list = []
        os_type_names = set(entry["ProductName"] for entry in feed_results)
        # build list if dict matching os_type, e.g. macOS or iOS
        for type_name in os_type_names:
            cached_os_data = [
                item for item in rss_cache if item.get("ProductName") == type_name
            ]
            # Extract unique identifiers for existing data
            existing_os_items = {
                f"{item['ReleaseType']}_{item['ProductVersion']}"
                for item in cached_os_data
                if "ReleaseType" in item
            }
            existing_os_items.update(  # faster to make 2nd generator
                {
                    item["ProductVersion"]
                    for item in cached_os_data
                    if "ReleaseType" not in item
                }
            )
            new_os_entries = [
                entry
                for entry in feed_results
                if entry["ProductName"] == type_name
                and f"{entry['ReleaseType']}_{entry['ProductVersion']}"
                not in existing_os_items
            ]
            # Update cache files if there are new entries
            if new_os_entries:
                cached_os_data.extend(new_os_entries)
                write_os_data_to_cache(type_name, cached_os_data)
                new_entries.extend(new_os_entries)
                print(f"RSS: Cache updated for {type_name}")
            else:
                print(f"No new entries found for {type_name}")
        rss_cache.extend(new_entries)
        diff_result = remove_dict_duplicates(rss_cache)
        data = sort_data(diff_result, "ReleaseDate")
        return data
    except Exception as e:
        print(f"Error diffing RSS data with cache: {e}")
        return data


def write_os_data_to_cache(product_name: str, data: list):
    """Write updated data to the cache"""
    rss_cache_dir = (
        "cache"  # TODO: consider making this a global, as per load_rss_data_cache()
    )
    os_rss_cache = os.path.join(rss_cache_dir, f"{product_name}_rss_data.json")
    data = sort_data(data, "ReleaseDate")
    try:
        os.makedirs(rss_cache_dir, exist_ok=True)
        with open(os_rss_cache, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print(f"Error writing to cache file {os_rss_cache}: {e}")


def remove_dict_duplicates(data: list) -> list:
    """Remove duplicate dictionaries (or lists) from a list"""
    new_set = set()
    unique_list = []
    for item in data:
        item_tuple = item
        if isinstance(item, (list, dict)):
            item_tuple = json.dumps(item, sort_keys=True)
        if item_tuple not in new_set:
            new_set.add(item_tuple)
            unique_list.append(item)
    return unique_list


def sort_data(data: list, sort_by: str) -> list:
    """Sort data based on sort_by key"""
    sorted_data = data
    if data:
        sorted_data = sorted(data, key=lambda x: x[sort_by])
    return sorted_data


def write_data_to_rss(sorted_feed: list, filename: str):
    """Write the sorted feed to a RSS feed"""
    # Escape if empty list
    if not sorted_feed:
        print("No entries to write. sorted_feed is empty.")
        return
    try:
        # Set the primary feed information
        feed_gen = FeedGenerator()
        feed_gen.id("https://sofa.macadmins.io")
        feed_gen.title("SOFA - RSS Update Feed")
        feed_gen.description(
            "This feed includes updates on OS versions and security info."
        )
        feed_gen.author({"name": "Mac Admins"})
        feed_gen.link(href="https://sofa.macadmins.io", rel="alternate")
        feed_gen.logo("https://sofa.macadmins.io/images/custom_logo.png")
        feed_gen.subtitle("Simple Organized Feed for Apple Software Updates")
        feed_gen.link(href=f"https://sofa.macadmins.io/v1/{filename}", rel="self")
        feed_gen.language("en")
        # For each item in the sorted list, create a new entry in RSS Feed
        for release in sorted_feed:
            feed_entry = feed_gen.add_entry()
            feed_entry.id(
                f"{release['ProductName']}_{release['ReleaseType']}_{release['ProductVersion']}"
            )
            feed_entry.title(release["UpdateName"])
            feed_entry.link(link={"href": "https://sofa.macadmins.io/"})
            description = ""
            if "UniqueCVEsCount" in release:
                description += (
                    f"Vulnerabilities Addressed: {release['UniqueCVEsCount']}<br>"
                )
            if "CVEs" in release:
                exploited = sum(value is True for value in release["CVEs"].values())
                description += f"Exploited CVE(s): {exploited}<br>"
            if "DaysSincePreviousRelease" in release:
                description += (
                    f"Days to Prev. Release: {release['DaysSincePreviousRelease']}"
                )
            feed_entry.description(description)
            publication_date = release["ReleaseDate"]
            feed_entry.published(publication_date)
        feed_gen.rss_file(filename, pretty=True)
    except Exception as rss_write_err:
        print(f"Error writing RSS feed: {rss_write_err}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process OS version information.")
    parser.add_argument(
        "osTypes",
        nargs="+",
        type=str,
        help="The types of OS to process (e.g., macOS iOS)",
    )
    args = parser.parse_args()
    main(args.osTypes)
