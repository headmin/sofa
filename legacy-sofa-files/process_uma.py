"""Helper library specific to uma parsing/URL/metadata processing
Can run standalone if you uncomment first line under `if __name__ ==...
Majority of code by Alex Ferrer Alequin github.com/Arequ except for errors,
which are all courtesy Allister Banks @arubdesu
"""

import plistlib
import ssl
import urllib
from urllib.request import urlopen
from xml.dom import minidom
from xml.dom.minidom import Element, Text
from xml.parsers.expat import ExpatError

import certifi


def main():
    """gimme some main"""
    cat_url = "https://swscan.apple.com/content/catalogs/others/index-14-13-12-10.16-10.15-10.14-10.13-10.12-10.11-10.10-10.9-mountainlion-lion-snowleopard-leopard.merged-1.sucatalog"  # noqa: E501 pylint: disable=line-too-long
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.load_verify_locations(cafile=certifi.where())
    try:
        # boilerplate context to have cert verification work without other magic
        with urlopen(cat_url, context=ctx) as response:
            catalog = response.read()
    except (Exception, OSError) as erroir:  # pylint: disable=broad-exception-caught
        print(f"Error fetching swupdate catalog, {erroir}")
        raise
    unrefined_products = initial_uma_parse(catalog)
    # let CI job see status output
    print(f"Extracted {len(unrefined_products)} potential UMA packages")
    final_dict = {}
    for slug, prod_dict in unrefined_products.items():
        title, build, version = get_metadata(ctx, prod_dict.get("dist_url"))
        if title:
            final_dict[slug] = {
                "build": build,
                "title": title,
                "version": version,
                "url": prod_dict.get("URL"),
                "apple_slug": slug,
            }
    latest, rest = sort_installers(final_dict)
    print(
        f"Latest UMA package is {latest['title']} {latest['version']}, build {latest['build']}"
    )
    print("\n".join(str(valyous) for valyous in rest))


def initial_uma_parse(catalog: bytes) -> dict:
    """Does initial processing to extract macOS installers from swupdate catalog.
    Passes back 'unrefined' dict (of dicts of products) with uma pkg URLs."""
    unrefined_products = {}
    # file not actually gzipped(!?), plist load bytes object directly
    catalog_dict = plistlib.loads(catalog)
    # schema note: as of 2024, besides Products, there's 3 one-value keys at the root
    #  which we don't need/throw away - CatalogVersion, ApplePostURL, IndexDate.
    # variable-ize two keys (the 2nd nested in the 1st) that denote UMA-related stanzas
    emi_key = "ExtendedMetaInfo"
    iapi_key = "InstallAssistantPackageIdentifiers"
    # product_key is in the XXX-XXXXX format, e.g. 042-45246, which you see as sort-of
    #  'name-spacing' in each URL
    for product_key in catalog_dict["Products"].keys():
        product = catalog_dict["Products"][product_key]
        # .get'ing without fallback to just avoid KeyError in lookup & skip invalid
        if product.get(emi_key) and product.get(emi_key).get(iapi_key):
            # further schema notes: each product has single values for DeferredSUEnablementDate,
            #  State, ExtendedMetaInfo, PostDate, except for 1. Distributions, with a single
            #  nested dict of English as key and .dist URL as value,
            #  the aforementioned ExtendedMetaInfo with string values for SharedSupport,
            #  InstallInfo, Info, UpdateBrain, BuildManifest under the referenced iapi_key,
            # and Packages with Size, IntegrityDataSize, IntegrityDataURL referring to a
            #  BuildManifest.plist.integrityDataV1 and URL w/ a BuildManifest.plist
            # UMA stanza's additionally have Digest and MetadataURL keys
            # even with those nested keys sometimes there's no actual .pkg URL
            #  == extract valid dict using list comprehension
            got_pkg = [
                pkg
                for pkg in product["Packages"]
                if pkg["URL"].endswith("InstallAssistant.pkg")
            ]
            if got_pkg:
                pkg_dict = got_pkg[0]
                dist_url = product["Distributions"].get("English")
                pkg_dict["dist_url"] = dist_url
                unrefined_products[product_key] = pkg_dict
    return unrefined_products


def get_metadata(ctx, dist_url: str) -> tuple[str, str, str]:
    """takes dist URL"""
    try:
        with urlopen(dist_url, context=ctx) as dist_response:
            dist_data = dist_response.read().decode()
    except urllib.error.URLError as urle:
        print(f"Error downloading .dist from URL {dist_url}: {urle}")
    title: str = ""
    build: str = ""
    version: str = ""
    try:
        xmldoc = minidom.parseString(dist_data)
        # DEBUG - contains js installer script embedded in xml
        # print(xmldoc.toprettyxml(indent="  "))
        title_elements = xmldoc.getElementsByTagName("title")
        if title_elements:
            title_element = title_elements[0]
            if isinstance(title_element, Element) and isinstance(
                title_element.firstChild, Text
            ):
                title = title_element.firstChild.data
        string_elements = xmldoc.getElementsByTagName("string")
        if string_elements:
            build_element = string_elements[0] if len(string_elements) > 0 else None
            version_element = string_elements[1] if len(string_elements) > 1 else None
            if isinstance(build_element, Element) and isinstance(
                build_element.firstChild, Text
            ):
                build = build_element.firstChild.data
            if isinstance(version_element, Element) and isinstance(
                version_element.firstChild, Text
            ):
                version = version_element.firstChild.data
    except ExpatError as xmle:
        print("Error parsing XML:", xmle)
    return title, build, version


def sort_installers(final_dict: dict) -> tuple[dict, list]:
    """Nicety function to take weight outta main, sorts and separates latest"""
    sorted_installers = dict(
        sorted(final_dict.items(), key=lambda item: item[1]["version"], reverse=True)
    )
    latest = next(iter(sorted_installers.values()))
    rest = []
    skip_first = True
    for each in sorted_installers.values():
        if skip_first:
            skip_first = False
            continue
        rest.append(each)
    return latest, rest


if __name__ == "__main__":
    # main()
    print("Library of uma processing for SOFA.")
