# SVGrepo.com Research

## Overview
SVGrepo hosts hundreds of thousands of free vector icons. It offers a public REST API that can be queried to locate and download SVG files for reuse.

## Base Endpoint
```
https://api.svgrepo.com/v2/
```

### Search
```
GET /search?q=<term>&page=<n>&per_page=<limit>
```
Returns JSON containing a `data` array. Each item provides at least an `id`, `name`, license information and a direct `svg` download URL.

### Icon Details
```
GET /icons/<id>
```
Fetches additional metadata for a single icon.

### Download
```
GET /download/<id>
```
Responds with the raw SVG bytes. Use `curl -L` to follow redirects.

Most endpoints work without an API key but free usage is rate limited. Creating an account yields an API token that raises the request limit.

## Example Search
```bash
curl -s "https://api.svgrepo.com/v2/search?q=arrow&per_page=3" | jq
```
Sample response:
```json
{
  "data": [
    {
      "id": 3438,
      "name": "arrow",
      "svg": "https://www.svgrepo.com/download/3438/arrow.svg",
      "permalink": "https://www.svgrepo.com/svg/3438/arrow",
      "license": "CC0"
    }
  ],
  "page": 1,
  "total": 3091
}
```

## Integration Plan
1. Determine query from the deepest non-empty category name.
2. Call the search endpoint and gather candidates.
3. Select the simplest icon; fetch its `svg` URL.
4. Restyle it to house style and record the original `permalink` in `manifest.csv`.

## Comparison to svgapi.com
- `svgapi.com` requires an API key embedded in the URL path; SVGrepo's API is open with optional token.
- SVGrepo provides license metadata and a larger free icon library.
- Both services return direct SVG links suitable for deterministic restyling.

## Access Notes
Attempts to reach svgrepo.com from this environment result in `403 Forbidden`, including through the recommended `r.jina.ai` proxy. A fresh test after svgapi integration (see `connection-prohibited.md`) still returns `403`, so automation remains blocked until alternate access is arranged.

