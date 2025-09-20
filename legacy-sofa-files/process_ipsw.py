"""Parses the catalog returned from the MESU API and chooses the 'universal'/current macOS IPSW"""

import plistlib
import re
import ssl
from collections import Counter
from urllib.request import urlopen

import certifi  # maybe I don't need any of this SSL handling,

# depending on how python on the runner points at certs? leaving for ease of dev


def main() -> None:
    """gimme some main"""
    mesu_url: str = (
        "https://mesu.apple.com/assets/macos/com_apple_macOSIPSW/com_apple_macOSIPSW.xml"  # noqa: E501 pylint: disable=line-too-long
    )
    # boilerplate context to have cert verification work without other magic
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.load_verify_locations(cafile=certifi.where())
    try:
        with urlopen(mesu_url, context=ctx) as response:
            mesu_cat = response.read()
    except (Exception, OSError) as erroir:  # pylint: disable=broad-exception-caught
        print(f"Error fetching mesu assets, {erroir}")
        raise
    mesu_catalog: dict = plistlib.loads(mesu_cat)
    restore_datas = extract_ipsw_raw(mesu_catalog)
    prevalent_url, prevalent_build, prevalent_version = process_ipsw_data(restore_datas)
    apple_slug = process_slug(prevalent_url)
    print(f"{prevalent_version} - {prevalent_build}, {apple_slug}:\n\t{prevalent_url}")


def extract_ipsw_raw(mesu_catalog: dict):
    """Trusts nothing about MESU format even though this is prolly over-defensive
    Extracts/returns most prevalent firmware URL+build+version in mesu cat"""
    restore_datas: list = []
    root_dict: dict = mesu_catalog.get("MobileDeviceSoftwareVersionsByVersion", {})
    if root_dict:
        dict_one: dict = root_dict.get(
            "1", {}
        )  # for some reason there's a 1 one level deep?
        for _, model_data in dict_one.get("MobileDeviceSoftwareVersions", {}).items():
            # Iterate over the dictionaries inside the model dictionary
            for (
                _,
                build_data,
            ) in model_data.items():  # key looks like build, but we don't trust it
                # check if 'Restore' key exists in build dict
                restore_data: dict = build_data.get("Restore", {})
                if restore_data:
                    restore_datas.append(restore_data)
    return restore_datas


def process_ipsw_data(restore_datas: list) -> tuple[str, str, str]:
    """Given extracted restore data, returns most common/prevalent"""
    firmware_urls: list = []
    builds: list = []
    versions: list = []
    extracts: list = ["FirmwareURL", "BuildVersion", "ProductVersion"]
    # Extract the url, version, build from 'Restore' dict
    for r_data in restore_datas:
        for each in extracts:
            value = r_data.get(each, False)
            if value:
                if each == "FirmwareURL":
                    firmware_urls.append(value)
                elif each == "BuildVersion":
                    builds.append(value)
                elif each == "ProductVersion":
                    versions.append(value)
    # Counter constructors to get occurrences of each unique value per list
    url_counts: Counter = Counter(firmware_urls)
    build_counts: Counter = Counter(builds)
    version_counts: Counter = Counter(versions)
    # most_common(1) function on a counter returns a list of tuples
    # each containing [element, count], sorted in descending order by count
    # index into first tuple's first element to get the most frequent
    prevalent_url = url_counts.most_common(1)[0][0] if url_counts else ""
    prevalent_build = build_counts.most_common(1)[0][0] if build_counts else ""
    prevalent_version = version_counts.most_common(1)[0][0] if version_counts else ""
    # Return the most frequent URL and build
    return prevalent_url, prevalent_build, prevalent_version


def process_slug(prevalent_url: str) -> str:
    """Processes the url to extract apple's 'slug'"""
    # again I'm tracking an apple slug for informational purposes... maybe useless?
    # e.g. in format 052-77579, in ~3rd path section of example full URL:
    # https://updates.cdn-apple.com/2024WinterFCS/fullrestores/052-77579/4569734E-120C-4F31-AD08-FC1FF825D059/UniversalMac_14.4.1_23E224_Restore.ipsw   # noqa: E501 pylint: disable=line-too-long
    pattern = r"/(\d{3}-\d{5})/"
    match = re.search(pattern, prevalent_url)
    if match:
        return match.group(1)
    return "unknown_appleslug"


if __name__ == "__main__":
    # main()
    print("Library of ipsw processing for SOFA.")
