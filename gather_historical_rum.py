#!/usr/bin/env python3
"""Read-only, estimated month-end RUM from retained Terraform state versions.

Does not modify the existing current-RUM collectors or Terraform state.
"""
import argparse
import calendar
import csv
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

import requests

UTC = dt.timezone.utc


def timestamp(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def month_starts(start, end):
    year, month = map(int, start.split("-"))
    end_year, end_month = map(int, end.split("-"))
    while (year, month) <= (end_year, end_month):
        yield f"{year:04d}-{month:02d}"
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)


def cutoff(month):
    year, m = map(int, month.split("-"))
    return dt.datetime(year + (m == 12), m % 12 + 1, 1, tzinfo=UTC)


class API:
    def __init__(self, address, token):
        self.base = address.rstrip("/") + "/api/v2"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": "Bearer " + token,
            "Content-Type": "application/vnd.api+json",
        })

    def get(self, path, params=None):
        url = path if path.startswith("https://") else self.base + path
        for attempt in range(7):
            response = self.session.get(url, params=params, timeout=60)
            if response.status_code in (429, 500, 502, 503, 504) and attempt < 6:
                time.sleep(min(2 ** attempt, 30))
                continue
            response.raise_for_status()
            return response.json()
        raise RuntimeError("API retry limit exceeded")

    def pages(self, path, params=None):
        url = path
        first = True
        while url:
            response = self.get(url, params if first else None)
            yield from response.get("data", [])
            next_url = response.get("links", {}).get("next")
            # Relative links are resolved against the API URL; absolute links are used as-is.
            if next_url and next_url.startswith("/api/v2/"):
                url = self.base[:-7] + next_url
            else:
                url = next_url
            first = False


def rum_from_attributes(attrs):
    """Mirror existing collector exclusions when billable-rum-count is unavailable."""
    billed = attrs.get("billable-rum-count")
    if isinstance(billed, int) and not isinstance(billed, bool):
        return billed
    if attrs.get("resources-processed") is False:
        return None
    resources = attrs.get("resources")
    if not isinstance(resources, list):
        return None
    return sum(
        int(r.get("count") or 0) for r in resources
        if r.get("type") != "terraform_data"
        and not str(r.get("type", "")).startswith("data.")
        and r.get("provider") != 'provider["registry.terraform.io/hashicorp/null"]'
    )


def workspace_history(api, organization, workspace):
    params = {
        "filter[organization][name]": organization,
        "filter[workspace][name]": workspace["attributes"]["name"],
        "filter[status]": "finalized",
        "page[size]": 100,
    }
    versions = []
    for version in api.pages("/state-versions", params):
        attrs = version.get("attributes", {})
        if attrs.get("status") not in (None, "finalized"):
            continue
        if attrs.get("intermediate"):
            continue
        when = attrs.get("created-at")
        if when:
            versions.append((timestamp(when), version["id"], attrs))
    return sorted(versions, key=lambda item: (item[0], item[1]))


def report(api, organization, months):
    workspaces = list(api.pages(
        "/organizations/" + requests.utils.quote(organization, safe="") + "/workspaces",
        {"page[size]": 100},
    ))
    totals = {month: {"known_rum": 0, "known_workspaces": 0,
                      "unknown_workspaces": 0, "excluded_not_created": 0}
              for month in months}
    details = []
    now = dt.datetime.now(UTC)
    for workspace in workspaces:
        name = workspace["attributes"]["name"]
        created = workspace["attributes"].get("created-at")
        created_at = timestamp(created) if created else None
        history = workspace_history(api, organization, workspace)
        for month in months:
            end = min(cutoff(month), now + dt.timedelta(microseconds=1))
            if created_at and created_at >= end:
                totals[month]["excluded_not_created"] += 1
                continue
            applicable = [state for state in history if state[0] < end]
            if not applicable:
                value, state_id, status = None, None, "no_retained_state"
            else:
                _, state_id, attrs = applicable[-1]
                value = rum_from_attributes(attrs)
                # Fetch detail only when list metadata is missing the count/resources.
                if value is None:
                    attrs = api.get("/state-versions/" + state_id)["data"]["attributes"]
                    value = rum_from_attributes(attrs)
                status = "known" if value is not None else "unavailable_resources"
            entry = {"month": month, "organization": organization,
                     "workspace_id": workspace["id"], "workspace": name,
                     "rum": value, "status": status, "state_version_id": state_id}
            details.append(entry)
            if value is None:
                totals[month]["unknown_workspaces"] += 1
            else:
                totals[month]["known_rum"] += value
                totals[month]["known_workspaces"] += 1
    summary = []
    for month in months:
        data = totals[month]
        # Never report a partial total as a complete organization-wide RUM count.
        summary.append({"month": month, "organization": organization,
                        "rum": data["known_rum"] if data["unknown_workspaces"] == 0 else None,
                        **data,
                        "complete": data["unknown_workspaces"] == 0})
    add_growth(summary)
    # Details are ordered by workspace and then month, so growth is within each workspace.
    add_growth(details, ("workspace_id",))
    return summary, details


def add_growth(rows, key_fields=()):
    """Month-over-month changes only when both snapshots are known."""
    previous = {}
    for row in rows:
        key = tuple(row[field] for field in key_fields)
        current = row["rum"]
        prior = previous.get(key)
        row["previous_month_rum"] = prior
        row["growth_rum"] = None if prior is None or current is None else current - prior
        row["growth_percent"] = (
            None if row["growth_rum"] is None or prior == 0
            else round(100 * row["growth_rum"] / prior, 2)
        )
        # Report no percent change for a zero baseline; absolute growth remains valid.
        previous[key] = current
    return rows


def print_monthly_summary(rows):
    print("\\nHistorical monthly RUM and growth (estimated month-end):")
    print(f'{"Month":<10} {"RUM":>12} {"Change":>12} {"Growth":>11} {"Coverage":>12}')
    for r in rows:
        fmt = lambda value: "N/A" if value is None else f"{value:,}"
        pct = "N/A" if r["growth_percent"] is None else f'{r["growth_percent"]:+.2f}%'
        coverage = "complete" if r["complete"] else "incomplete"
        print(f'{r["month"]:<10} {fmt(r["rum"]):>12} '
              f'{fmt(r["growth_rum"]):>12} {pct:>11} {coverage:>12}')


def write_csv(path, rows, columns):
    with open(path, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Estimated monthly month-end RUM from retained state.")
    parser.add_argument("-a", "--addr", default=os.getenv("TF_ADDR", "https://app.terraform.io"))
    parser.add_argument("-o", "--organization", required=True)
    parser.add_argument("--start", required=True, help="First month YYYY-MM")
    parser.add_argument("--end", required=True, help="Last month YYYY-MM")
    parser.add_argument("--output-dir", default="historical_rum_output")
    args = parser.parse_args()
    try:
        months = list(month_starts(args.start, args.end))
        if not months or any(len(x) != 7 for x in (args.start, args.end)):
            raise ValueError("Expected start <= end in YYYY-MM")
        # Validate calendar months, and reject future periods.
        dt.date.fromisoformat(args.start + "-01")
        dt.date.fromisoformat(args.end + "-01")
        if args.end > dt.datetime.now(UTC).strftime("%Y-%m"):
            raise ValueError("End month cannot be in the future")
    except ValueError as exc:
        parser.error(str(exc))
    token = os.getenv("TF_TOKEN")
    if not token:
        parser.error("Set TF_TOKEN to a token with workspace and state-version read permissions")
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    try:
        summary, details = report(API(args.addr, token), args.organization, months)
    except (requests.RequestException, KeyError, ValueError) as exc:
        parser.exit(1, f"Historical RUM collection failed: {exc}\n")
    write_csv(out / "monthly_rum.csv", summary,
              ["month", "organization", "rum", "known_rum", "known_workspaces",
               "unknown_workspaces", "excluded_not_created", "complete",
               "previous_month_rum", "growth_rum", "growth_percent"])
    write_csv(out / "workspace_monthly_rum.csv", details,
              ["month", "organization", "workspace_id", "workspace", "rum",
               "status", "state_version_id", "previous_month_rum",
               "growth_rum", "growth_percent"])
    with open(out / "historical_rum.json", "w", encoding="utf-8") as stream:
        json.dump({"organization": args.organization, "summary": summary,
                   "workspace_months": details}, stream, indent=2)
    print_monthly_summary(summary)
    print(f"Wrote {len(summary)} monthly rows and {len(details)} workspace-month rows to {out}")
    if any(not row["complete"] for row in summary):
        print("WARNING: Some months are incomplete; see unknown_workspaces and workspace_monthly_rum.csv",
              file=sys.stderr)


if __name__ == "__main__":
    main()
