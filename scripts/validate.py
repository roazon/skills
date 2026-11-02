#!/usr/bin/env python3
"""Validate the standalone skill package without third-party dependencies."""

from json import loads
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_FILES = (
    "README.md",
    "AGENTS.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "llms.txt",
    "openapi.json",
    ".agents/skills/roazon-coffee/SKILL.md",
)
FORBIDDEN = (
    "/Users/",
    "~/.factory/",
    "oleg-koval/roazon",
    "wrangler",
    "AGTERM_",
)
ENVELOPE_FIELDS = {"schema", "readings_match", "roasters", "coffees", "applied_facets", "relaxations"}
ROASTER_FIELDS = {"id", "name", "shop_url", "logo", "city", "beans", "sponsored"}
COFFEE_FIELDS = {
    "id", "roaster_id", "roaster_name", "title", "url", "image",
    "price_cents", "origins", "variety", "process", "varietals", "roast",
    "method", "decaf", "subscription", "wheel_groups", "price_band", "city",
    "sponsored",
}


def read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def main():
    missing = tuple(path for path in REQUIRED_FILES if not (ROOT / path).is_file())
    if missing:
        raise SystemExit(f"missing required files: {', '.join(missing)}")

    skill = read(".agents/skills/roazon-coffee/SKILL.md")
    lines = skill.splitlines()
    if lines[0] != "---" or lines[3] != "---":
        raise SystemExit("skill frontmatter must have name and description")
    if lines[1] != "name: roazon-coffee" or not lines[2].startswith("description: "):
        raise SystemExit("skill frontmatter name or description is invalid")

    api = loads(read("openapi.json"))
    if api.get("openapi") != "3.1.0":
        raise SystemExit("OpenAPI version must be 3.1.0")
    if set(api.get("paths", {})) != {"/api/v1/search"}:
        raise SystemExit("OpenAPI must describe only the public search path")
    path_item = api["paths"]["/api/v1/search"]
    if set(path_item) != {"get"}:
        raise SystemExit("OpenAPI must document only GET")
    operation = path_item["get"]
    parameters = operation.get("parameters", [])
    if (len(parameters) != 1 or parameters[0].get("name") != "q"
            or parameters[0].get("in") != "query" or parameters[0].get("required") is not False):
        raise SystemExit("search must document only the q query parameter")
    query_note = parameters[0].get("description", "").lower()
    if "optional" not in query_note or "omitted or blank" not in query_note or "http 200" not in query_note:
        raise SystemExit("q must document optional and blank-query behavior")
    response = api["components"]["schemas"]["SearchResponse"]
    if set(response["properties"]) != ENVELOPE_FIELDS:
        raise SystemExit("response fields differ from the observed public envelope")
    if response["properties"]["schema"].get("const") != "roazon/api@1":
        raise SystemExit("response schema version does not match the live API")
    contract_note = api["info"].get("description", "").lower()
    match_note = response["properties"]["readings_match"].get("description", "").lower()
    if ("partial" not in contract_note or "organic" not in match_note
            or "coffee and roaster matches" not in match_note or "before output caps" not in match_note
            or "24 coffees" not in match_note or "12 roasters" not in match_note
            or "sponsored placements are excluded" not in match_note
            or "returned coffees and roasters arrays" not in match_note):
        raise SystemExit("OpenAPI must mark the sampled contract as partial and define readings_match accurately")
    schemas = api["components"]["schemas"]
    if set(schemas["Coffee"]["properties"]) != COFFEE_FIELDS:
        raise SystemExit("coffee fields differ from the observed public response")
    if set(schemas["Roaster"]["properties"]) != ROASTER_FIELDS:
        raise SystemExit("roaster fields differ from the observed public response")
    for item_name in ("Coffee", "Roaster"):
        sponsored_note = schemas[item_name]["properties"]["sponsored"].get("description", "").lower()
        if "sponsored placement" not in sponsored_note or "disclose" not in sponsored_note or "organic ranking" not in sponsored_note:
            raise SystemExit(f"{item_name} sponsored flag must be explained")
    if api["servers"] != [{"url": "https://roazon.nl"}]:
        raise SystemExit("API server must remain the fixed HTTPS Roazon endpoint")

    docs = "\n".join(read(path) for path in REQUIRED_FILES if path != "openapi.json")
    if any(term in docs for term in FORBIDDEN):
        raise SystemExit("package contains a prohibited private path or infrastructure reference")
    if "npx skills add roazon/skills --skill roazon-coffee" not in docs:
        raise SystemExit("standard install command is missing")
    if "--agent droid" not in docs or ".agents/skills/roazon-coffee/" not in docs:
        raise SystemExit("Droid install or canonical project path is missing")
    if "crawl timestamp" not in docs.lower() or "never claim current stock" not in skill.lower():
        raise SystemExit("freshness and stock caveats are missing")
    skill_note = skill.lower()
    if ("organic coffee and roaster matches" not in skill_note or "24 coffees" not in skill_note
            or "12 roasters" not in skill_note or "sponsored: true" not in skill_note
            or "never present it as organically ranked" not in skill_note):
        raise SystemExit("skill must explain match counts, output caps, and sponsored disclosure")
    print("Package validation passed: files, frontmatter, OpenAPI scope, install guidance, and safety/freshness limits.")


if __name__ == "__main__":
    main()
