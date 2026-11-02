# Contributing

Contributions should improve the public coffee-search skill or its package documentation. Keep changes focused, source claims in the live public API or repository behavior, and do not add private Roazon code, credentials, customer data, or third-party catalog images and records.

Before opening a pull request, run:

```sh
python3 scripts/validate.py
```

For changes to the documented API, verify the anonymous endpoint and update `openapi.json` and the examples together. Do not add dependencies for validation without discussion. See [SECURITY.md](SECURITY.md) for private vulnerability reports.
