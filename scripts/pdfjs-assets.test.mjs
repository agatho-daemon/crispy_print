import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { checkPdfJs, syncPdfJs } from './pdfjs-assets.mjs';

function fixture(t) {
  const root = fs.mkdtempSync(join(tmpdir(), 'crispy-pdfjs-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const js = join(root, 'crispy_print/public/js');
  const source = join(js, 'node_modules/pdfjs-dist');
  const vendor = join(root, 'crispy_print/public/vendor/pdfjs');
  fs.mkdirSync(join(source, 'legacy/build'), { recursive: true });
  fs.mkdirSync(vendor, { recursive: true });
  function install(version = '6.1.200') {
    fs.writeFileSync(join(js, 'package.json'), JSON.stringify({ dependencies: { 'pdfjs-dist': version } }));
    fs.writeFileSync(join(source, 'package.json'), JSON.stringify({ version }));
    fs.writeFileSync(join(source, 'legacy/build/pdf.min.mjs'), `/* pdfjsVersion = ${version} */ module`);
    fs.writeFileSync(join(source, 'legacy/build/pdf.worker.min.mjs'), `/* pdfjsVersion = ${version} */ worker`);
    fs.writeFileSync(join(source, 'LICENSE'), 'Upstream license\n');
  }
  install();
  return { root, js, source, vendor, install };
}

function snapshot(directory) {
  return fs.readdirSync(directory).sort().map((name) => [name, fs.readFileSync(join(directory, name)).toString('base64')]);
}

const readonly = { ...fs };
for (const name of ['writeFileSync', 'mkdirSync', 'mkdtempSync', 'renameSync', 'unlinkSync', 'rmSync']) {
  readonly[name] = () => { throw new Error(`Unexpected write: ${name}`); };
}

test('copies byte-identical legacy module, worker, and license; repeated sync does no writes', (t) => {
  const { root, source, vendor } = fixture(t);
  assert.equal(syncPdfJs(root).changed.length, 3);
  for (const [src, dest] of [['legacy/build/pdf.min.mjs', 'pdf-6.1.200.min.js'], ['legacy/build/pdf.worker.min.mjs', 'pdf.worker-6.1.200.min.js'], ['LICENSE', 'LICENSE']]) {
    assert.deepEqual(fs.readFileSync(join(vendor, dest)), fs.readFileSync(join(source, src)));
  }
  assert.equal(checkPdfJs(root, readonly).version, '6.1.200');
  assert.deepEqual(syncPdfJs(root, readonly).changed, []);
});

for (const pin of ['^6.1.200', '~6.1.200', 'latest', '6.1', '6.2.0-beta.1', '6.1.200+build', '06.1.200', '../outside']) {
  test(`rejects invalid pin before writing: ${pin}`, (t) => {
    const { root, js, vendor } = fixture(t);
    fs.writeFileSync(join(js, 'package.json'), JSON.stringify({ dependencies: { 'pdfjs-dist': pin } }));
    assert.throws(() => syncPdfJs(root, readonly), /exact stable three-part/);
    assert.throws(() => checkPdfJs(root, readonly), /exact stable three-part/);
    assert.deepEqual(snapshot(vendor), []);
  });
}

for (const broken of ['installed-version', 'missing-module', 'missing-worker', 'missing-license', 'header']) {
  test(`validates all source files before writing: ${broken}`, (t) => {
    const { root, source, vendor } = fixture(t);
    if (broken === 'installed-version') fs.writeFileSync(join(source, 'package.json'), '{"version":"6.1.201"}');
    if (broken === 'missing-module') fs.unlinkSync(join(source, 'legacy/build/pdf.min.mjs'));
    if (broken === 'missing-worker') fs.unlinkSync(join(source, 'legacy/build/pdf.worker.min.mjs'));
    if (broken === 'missing-license') fs.unlinkSync(join(source, 'LICENSE'));
    if (broken === 'header') fs.writeFileSync(join(source, 'legacy/build/pdf.worker.min.mjs'), '/* pdfjsVersion = 6.1.201 */');
    assert.throws(() => syncPdfJs(root, readonly));
    assert.deepEqual(snapshot(vendor), []);
  });
}

for (const broken of ['module', 'worker', 'license', 'missing-module', 'missing-worker', 'missing-license', 'stale-module', 'stale-worker']) {
  test(`read-only verifier detects drift: ${broken}`, (t) => {
    const { root, vendor } = fixture(t);
    syncPdfJs(root);
    if (broken === 'module') fs.appendFileSync(join(vendor, 'pdf-6.1.200.min.js'), 'changed');
    if (broken === 'worker') fs.appendFileSync(join(vendor, 'pdf.worker-6.1.200.min.js'), 'changed');
    if (broken === 'license') fs.appendFileSync(join(vendor, 'LICENSE'), 'changed');
    if (broken === 'missing-module') fs.unlinkSync(join(vendor, 'pdf-6.1.200.min.js'));
    if (broken === 'missing-worker') fs.unlinkSync(join(vendor, 'pdf.worker-6.1.200.min.js'));
    if (broken === 'missing-license') fs.unlinkSync(join(vendor, 'LICENSE'));
    if (broken === 'stale-module') fs.writeFileSync(join(vendor, 'pdf-6.0.0.min.js'), 'old');
    if (broken === 'stale-worker') fs.writeFileSync(join(vendor, 'pdf.worker-6.0.0.min.js'), 'old');
    const before = snapshot(vendor);
    assert.throws(() => checkPdfJs(root, readonly), /mismatch|Missing|Stale/);
    assert.deepEqual(snapshot(vendor), before);
  });
}

test('upgrade removes only old managed versions and preserves unrelated files', (t) => {
  const { root, vendor, install } = fixture(t);
  syncPdfJs(root);
  fs.writeFileSync(join(vendor, 'operator-notes.txt'), 'unrelated uncommitted work');
  fs.writeFileSync(join(vendor, 'pdf-custom.min.js'), 'not owned');
  install('6.1.201');
  syncPdfJs(root);
  assert.deepEqual(fs.readdirSync(vendor).sort(), ['LICENSE', 'operator-notes.txt', 'pdf-6.1.201.min.js', 'pdf-custom.min.js', 'pdf.worker-6.1.201.min.js'].sort());
  assert.equal(fs.readFileSync(join(vendor, 'operator-notes.txt'), 'utf8'), 'unrelated uncommitted work');
  checkPdfJs(root);
});

test('partial replacement failure reports changed files; rerunning repairs the complete set', (t) => {
  const { root, vendor, install } = fixture(t);
  syncPdfJs(root);
  install('6.1.201');
  let replacements = 0;
  const failSecond = { ...fs, renameSync(from, to) {
    if (++replacements === 2) throw new Error('simulated disk failure');
    return fs.renameSync(from, to);
  } };
  assert.throws(() => syncPdfJs(root, failSecond), (error) => {
    assert.match(error.message, /Replaced pdf-6.1.201.min.js/);
    assert.doesNotMatch(error.message, /Replaced pdf.worker-6.1.201.min.js/);
    assert.match(error.message, /Rerun yarn sync:pdfjs/);
    return true;
  });
  assert.ok(fs.existsSync(join(vendor, 'pdf-6.1.200.min.js')));
  assert.ok(!fs.readdirSync(vendor).some((name) => name.startsWith('.pdfjs-sync-')));
  assert.throws(() => checkPdfJs(root));
  syncPdfJs(root);
  checkPdfJs(root, readonly);
  assert.deepEqual(syncPdfJs(root, readonly).changed, []);
});

test('staging failure leaves existing destinations unchanged', (t) => {
  const { root, vendor, install } = fixture(t);
  syncPdfJs(root);
  install('6.1.201');
  const before = snapshot(vendor);
  const failStage = { ...fs, writeFileSync() { throw new Error('simulated staging failure'); } };
  assert.throws(() => syncPdfJs(root, failStage), /Managed files changed:\n\(none\)/);
  assert.deepEqual(snapshot(vendor), before);
});

test('rejects managed symlinks without changing their targets', (t) => {
  const { root, vendor } = fixture(t);
  const external = join(root, 'outside.js');
  fs.writeFileSync(external, 'untouched');
  fs.symlinkSync(external, join(vendor, 'pdf-6.1.200.min.js'));
  assert.throws(() => syncPdfJs(root), /Unsafe managed/);
  assert.throws(() => checkPdfJs(root), /Unsafe managed/);
  assert.equal(fs.readFileSync(external, 'utf8'), 'untouched');
});


test('CI command exits nonzero for a stale set, does not repair it, and passes after sync', (t) => {
  const { root, vendor } = fixture(t);
  const script = join(root, 'scripts/pdfjs-assets.mjs');
  fs.mkdirSync(join(root, 'scripts'));
  fs.copyFileSync(fileURLToPath(new URL('./pdfjs-assets.mjs', import.meta.url)), script);
  const stale = spawnSync(process.execPath, [script, 'check'], { encoding: 'utf8' });
  assert.equal(stale.status, 1);
  assert.match(stale.stderr, /Missing managed file/);
  assert.deepEqual(snapshot(vendor), []);
  const synced = spawnSync(process.execPath, [script, 'sync'], { encoding: 'utf8' });
  assert.equal(synced.status, 0, synced.stderr);
  const checked = spawnSync(process.execPath, [script, 'check'], { encoding: 'utf8' });
  assert.equal(checked.status, 0, checked.stderr);
  assert.match(checked.stdout, /verified/);
});
