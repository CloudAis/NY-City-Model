/** Capture the existing runtime through its public UI and attributed PNG exporter. */
import { chromium } from 'playwright-core';
import { readFile, writeFile, mkdir, stat, rm } from 'node:fs/promises';
import { resolve, join, relative } from 'node:path';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { setTimeout as delay } from 'node:timers/promises';
import os from 'node:os';
import assert from 'node:assert/strict';

const root = resolve(process.env.NYC_CAPTURE_ROOT ?? '/tmp/nyc-final-release-20261028');
const origin = process.env.NYC_CAPTURE_ORIGIN ?? 'http://127.0.0.1:8080';
assert.equal(new URL(origin).hostname, '127.0.0.1', 'Only the local published runtime is captured');
const output = resolve(process.env.NYC_CAPTURE_OUTPUT ?? 'reports/screenshots/2026-10-29');
const limit = Number(process.env.NYC_CAPTURE_LIMIT ?? 20);
assert.ok(Number.isInteger(limit) && limit >= 1 && limit <= 20);
const route = JSON.parse(await readFile('config/screenshot-route.json', 'utf8'));
const manifest = JSON.parse(await readFile(join(root, 'app/datasets/environment/manifest.json'), 'utf8'));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const locks = ['delivery-manifest.json', 'app/index.html', 'app/inspection.html', 'app/datasets/environment/manifest.json', 'app/datasets/buildings-city/manifest.json'];
for (const borough of ['manhattan', 'brooklyn', 'queens', 'bronx', 'staten-island']) locks.push(`app/datasets/buildings-city/${borough}/strict.json`);
const locked = [];
for (const name of locks) locked.push({ path: name, sha256: sha(await readFile(join(root, name))) });
await mkdir(output, { recursive: true });
try { await stat(join(output, 'manifest.json')); throw Error('Existing capture manifest must not be overwritten'); }
catch (e) { if (e.code !== 'ENOENT') throw e; }
const started = new Date().toISOString();
const report = {
  schema: 1, started_at_utc: started, user_timezone: 'Asia/Taipei',
  source_commit: execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(),
  runtime_root: root, origin, entry: '/index.html', viewport: route.viewport,
  quality: route.quality, automatic_quality: false, screenshot_method: 'Existing #screenshot UI exports its actual WebGL canvas and source credit strip; no image synthesis or geometry changes',
  scope: route.scope, city_body_evidence: 'source outlines only', independently_verified_building_dimensions: false,
  world_ground_registered: false, target_count: limit,
  environment: { system: os.type(), release: os.release(), arch: os.arch(), cpu: os.cpus()[0]?.model, logical_cpus: os.cpus().length, node: process.version, hardware_gpu_tested: false, headless: true },
  runtime_locks: locked, views: [], errors: [], console_errors: [], failed_requests: [], responses: [], blocked_external_requests: [],
};
let browser, page;
const snap = () => page.evaluate(() => window.__NYC_INSPECTION__.snapshot());
async function settled(area) {
  await page.waitForFunction(({ preset, borough }) => {
    const s = window.__NYC_INSPECTION__?.snapshot();
    return s?.preset === preset && !s.flying && !s.runtime.contextLost && !s.runtime.renderFailed &&
      s.layers.buildings && s.layerStates.some(l => l.key === `city:${borough}` && l.shown && l.loaded > 0) &&
      s.layerStates.some(l => l.key === 'roads' && l.shown && l.loaded > 0);
  }, area, { timeout: 120000 });
  let stable = 0;
  const deadline = Date.now() + 90000;
  while (Date.now() < deadline) {
    const s = await snap();
    assert.deepEqual(s.errors, []);
    assert.deepEqual(s.tileFailures, []);
    const busy = s.layerStates.some(l => ['loading', 'queued'].includes(l.state) || (l.shown && (l.pending > 0 || l.processing > 0)));
    if (!s.flying && !busy && s.runtime.queue.active === 0 && s.runtime.queue.pending === 0) stable++; else stable = 0;
    if (stable >= 4) return s;
    await delay(500);
  }
  throw Error(`Actual visible layers did not settle at ${area.preset}`);
}

try {
  browser = await chromium.launch({ executablePath: '/usr/bin/chromium', headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  report.environment.browser = await browser.version();
  report.environment.launch_args = ['--no-sandbox', '--disable-dev-shm-usage', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'];
  const context = await browser.newContext({ viewport: { width: route.viewport.width, height: route.viewport.height }, deviceScaleFactor: 1, acceptDownloads: true, serviceWorkers: 'block' });
  await context.route('**/*', r => {
    const u = new URL(r.request().url());
    if (u.origin === origin || ['data:', 'blob:'].includes(u.protocol)) return r.continue();
    report.blocked_external_requests.push(r.request().url());
    return r.abort();
  });
  page = await context.newPage();
  page.on('pageerror', e => report.errors.push(e.stack ?? e.message));
  page.on('console', m => { if (m.type() === 'error') report.console_errors.push(m.text()); });
  page.on('requestfailed', r => report.failed_requests.push({ url: r.url(), reason: r.failure()?.errorText }));
  page.on('response', r => report.responses.push({ url: r.url(), status: r.status() }));
  const cdp = await context.newCDPSession(page);
  await cdp.send('Network.enable');
  await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
  report.fresh_browser_context = true;
  report.http_cache_disabled = true;
  report.external_network_blocked = true;

  await page.goto(origin + '/index.html');
  await page.waitForFunction(() => window.__NYC_RELEASE__?.snapshot().ready);
  report.opened_entry = await page.evaluate(() => ({ title: document.title, state: window.__NYC_RELEASE__.snapshot() }));
  assert.match(report.opened_entry.title, /部分完成/);
  await page.goto(origin + '/inspection.html?diagnostics=1');
  await page.waitForFunction(() => window.__NYC_INSPECTION__?.snapshot().preset);
  await page.locator('#quality').selectOption('high');
  assert.equal(await page.locator('#auto-quality').isChecked(), false);
  report.environment.webgl = await page.locator('#globe canvas').evaluate(canvas => {
    const gl = canvas.getContext('webgl2'), ext = gl.getExtension('WEBGL_debug_renderer_info');
    return { version: gl.getParameter(gl.VERSION), renderer: ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER), vendor: ext ? gl.getParameter(ext.UNMASKED_VENDOR_WEBGL) : gl.getParameter(gl.VENDOR), gpu_memory_measured_bytes: null };
  });

  outer: for (const area of route.areas) {
    const preset = manifest.observations.find(p => p.id === area.preset);
    assert.ok(preset); assert.equal(preset.borough, area.borough);
    await page.locator('#preset').selectOption(area.preset);
    for (const mode of route.modes) {
      if (report.views.length >= limit) break outer;
      await page.locator('#mode').selectOption(mode);
      const state = await settled(area);
      assert.equal(state.mode, mode);
      assert.equal(state.quality, 'high');
      assert.equal(state.worldGroundRegistered, false);
      if (mode === 'top') assert.ok(state.pitch < -1.55);
      const n = report.views.length + 1;
      const filename = `${String(n).padStart(2, '0')}-${area.borough}-${area.preset}-${mode === 'orbit' ? 'oblique' : 'top'}.png`;
      const downloadPromise = page.waitForEvent('download', { timeout: 30000 });
      await page.locator('#screenshot').click();
      const download = await downloadPromise;
      const path = join(output, filename);
      await download.saveAs(path);
      assert.equal(await download.failure(), null);
      const image = await readFile(path);
      assert.equal(image.subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
      const width = image.readUInt32BE(16), height = image.readUInt32BE(20);
      assert.ok(width >= 1200 && height >= 900);
      const after = await snap();
      assert.match(after.lastExportCredit, /NYC OTI/);
      assert.deepEqual(after.errors, []);
      const view = {
        sequence: n, file: filename, label: area.label, borough: area.borough, preset: area.preset,
        view: mode === 'orbit' ? '斜视' : '俯视', captured_at_utc: new Date().toISOString(),
        png_bytes: image.length, sha256: sha(image), dimensions: { width, height },
        target_longitude_degrees: preset.lon, target_latitude_degrees: preset.lat,
        camera: { ecef_metres: state.cameraWorld, height_above_display_ellipsoid_m: state.cameraHeight, heading_radians: state.heading, pitch_radians: state.pitch },
        attribution: after.lastExportCredit, layers: state.layers,
        visible_layer_states: state.layerStates.filter(l => l.shown).map(l => ({ key: l.key, state: l.state, parsed_count: l.loaded, pending: l.pending, processing: l.processing, failures: l.failures })),
        page_errors_so_far: report.errors.length, console_errors_so_far: report.console_errors.length,
      };
      report.views.push(view);
      await writeFile(join(output, 'capture-in-progress.json'), JSON.stringify(report, null, 2) + '\n');
      console.log(`CAPTURED ${n}/${limit} ${filename} ${width}x${height} ${image.length} bytes`);
    }
  }
  assert.equal(report.views.length, limit);
  assert.equal(new Set(report.views.map(v => v.sha256)).size, limit, 'Images must differ');
  assert.deepEqual(report.errors, []);
  assert.deepEqual(report.console_errors, []);
  assert.deepEqual(report.blocked_external_requests, []);
  assert.deepEqual(report.responses.filter(r => r.status >= 400), []);
  assert.ok(report.failed_requests.every(r => r.reason === 'net::ERR_ABORTED'), 'Only cancelled obsolete requests may fail');
  for (const f of locked) assert.equal(sha(await readFile(join(root, f.path))), f.sha256, `Runtime input changed: ${f.path}`);
  if (limit === 20) for (const b of new Set(route.areas.map(a => a.borough))) assert.equal(report.views.filter(v => v.borough === b).length, 4);
  report.completed_at_utc = new Date().toISOString();
  report.complete = true;
  report.runtime_locks_unchanged = true;
  await writeFile(join(output, 'manifest.json'), JSON.stringify(report, null, 2) + '\n');
  await writeFile(join(output, 'SHA256SUMS'), report.views.map(v => `${v.sha256}  ${v.file}`).join('\n') + '\n');
  await rm(join(output, 'capture-in-progress.json'), { force: true });
  const rows = report.views.map(v => `| ${v.sequence} | ${v.label} | ${v.view} | [PNG](${v.file}) |`).join('\n');
  const images = report.views.map(v => `### ${String(v.sequence).padStart(2, '0')} · ${v.label} · ${v.view}\n\n![${v.label} · ${v.view}](${v.file})\n`).join('\n');
  await writeFile(join(output, 'README.md'), `# 当前运行包 · ${report.views.length}个真实浏览器视角\n\n这些图像由已发布运行包的实际WebGL画面导出，每张保留来源署名；没有生成或补画建筑。默认严格证据模式显示**来源建筑轮廓和局部环境投影**，不是全纽约精细3D建筑完成版。桥面实体、建筑可靠高度和全局地面配准仍未完成。\n\n五区各两个区域，每区斜视与俯视各两张，合计20张。\n\n- 原源码检查点：\`${report.source_commit}\`；实际打开运行包\`index.html\`，随后进入\`inspection.html\`。\n- 抓拍UTC：${report.started_at_utc} 至 ${report.completed_at_utc}；用户时区Asia/Taipei。抓拍时间不是数据观测日期。\n- Chromium ${report.environment.browser}，无头SwiftShader软件渲染；浏览器视口1600×1000、DPR1、原始精度1×、固定中性光，未测试物理GPU。\n- PNG直接来自已有“导出带署名截图”按钮；场景画布为1280×912，另加70像素署名条（实际尺寸见清单）。\n- 新浏览器上下文、HTTP缓存关闭、外网请求阻断；每张在本区真实建筑GLB及道路层加载、可见队列稳定后导出。未隐藏五区建筑、未更改模型或真实尺寸。\n- [完整抓拍记录、相机和实际请求](manifest.json) · [20张PNG校验和](SHA256SUMS)。\n- 相机高度相对展示椭球面，不能解读为真实离地高度；环境资料不是已核验实体道路/桥梁。\n\n| 序号 | 区域 | 视角 | 文件 |\n| --- | --- | --- | --- |\n${rows}\n\n${images}`);
  console.log(`COMPLETE ${report.views.length} real PNGs at ${relative(process.cwd(), output)}; ${report.errors.length} page errors; ${report.console_errors.length} console errors`);
} catch (e) {
  report.failure = String(e.stack ?? e);
  report.failed_at_utc = new Date().toISOString();
  await writeFile(join(output, 'capture-failure.json'), JSON.stringify(report, null, 2) + '\n');
  if (page) await page.screenshot({ path: join(output, 'capture-failure-ui.png') }).catch(() => {});
  throw e;
} finally {
  await browser?.close();
}
