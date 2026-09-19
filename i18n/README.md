# Translations

One file per locale, named after its BCP 47 language tag: `en.json`, `zh-Hans.json`.
`index.html` fetches them at startup (see `CATALOG_DIR`) and rebuilds its `<select>`
from the `LOCALES` list in that script.

## Default language

Two constants in `index.html` control this, and they are deliberately separate:

| Constant | Value | Meaning |
| --- | --- | --- |
| `DEFAULT_LANG` | `zh-Hans` | What a visitor sees until they pick a language. |
| `BASE_LANG` | `en` | The catalog every other locale falls back to, and the one that must always load. |

There is no `Accept-Language` sniffing: the page opens in the default language for
everyone, and only a stored choice changes that. Set `DEFAULT_LANG = 'en'` to go
back to English-first.

The static markup in `index.html` carries the default locale's text, so the first
paint is already in the right language; it is replaced the moment the catalogs land.

## Adding a language

1. Copy `en.json` to `<tag>.json` and translate the values.
2. Add one entry to `LOCALES` in `index.html`:
   ```js
   { code: '<tag>', name: 'Native Name' },
   ```
   `name` is the language's own name, so it reads correctly for everyone.
3. Check it: `python3 scripts/check_i18n.py`

No markup changes are needed — the switcher is generated from `LOCALES`.

## Message format

A message is either a plain string with `{placeholder}`s:

```json
"query.noMatch": "No root key matches {q}."
```

or an object keyed by [CLDR plural category](https://cldr.unicode.org/index/cldr-spec/plural-rules),
selected with `Intl.PluralRules` for the active locale. The placeholder that
drives the choice is always `n`:

```json
"edit.count": { "one": "{n} value", "other": "{n} values" }
```

Chinese has a single form, so only `other` is needed:

```json
"edit.count": { "other": "{n} 个值" }
```

Languages with more categories (`few`, `many`, …) work the same way — just add
the keys their CLDR rules can produce.

## Rules

- **`en.json` is the base.** Any key missing from another locale falls back to
  English at runtime. Never remove a key from `en.json` without removing it
  everywhere — the checker enforces this.
- **Keep placeholders identical across locales.** `scripts/check_i18n.py` fails
  on a dropped or renamed `{placeholder}`, since it renders literally on screen.
- **Keys are namespaced by area** (`app.`, `tab.`, `picker.`, `query.`, `edit.`,
  `valid.`, `bar.`, `status.`, `msg.`, `confirm.`) so a key's home is obvious.

## Notes

- These files deliberately do **not** live under `assets/`: `scripts/build_manifest.py`
  globs every `*.json` there into the file picker.
- `index.html` keeps a small inline `BOOTSTRAP` fallback. It is used only when the
  catalogs themselves cannot be read (typically the page was opened over `file://`,
  where the browser blocks local `fetch`), because at that point there are no
  loaded messages to report the problem with.
