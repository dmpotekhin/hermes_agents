# Task 10 — Kids Learn frontend components (verbatim-react-components brief)

Brief that said "follow code verbatim" for 7 React components in `frontend/src/components/`
(Header, ProgressBar, ChoiceTask, NumberTask, TextTask, CodeTask, ResultPanel). All
component files matched the brief byte-for-byte. The bug was NOT in the component code —
it was a **missing dependency in `package.json`** that the brief's components silently depended on.

## The bug: `codemirror` meta-package vs `@codemirror/*` sub-packages

`CodeTask.jsx` imports:

```jsx
import { EditorView, basicSetup } from 'codemirror';
import { python } from '@codemirror/lang-python';
import { oneDark } from '@codemirror/theme-one-dark';
import { EditorState } from '@codemirror/state';
```

At task time `package.json` only declared the individual packages
(`@codemirror/lang-python`, `@codemirror/state`, `@codemirror/theme-one-dark`,
`@codemirror/view`). The **`codemirror` meta-package was absent** from node_modules.

Why it matters: **`basicSetup` lives ONLY in the `codemirror` meta-package**, not in
`@codemirror/view` (which exports `EditorView`, `keymap`, `basicSetup` is NOT one of its
exports). So `import { basicSetup } from '@codemirror/view'` would fail; the import in the
brief is correct AS WRITTEN but the dependency config is incomplete.

- Check with `ls node_modules/codemirror/package.json` — absent ⇒ missing.
- Fix: `npm install codemirror@^6` (adds `^6.0.2` to dependencies + lockfile).
- This is additive and consistent with the brief's intent (the brief code references it), so it
  is not a deviation from "verbatim" — the component files stay verbatim; only deps are fixed.

## Why the build hid it (until the pages exist)

`npm run build` fails EARLY on the two missing page modules (`./pages/HomePage`,
`./pages/LessonPage`) imported by `App.jsx` — those belong to a later task. So the missing
`codemirror` dep was a *latent second failure* that only surfaces once pages exist. In
incremental SDD, don't stop at "build fails on expected pending imports" — also grep the
new files' deps for anything not in `package.json`. The page errors string
(`Help: 'src/App.jsx' is imported by ... Module not found.`) is the ONLY error; nothing
references the component files, but that doesn't prove their deps resolve.

Pattern: **verify every import in verbatim component code maps to an INSTALLED dependency,
not just to a module that exists in node_modules somewhere.** Check the exact package name
in `package.json`, because the brief's top-level meta-package can differ from the sub-packages.

## Ad-hoc verification (no suite, build red on pending pages)

Focused, authoritative per-component check = bundle each `.jsx` with the project's own bundler
(rolldown, what Vite 8 uses) with externals:

```js
const req = createRequire(projectRoot + '/noop.js');   // anchor resolution to project
const { build } = req('rolldown');
await build({ input: file, external: [/^react/, /^codemirror/, /^@codemirror/, /^\.\.\/api/, /^react-dom/], write: false });
```

All 7 `OK`. See `execute-code-verification` for the `createRequire` + temp-`.cjs` mechanics.
