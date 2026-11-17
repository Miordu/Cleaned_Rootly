# Portfolio site

A static, single-page portfolio for Quinntin Saint Laurent. No build step and
no dependencies: three files.

| File | What it is |
| --- | --- |
| `index.html` | All of the content |
| `styles.css` | Layout, type, light and dark themes |
| `script.js` | Theme toggle, credits filter, scroll effects |

## Preview it

```bash
python3 -m http.server 8000 --directory portfolio
```

Then open http://localhost:8000.

## Publish it

Any static host works. Upload this folder to Netlify, Vercel or Cloudflare
Pages, or move the three files into their own repository and turn on GitHub
Pages.

## Edit it

Every section in `index.html` is marked with a comment (`<!-- Experience -->`,
`<!-- Credits -->` and so on). To add a screen credit, copy a `<tr>` row in the
credits table and set `data-kind` to `tv` or `film` so the filter picks it up.
