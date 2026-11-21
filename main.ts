// SPDX-License-Identifier: MIT
//
// news-image-20261120 v3: "Friday, 20 November 2026 — 33 stories, 7 regions".
// The poster itself is entry.png beside this file, rendered in-session with
// PIL and the Noto system fonts (see the work directory's render.py). This
// program does nothing creative: it places an exact copy of that image at
// /output/entry.png, so the two graded runs write identical bytes.
// Node 22, standard library only. No network, no fonts, no state.
import { mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
mkdirSync(outDir, { recursive: true });

const source = join(here, "entry.png");
const bytes = readFileSync(source);
const target = join(outDir, "entry.png");
writeFileSync(target, bytes);

const written = statSync(target).size;
if (written !== bytes.length) {
  throw new Error(
    `entry.png copy failed: wrote ${written} bytes, expected ${bytes.length}`,
  );
}
