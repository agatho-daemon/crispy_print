#!/usr/bin/env node
// Developer tooling only. Normal Bench builds serve the committed assets.
import * as fs from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const VERSION = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/;
const MANAGED_ASSET = /^pdf(?:\.worker)?-\d+\.\d+\.\d+\.min\.js$/;
const isManaged = (name) => name === 'LICENSE' || MANAGED_ASSET.test(name);

function expectedAssets(root, io) {
  const js = join(root, 'crispy_print/public/js');
  const version = JSON.parse(io.readFileSync(join(js, 'package.json'), 'utf8')).dependencies?.['pdfjs-dist'];
  if (typeof version !== 'string' || !VERSION.test(version)) {
    throw new Error('pdfjs-dist must have an exact stable three-part version pin (for example, 6.1.200).');
  }
  const source = join(js, 'node_modules/pdfjs-dist');
  const installed = JSON.parse(io.readFileSync(join(source, 'package.json'), 'utf8')).version;
  if (installed !== version) throw new Error(`Installed PDF.js ${installed} does not match pin ${version}. Install the locked dependencies first.`);
  const assets = new Map();
  for (const [from, to] of [
    ['legacy/build/pdf.min.mjs', `pdf-${version}.min.js`],
    ['legacy/build/pdf.worker.min.mjs', `pdf.worker-${version}.min.js`],
    ['LICENSE', 'LICENSE'],
  ]) {
    const bytes = io.readFileSync(join(source, from));
    if (!bytes.length) throw new Error(`Empty PDF.js source file: ${from}`);
    if (from !== 'LICENSE' && bytes.toString().match(/pdfjsVersion\s*=\s*([\d.]+)/)?.[1] !== version) {
      throw new Error(`PDF.js version header does not match ${version}: ${from}`);
    }
    assets.set(to, bytes);
  }
  return { version, assets };
}

function destination(root, io) {
  // Reject symlinks in the destination path and managed entries. Never follow
  // a managed symlink when comparing, replacing, or removing files.
  let directory = resolve(root);
  for (const part of ['crispy_print', 'public', 'vendor', 'pdfjs']) {
    directory = join(directory, part);
    if (io.existsSync(directory)) {
      const stat = io.lstatSync(directory);
      if (!stat.isDirectory() || stat.isSymbolicLink()) throw new Error(`Unsafe PDF.js destination: ${directory}`);
    }
  }
  const names = io.existsSync(directory) ? io.readdirSync(directory) : [];
  for (const name of names.filter(isManaged)) {
    const stat = io.lstatSync(join(directory, name));
    if (!stat.isFile() || stat.isSymbolicLink()) throw new Error(`Unsafe managed PDF.js entry: ${name}`);
  }
  return { directory, names };
}

export function checkPdfJs(root = ROOT, io = fs) {
  const { version, assets } = expectedAssets(root, io);
  const { directory, names } = destination(root, io);
  const errors = [];
  for (const [name, bytes] of assets) {
    if (!names.includes(name)) errors.push(`Missing managed file: ${name}`);
    else if (!io.readFileSync(join(directory, name)).equals(bytes)) errors.push(`Content mismatch: ${name}`);
  }
  for (const name of names.filter(isManaged)) {
    if (!assets.has(name)) errors.push(`Stale managed file: ${name}`);
  }
  if (errors.length) throw new Error(`${errors.join('\n')}\nRun yarn sync:pdfjs, review the diff, and commit the synchronized files.`);
  return { version, changed: [] };
}

export function syncPdfJs(root = ROOT, io = fs) {
  // Read and validate every input and destination before making any changes.
  const { version, assets } = expectedAssets(root, io);
  const { directory, names } = destination(root, io);
  const replacements = [...assets].filter(([name, bytes]) => !names.includes(name) || !io.readFileSync(join(directory, name)).equals(bytes));
  const stale = names.filter((name) => isManaged(name) && !assets.has(name));
  const changed = [];
  if (!replacements.length && !stale.length) return { version, changed };
  let stage;
  try {
    io.mkdirSync(directory, { recursive: true });
    stage = io.mkdtempSync(join(directory, '.pdfjs-sync-'));
    for (const [name, bytes] of replacements) {
      io.writeFileSync(join(stage, name), bytes);
      if (!io.readFileSync(join(stage, name)).equals(bytes)) throw new Error(`Staged file verification failed: ${name}`);
    }
    for (const [name] of replacements) {
      io.renameSync(join(stage, name), join(directory, name));
      changed.push(`Replaced ${name}`);
    }
    // Only remove old versions after the complete replacement set is staged
    // and all replacements succeeded. Unrelated files are never removed.
    for (const name of stale) {
      io.unlinkSync(join(directory, name));
      changed.push(`Removed ${name}`);
    }
  } catch (error) {
    throw new Error(`PDF.js sync failed: ${error.message}\nManaged files changed:\n${changed.join('\n') || '(none)'}\nRerun yarn sync:pdfjs to repair the managed set. Review git diff before any targeted recovery; do not run a blanket git restore.`, { cause: error });
  } finally {
    if (stage) io.rmSync(stage, { recursive: true, force: true });
  }
  return { version, changed };
}

if (process.argv[1] && fs.realpathSync(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const mode = process.argv[2];
    if (!['check', 'sync'].includes(mode) || process.argv.length !== 3) throw new Error('Usage: node scripts/pdfjs-assets.mjs check|sync');
    const result = mode === 'check' ? checkPdfJs() : syncPdfJs();
    console.log(`PDF.js ${result.version}: ${mode === 'check' ? 'verified' : result.changed.length ? 'synchronized' : 'already synchronized'}.`);
    for (const change of result.changed) console.log(change);
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
