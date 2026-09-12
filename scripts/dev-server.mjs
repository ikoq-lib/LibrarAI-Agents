// 로컬 개발 서버 — 정적 파일 + Vercel 서버리스 함수(api/*.js)를 그대로 태운다.
// vercel dev 없이 웹앱 전체 경로(리프 호출·문서 생성)를 실제로 돌려보기 위한 것.
//
// 실행: node scripts/dev-server.mjs [포트]
import http from "http";
import fs from "fs";
import path from "path";
import { fileURLToPath, pathToFileURL } from "url";
import { createRequire } from "module";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(import.meta.url);
const port = +(process.argv[2] || 5173);

// .env.local 을 process.env 에 올린다(서버리스 함수가 키를 여기서 읽는다)
for (const name of [".env", ".env.local"]) {
  const file = path.join(root, name);
  if (!fs.existsSync(file)) continue;
  for (const line of fs.readFileSync(file, "utf8").split(/\r?\n/)) {
    const m = line.match(/^([A-Z0-9_]+)=(.*)$/);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2].trim();
  }
}

const MIME = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8", ".png": "image/png", ".svg": "image/svg+xml" };

// Vercel 핸들러가 기대하는 res.status()/json() 를 Node 응답에 붙인다
const vercelRes = (res) => {
  res.status = (code) => { res.statusCode = code; return res; };
  res.json = (obj) => { res.setHeader("Content-Type", "application/json; charset=utf-8"); res.end(JSON.stringify(obj)); return res; };
  res.send = (body) => { res.end(body); return res; };
  return res;
};

const readBody = (req) => new Promise((resolve) => {
  let raw = "";
  req.on("data", c => { raw += c; });
  req.on("end", () => { try { resolve(raw ? JSON.parse(raw) : {}); } catch { resolve({}); } });
});

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${port}`);
  if (url.pathname.startsWith("/api/")) {
    const file = path.join(root, url.pathname.replace(/\/$/, "") + ".js");
    if (!fs.existsSync(file)) { res.statusCode = 404; return res.end("no such api"); }
    try {
      const mod = require(file);
      const handler = mod.default || mod;
      req.body = req.method === "POST" ? await readBody(req) : {};
      req.query = Object.fromEntries(url.searchParams);
      await handler(req, vercelRes(res));
    } catch (e) {
      console.error("[api]", url.pathname, e.message);
      if (!res.headersSent) { res.statusCode = 500; res.end(JSON.stringify({ error: e.message })); }
    }
    return;
  }
  const rel = url.pathname === "/" ? "/LibrarAI.html" : decodeURIComponent(url.pathname);
  const file = path.join(root, rel);
  if (!file.startsWith(root) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    res.statusCode = 404; return res.end("not found");
  }
  res.setHeader("Content-Type", MIME[path.extname(file)] || "application/octet-stream");
  fs.createReadStream(file).pipe(res);
});

server.listen(port, () => console.log(`dev server http://localhost:${port} (root: ${root})`));
