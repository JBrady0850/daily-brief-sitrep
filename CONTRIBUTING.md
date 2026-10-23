# Contributing

Ideas, bug reports and new library categories are welcome through the issue
forms. For code:

## Rules that keep the app working

1. Plain JavaScript in classic scripts, no build step, and it must work when
   `app/index.html` is opened straight from disk.
2. `app/js/engine.js` and `dailybrief/engine.py` are twins, and so are
   `app/js/newsletter.js` and `dailybrief/render.py`. Change both, then run the
   parity tests.
3. Generated files (`app/data/prompts.js`, `app/data/sample.js`,
   `prompt/category-library.md` and the library list inside the full prompt)
   come from `python -m dailybrief build-assets`. Edit the sources, not them.
4. The Python side uses the standard library only.
5. No personal data: example data uses example.com and invented names. Run
   `python -m dailybrief scan .` before every push, plus `--terms` with a
   private word list kept outside the repository.
6. No em dashes in any file.
7. Bump the version in `app/js/engine.js`, `dailybrief/engine.py` and `app/sw.js`
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
