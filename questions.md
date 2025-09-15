# Questions

1. If the repository's SVG outputs approach GitHub's 100 MiB file limit, should we integrate an external storage solution (e.g., Google Drive), and what interface is required?
2. Iconify API requests can hang or fail during icon downloads. Should we switch to another public source or introduce caching/retry logic to ensure reliable access?
3. Direct access to svgrepo.com (and the `r.jina.ai` proxy) returns `403 Forbidden`. Is there an approved method or credentials to reach SVGrepo from CI?
