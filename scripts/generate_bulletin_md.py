#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""
Generate a markdown bulletin from bulletin_data.json and v2 feed data.

Usage:
    uv run --script scripts/generate_bulletin_md.py
"""

import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BULLETIN = PROJECT_ROOT / "data" / "resources" / "bulletin_data.json"
V2_DIR = PROJECT_ROOT / "v2"
OUTPUT = PROJECT_ROOT / "data" / "resources" / "bulletin.md"


def fmt_date(s: str) -> str:
    if not s:
        return "—"
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except Exception:
        return s


def load_json(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def main():
    bulletin = load_json(BULLETIN)
    if not bulletin:
        print("No bulletin_data.json found")
        return

    lines: list[str] = []
    generated = fmt_date(bulletin.get("generated_at", ""))
    lines.append(f"# SOFA Security Bulletin")
    lines.append(f"")
    lines.append(f"Generated: {generated}")
    lines.append("")

    # Recent releases
    recent = bulletin.get("recent_releases", [])
    if recent:
        lines.append("## Recent Releases")
        lines.append("")
        lines.append("| Date | Release | Platform | Links |")
        lines.append("|------|---------|----------|-------|")
        for r in recent:
            date = fmt_date(r.get("release_date", ""))
            name = r.get("name", "Unknown")
            platform = r.get("platform", "").upper()
            url = r.get("url", "")
            link_parts = []
            if url:
                link_parts.append(f"[Notes]({url})")
            if r.get("enterprise_link"):
                link_parts.append(f"[Enterprise]({r['enterprise_link']})")
            if r.get("updates_link"):
                link_parts.append(f"[What's New]({r['updates_link']})")
            links = " · ".join(link_parts) if link_parts else "—"
            lines.append(f"| {date} | {name} | {platform} | {links} |")
        lines.append("")

    # Latest releases
    latest = bulletin.get("latest_releases", {})
    has_latest = any(v.get("version") for v in latest.values())
    if has_latest:
        lines.append("## Current Latest Versions")
        lines.append("")
        lines.append("| Platform | Version | Build | Released | CVEs | Actively Exploited |")
        lines.append("|----------|---------|-------|----------|------|--------------------|")
        names = {"macos": "macOS", "ios": "iOS", "ipados": "iPadOS", "tvos": "tvOS",
                 "watchos": "watchOS", "visionos": "visionOS", "safari": "Safari"}
        for key, info in latest.items():
            if not info.get("version"):
                continue
            pname = names.get(key, key)
            version = info.get("version", "—")
            build = info.get("build", "—")
            date = fmt_date(info.get("release_date", ""))
            total_cve = info.get("total_cve_count", 0)
            exploited = info.get("actively_exploited_count", 0)
            exploited_str = f"**{exploited}**" if exploited > 0 else "0"
            lines.append(f"| {pname} | {version} | `{build}` | {date} | {total_cve} | {exploited_str} |")
        lines.append("")

    # Security summary
    sec = bulletin.get("security_summary", {})
    if sec.get("unique_cves_fixed") or sec.get("kev_matches"):
        lines.append("## Security Summary")
        lines.append("")
        lines.append(f"- **Unique CVEs fixed:** {sec.get('unique_cves_fixed', 0)}")
        lines.append(f"- **CISA KEV matches:** {sec.get('kev_matches', 0)}")
        if sec.get("kev_cve_list"):
            lines.append(f"- **Actively exploited:** {', '.join(sec['kev_cve_list'])}")
        lines.append("")

    # Beta releases
    betas = bulletin.get("beta_releases", {})
    has_betas = any(v for k, v in betas.items() if k != "latest_wave" and v)
    if has_betas:
        lines.append("## Beta Releases")
        lines.append("")
        wave = fmt_date(betas.get("latest_wave", ""))
        lines.append(f"Latest wave: {wave}")
        lines.append("")
        lines.append("| Platform | Version | Build | Released |")
        lines.append("|----------|---------|-------|----------|")
        names = {"macos": "macOS", "ios": "iOS", "ipados": "iPadOS", "tvos": "tvOS",
                 "watchos": "watchOS", "visionos": "visionOS"}
        for key, info in betas.items():
            if key == "latest_wave" or not info:
                continue
            pname = names.get(key, key)
            lines.append(f"| {pname} | {info.get('version', '—')} | `{info.get('build', '—')}` | {fmt_date(info.get('released', ''))} |")
        lines.append("")

    # BSI data from v2 feeds
    bsi_entries = []
    for feed_file in sorted(V2_DIR.glob("*_data_feed.json")):
        platform = feed_file.stem.replace("_data_feed", "")
        data = load_json(feed_file)
        bsi = data.get("BackgroundSecurityImprovements", {})
        if not bsi or not any(bsi.values()):
            continue
        for os_ver, entries in bsi.items():
            for entry in entries:
                bsi_entries.append({"platform": platform, "os_version": os_ver, **entry})

    if bsi_entries:
        names = {"macos": "macOS", "ios": "iOS/iPadOS", "tvos": "tvOS",
                 "watchos": "watchOS", "visionos": "visionOS"}
        lines.append("## Background Security Improvements")
        lines.append("")
        lines.append("| Platform | Patched Build | Prerequisite | Date | Devices |")
        lines.append("|----------|---------------|--------------|------|---------|")
        for e in sorted(bsi_entries, key=lambda x: (x["platform"], x.get("posting_date", ""))):
            pname = names.get(e["platform"], e["platform"])
            version = e.get("version", "")
            build = e.get("build", "")
            prereq = e.get("prerequisite_build") or "—"
            date = fmt_date(e.get("posting_date", ""))
            devices = len(e.get("supported_devices", []))
            lines.append(f"| {pname} | {version} (`{build}`) | `{prereq}` | {date} | {devices} |")
        lines.append("")

    md = "\n".join(lines)
    OUTPUT.write_text(md)
    print(md)
    print(f"\n---\nWritten to {OUTPUT}")


if __name__ == "__main__":
    main()
