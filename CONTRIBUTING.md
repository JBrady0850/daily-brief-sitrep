# Contributing

Ideas, bug reports and new library categories are welcome through the issue
forms. For code:

## Rules that keep the app working

1. Plain JavaScript in classic scripts, no build step, and it must work when
   `app/index.html` is opened straight from disk.
2. `app/js/engine.js` and `dailybrief/engine.py` are twins, and so are
   `app/js/newsletter.js` and `dailybrief/render.py`. Change both, then run the
   parity tests.
   `app/js/collect.js` and `dailybrief/collect.py` share the forecast code
   (`forecastUrl`, `weatherFrom`), also checked by the parity tests.
3. Generated files (`app/data/prompts.js`, `app/data/sample.js`,
   `prompt/category-library.md` and the library list inside the full prompt)
   come from `python -m dailybrief build-assets`; `app/data/icons.js` comes from
   `python tools/icons_source.py`. Edit the sources, not them.
4. The browser tests never touch the real network: every outside request is
   answered from recorded data in `tests/test_ui.py`. A new outside service
   needs an answer there too.
5. Icons and artwork are drawn for the project. Do not add logos, mascots or
   pictures copied from elsewhere.
6. The Python side uses the standard library only.
7. No personal data: example data uses example.com and invented names. Run
   `python -m dailybrief scan .` before every push, plus `--terms` with a
   private word list kept outside the repository.
8. No em dashes in any file.
9. Bump the version in `app/js/engine.js`, `dailybrief/engine.py` and `app/sw.js`
   together, and add a CHANGELOG entry.

## Tests

```
pip install pytest playwright
python -m playwright install chromium
python -m pytest -q
python tests/make_screenshots.py     # after a visible change
```

The parity tests need Node.js; the browser tests need Playwright and Chromium.
Without them those tests are skipped locally, and CI runs them all.
