# SVGAPI.com Research

## Overview
SVGAPI provides a hosted icon search API. Queries return JSON metadata and direct links to downloadable SVGs. API keys are passed as part of the URL path.

## Base Endpoint
```
https://api.svgapi.com/v1/{API_KEY}/list/?search=<term>&start=<offset>&limit=<n>
```
- **API_KEY** – required identifier; example from public site: `Ty5WcDa63E`.
- **search** – query string.
- **start** – optional offset for pagination.
- **limit** – optional number of results per page (defaults to 10).

## Example Search
```bash
curl -Ls "https://api.svgapi.com/v1/Ty5WcDa63E/list/?search=arrow" | jq
```
Sample response:
```json
{
  "term": "arrow",
  "count": 3091,
  "limit": 10,
  "start": 0,
  "response_time": 0.7855498790741,
  "icons": [
    {"id": "33329", "slug": "arrow", "title": "Arrow", "url": "https://cdn.svgapi.com/vector/33329/arrow.svg"},
    {"id": "33531", "slug": "arrow", "title": "Arrow", "url": "https://cdn.svgapi.com/vector/33531/arrow.svg"},
    {"id": "35403", "slug": "arrow", "title": "Arrow", "url": "https://cdn.svgapi.com/vector/35403/arrow.svg"}
    /* ... */
  ]
}
```
The response also includes a `next` URL when additional pages are available.

## Downloading Icons
The `url` field points directly to the raw SVG.
```bash
curl -Ls https://cdn.svgapi.com/vector/33329/arrow.svg -o arrow.svg
```

## Other Observations
- The site bundles JavaScript assets that reveal the API endpoints, e.g. `https://svgapi.com/component---src-pages-index-js-*.js`.
- There is a panel for key management at `https://panel.svgapi.com`.
- An unkeyed endpoint hint `v1/search?term=` was found in the scripts but returns `404` when called directly.

## Integration Ideas
Using SVGAPI can replace manual scraping from SVGrepo:
1. Derive the deepest category term.
2. Call the `list` endpoint with that term.
3. Select a suitable candidate from the JSON (e.g., based on title or slug).
4. Fetch the SVG via the `url` field and restyle it to house guidelines.
5. Record `source_icon` with the SVGAPI URL in `manifest.csv`.

This API streamlines search and collection by providing structured metadata and direct SVG downloads, eliminating HTML parsing.

## Integration Status
- `scripts/generate_icons.py` now uses the `list` endpoint with deterministic
  result selection. The script accepts an explicit `--api-key` argument (or
  `SVGAPI_API_KEY` environment variable) and records diagnostics to a
  `generation.log` file in the output directory. A successful dry run against
  `categories_25.csv` produced 25 classic-style icons in `output/test4`.

