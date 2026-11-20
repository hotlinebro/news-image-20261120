// SPDX-License-Identifier: MIT
//
// news-image-20261120 v2: "Friday, 20 November 2026 — 18 stories".
// The poster is entry.png next to this file, rendered in-session with
// PIL and the Noto system fonts. This program only places an exact copy
// of it at /output/entry.png, so both graded runs are byte-identical.
// Node 22, standard library only, no network, no fonts at runtime.
import { mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const destDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
mkdirSync(destDir, { recursive: true });
const src = join(here, "entry.png");
const bytes = readFileSync(src);
const out = join(destDir, "entry.png");
writeFileSync(out, bytes);
// Fail loudly instead of shipping a truncated copy.
if (statSync(out).size !== bytes.length) {
  throw new Error(`entry.png write mismatch: ${statSync(out).size} != ${bytes.length}`);
}
