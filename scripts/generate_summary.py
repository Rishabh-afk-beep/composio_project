"""
Generate summary.json from results.json – computes real aggregate statistics and patterns.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def load_json(name):
    p = os.path.join(DATA_DIR, name)
    if os.path.exists(p):
        with open(p, "r") as f:
            return json.load(f)
    return []


def save_json(name, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, name), "w") as f:
        json.dump(data, f, indent=2, default=str)


def main():
    results = load_json("results.json")
    total = len(results)
    if total == 0:
        print("No results found.")
        return

    # ── Count buildability ──
    green, yellow, red, unknown = 0, 0, 0, 0
    covered = 0
    p0, p1, p2, hold, needs_review = 0, 0, 0, 0, 0

    # ── Aggregate stats ──
    has_api = 0
    self_serve = 0
    has_oauth = 0
    has_webhooks = 0
    has_mcp_official = 0
    has_mcp_any = 0

    # ── Category breakdown ──
    category_scores = {}

    for r in results:
        rec = r.get("recommendation", {})
        comp = r.get("composio", {})
        api = r.get("api", {})
        auth = r.get("authentication", {})
        wh = r.get("webhooks", {})
        mcp = r.get("mcp", {})
        cat = r.get("category", "Unknown")

        build = rec.get("buildability", "UNKNOWN")
        prio = rec.get("priority", "HOLD")
        score = rec.get("score", 0)

        # Buildability
        if prio == "COVERED":
            covered += 1
        if build == "GREEN":
            green += 1
        elif build == "YELLOW":
            yellow += 1
        elif build == "RED":
            red += 1
        else:
            unknown += 1

        # Priority
        if prio == "P0":
            p0 += 1
        elif prio == "P1":
            p1 += 1
        elif prio == "P2":
            p2 += 1
        elif prio == "HOLD":
            hold += 1
        elif prio == "NEEDS_REVIEW":
            needs_review += 1

        # API
        if api.get("api_available", "").lower() == "yes":
            has_api += 1

        # Auth
        if auth.get("developer_access", "").lower() == "self_serve":
            self_serve += 1
        methods = auth.get("auth_methods", [])
        if any("oauth" in m.lower() for m in methods):
            has_oauth += 1

        # Webhooks
        if wh.get("available", "").lower() == "yes":
            has_webhooks += 1

        # MCP
        mcp_status = mcp.get("status", "").lower()
        if mcp_status == "official":
            has_mcp_official += 1
        if mcp_status in ("official", "vendor", "community"):
            has_mcp_any += 1

        # Category
        if cat not in category_scores:
            category_scores[cat] = {"count": 0, "total_score": 0}
        category_scores[cat]["count"] += 1
        category_scores[cat]["total_score"] += score

    # ── Compute averages ──
    for cat in category_scores:
        c = category_scores[cat]
        c["avg_score"] = round(c["total_score"] / c["count"], 1) if c["count"] else 0

    # ── Derive patterns from actual data ──
    patterns = []

    if total > 0:
        api_pct = round(has_api / total * 100)
        ss_pct = round(self_serve / total * 100)
        wh_pct = round(has_webhooks / total * 100)
        mcp_pct = round(has_mcp_any / total * 100)

        if api_pct > ss_pct + 15:
            patterns.append(
                f"The bottleneck is access, not API existence. "
                f"{api_pct}% of apps have APIs, but only {ss_pct}% offer self-serve developer access."
            )

        if ss_pct > 0:
            patterns.append(
                f"Self-serve developer access is a stronger build signal than API presence alone. "
                f"{ss_pct}% of the {total} apps have self-serve access."
            )

        if has_mcp_any > 0 and has_mcp_any < has_api:
            patterns.append(
                f"MCP adoption is still early. Only {mcp_pct}% of apps have any MCP server "
                f"(official or community), vs {api_pct}% with APIs."
            )

        green_unsupported = sum(
            1 for r in results
            if r.get("recommendation", {}).get("buildability") == "GREEN"
            and r.get("composio", {}).get("currently_supported") in ("no", "fuzzy_match")
        )
        if green_unsupported > 0:
            patterns.append(
                f"There are {green_unsupported} build-ready apps not yet covered by Composio – "
                f"the highest-value build queue."
            )

        if covered > 0:
            patterns.append(
                f"Composio already covers {covered} of the {total} target apps."
            )

    summary = {
        "total_researched": total,
        "green_count": green,
        "yellow_count": yellow,
        "red_count": red,
        "unknown_count": unknown,
        "covered_count": covered,
        "priority_breakdown": {
            "P0": p0, "P1": p1, "P2": p2,
            "HOLD": hold, "NEEDS_REVIEW": needs_review, "COVERED": covered,
        },
        "aggregate": {
            "has_api": has_api,
            "self_serve_access": self_serve,
            "has_oauth": has_oauth,
            "has_webhooks": has_webhooks,
            "has_mcp_official": has_mcp_official,
            "has_mcp_any": has_mcp_any,
        },
        "category_scores": category_scores,
        "patterns": patterns,
    }

    save_json("summary.json", summary)
    print(f"Summary generated: {total} apps analyzed.")
    print(f"  GREEN={green} YELLOW={yellow} RED={red} UNKNOWN={unknown} COVERED={covered}")
    for p in patterns:
        print(f"  > {p}")


if __name__ == "__main__":
    main()
