/**
 * 文章博士 フロントエンド — 校正フォームの制御。
 *
 * フォーム送信を横取りして /njc.cgi?format=json を fetch し、結果を
 * ページ遷移なしに描画する。JavaScript が無効なら通常の POST で
 * 従来の HTML 画面（njc.cgi）にフォールバックする。
 */

type ErrorType = 1 | 2 | 3 | 4 | 5 | 6 | 7;

interface Sentence { no: number; text: string; html: string }
interface ProofError {
  sentence: number;
  type: ErrorType;
  label: string;
  cssClass: string;
  message: string;
  phrase: string;
}
interface Explanation { type: ErrorType; title: string; lines: string[] }
interface ProofResult {
  ok: boolean;
  input: string;
  sentences: Sentence[];
  errors: ProofError[];
  summary: Record<string, number>;
  explanations: Explanation[];
  errorTypes: { type: ErrorType; label: string; cssClass: string }[];
}

const API = '/njc.cgi';
const DRAFT_KEY = 'monjo-hakase:draft';
const ALLOWED_CLASSES = new Set([
  'error-missing-subject',
  'error-avoid-using',
  'reversed-word-order',
  'too-many-connection',
  'too-long-chaining',
]);
/** 種別ごとの一覧用アクセント（本文マークと同じ意味色） */
const TYPE_VAR: Record<ErrorType, string> = {
  1: 'var(--mark-subject)',
  2: 'var(--mark-avoid)',
  3: 'var(--mark-reversed)',
  4: 'var(--mark-phrase)',
  5: 'var(--mark-sentence)',
  6: 'var(--mark-connection)',
  7: 'var(--mark-chain)',
};

const SAMPLE_TEXT = [
  'これは文章博士のサンプル文です。',
  '本システムは、係り受け解析を行うことによって、技術文書の読みやすさを改善するためのものであるということができます。',
  '入力された文章を解析して、主語がない文や、冗長な表現、語順、文節の長さ、係り受けの深さと量を指摘し、色を付けて表示し、一覧にまとめ、解説も添えて出力します。',
].join('\n');

function $<T extends Element>(sel: string, root: ParentNode = document): T {
  const el = root.querySelector<T>(sel);
  if (!el) throw new Error(`element not found: ${sel}`);
  return el;
}

/**
 * njc.cgi が返す本文 HTML（<span class="…"> と <br> のみを含む想定）を
 * 許可リストで濾しながら DOM に変換する。入力文は CGI 側で <,>,& が
 * 全角化されているため実質タグは含まれないが、念のため防御的に扱う。
 */
function sanitizeMarkup(html: string): DocumentFragment {
  const doc = new DOMParser().parseFromString(`<div>${html}</div>`, 'text/html');
  const src = doc.body.firstElementChild as HTMLElement;
  const frag = document.createDocumentFragment();
  const walk = (from: Node, to: Node) => {
    for (const child of Array.from(from.childNodes)) {
      if (child.nodeType === Node.TEXT_NODE) {
        to.appendChild(document.createTextNode(child.textContent ?? ''));
      } else if (child instanceof HTMLElement) {
        const tag = child.tagName.toLowerCase();
        if (tag === 'br') {
          to.appendChild(document.createElement('br'));
        } else if (tag === 'span') {
          const span = document.createElement('span');
          const classes = (child.getAttribute('class') ?? '')
            .split(/\s+/)
            .filter((c) => ALLOWED_CLASSES.has(c));
          if (classes.length) span.className = classes.join(' ');
          walk(child, span);
          to.appendChild(span);
        } else {
          // 想定外のタグは中身だけ残す
          walk(child, to);
        }
      }
    }
  };
  walk(src, frag);
  return frag;
}

/** 一覧のメッセージ（<br> 区切りの複数行）をテキストとして安全に描画 */
function renderMessage(message: string): DocumentFragment {
  const frag = document.createDocumentFragment();
  const parts = message.split(/<br\s*\/?>/i);
  parts.forEach((part, i) => {
    if (i > 0) frag.appendChild(document.createElement('br'));
    // 語順・冗長表現の「 -> 」を矢印記号に整形
    const text = part.replace(/\s->\s/g, ' → ');
    frag.appendChild(document.createTextNode(text));
  });
  return frag;
}

function main() {
  const form = $<HTMLFormElement>('#proof-form');
  const textarea = $<HTMLTextAreaElement>('#txtInput');
  const submitBtn = $<HTMLButtonElement>('#btn-submit');
  const clearBtn = $<HTMLButtonElement>('#btn-clear');
  const sampleBtn = $<HTMLButtonElement>('#btn-sample');
  const counter = $<HTMLElement>('#char-count');
  const status = $<HTMLElement>('#status');
  const results = $<HTMLElement>('#results');
  const summaryEl = $<HTMLElement>('#summary');
  const bodyEl = $<HTMLElement>('#body-text');
  const tableBody = $<HTMLTableSectionElement>('#error-rows');
  const tableWrap = $<HTMLElement>('#error-table');
  const explainEl = $<HTMLElement>('#explanations');
  const emptyEl = $<HTMLElement>('#no-errors');

  // ---- 下書きの復元 ----
  try {
    const draft = localStorage.getItem(DRAFT_KEY);
    if (draft && !textarea.value) textarea.value = draft;
  } catch { /* private mode 等 */ }

  const updateCount = () => {
    const n = Array.from(textarea.value.replace(/\r?\n/g, '')).length;
    counter.textContent = `${n.toLocaleString('ja-JP')} 文字`;
    submitBtn.disabled = textarea.value.trim() === '';
  };
  updateCount();

  let draftTimer: number | undefined;
  textarea.addEventListener('input', () => {
    updateCount();
    window.clearTimeout(draftTimer);
    draftTimer = window.setTimeout(() => {
      try { localStorage.setItem(DRAFT_KEY, textarea.value); } catch { /* noop */ }
    }, 300);
  });

  // ---- ボタン ----
  clearBtn.addEventListener('click', () => {
    textarea.value = '';
    updateCount();
    try { localStorage.removeItem(DRAFT_KEY); } catch { /* noop */ }
    results.hidden = true;
    setStatus('');
    textarea.focus();
  });
  sampleBtn.addEventListener('click', () => {
    textarea.value = SAMPLE_TEXT;
    updateCount();
    textarea.focus();
    form.requestSubmit();
  });

  // ⌘/Ctrl + Enter で送信
  textarea.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      form.requestSubmit();
    }
  });

  function setStatus(msg: string, kind: '' | 'busy' | 'error' = '') {
    status.textContent = msg;
    status.dataset.kind = kind;
  }

  function setBusy(busy: boolean) {
    form.classList.toggle('is-busy', busy);
    submitBtn.setAttribute('aria-busy', String(busy));
    submitBtn.disabled = busy || textarea.value.trim() === '';
    results.setAttribute('aria-busy', String(busy));
  }

  // ---- 送信 ----
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = textarea.value;
    if (!text.trim()) { textarea.focus(); return; }

    const fd = new FormData();
    fd.set('txtInput', text);
    fd.set('btnKaiseki', '校正');
    fd.set('format', 'json');

    setBusy(true);
    setStatus('解析中… 文の数が多いと数秒かかります。', 'busy');
    const started = performance.now();
    try {
      const res = await fetch(API, { method: 'POST', body: fd, headers: { Accept: 'application/json' } });
      const ctype = res.headers.get('content-type') ?? '';
      if (!res.ok || !ctype.includes('application/json')) {
        throw new Error(`サーバーが想定外の応答を返しました（HTTP ${res.status}）`);
      }
      const data = (await res.json()) as ProofResult;
      if (!data.ok) throw new Error('校正に失敗しました');
      render(data);
      const ms = Math.round(performance.now() - started);
      const total = data.errors.length;
      setStatus(total === 0
        ? `解析完了（${(ms / 1000).toFixed(1)} 秒）。指摘はありません。`
        : `解析完了（${(ms / 1000).toFixed(1)} 秒）。${data.sentences.length} 文中 ${total} 件を指摘しました。`);
      results.hidden = false;
      results.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setStatus(`エラー: ${msg}。時間をおいて再度お試しください。`, 'error');
    } finally {
      setBusy(false);
      submitBtn.querySelector('.label')!.textContent = '再校正する';
    }
  });

  // ---- 描画 ----
  function render(data: ProofResult) {
    // サマリー
    summaryEl.replaceChildren();
    const total = data.errors.length;
    const totalChip = document.createElement('div');
    totalChip.className = 'chip chip--total';
    totalChip.innerHTML = `<b>${total}</b><span>件の指摘</span>`;
    summaryEl.appendChild(totalChip);
    for (const t of data.errorTypes) {
      const n = data.summary[String(t.type)] ?? 0;
      if (n === 0) continue;
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'chip';
      chip.style.setProperty('--chip-accent', TYPE_VAR[t.type]);
      chip.innerHTML = `<i aria-hidden="true"></i><span>${t.label}</span><b>${n}</b>`;
      chip.title = `${t.label} の指摘へ移動`;
      chip.addEventListener('click', () => {
        const row = tableBody.querySelector<HTMLElement>(`tr[data-type="${t.type}"]`);
        row?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        row?.classList.add('is-flash');
        window.setTimeout(() => row?.classList.remove('is-flash'), 1200);
      });
      summaryEl.appendChild(chip);
    }

    // 本文
    bodyEl.replaceChildren();
    const errCount = new Map<number, number>();
    for (const e of data.errors) errCount.set(e.sentence, (errCount.get(e.sentence) ?? 0) + 1);
    for (const s of data.sentences) {
      const p = document.createElement('p');
      p.className = 'sentence';
      p.id = `s-${s.no}`;
      if (errCount.get(s.no)) p.dataset.errors = String(errCount.get(s.no));
      const num = document.createElement('span');
      num.className = 'sentence__no';
      num.textContent = String(s.no);
      num.title = `文 ${s.no}`;
      p.appendChild(num);
      const body = document.createElement('span');
      body.className = 'sentence__text';
      body.appendChild(sanitizeMarkup(s.html));
      p.appendChild(body);
      bodyEl.appendChild(p);
    }

    // 一覧
    tableBody.replaceChildren();
    for (const e of data.errors) {
      const tr = document.createElement('tr');
      tr.dataset.type = String(e.type);
      tr.style.setProperty('--row-accent', TYPE_VAR[e.type]);
      const tdType = document.createElement('td');
      tdType.className = 'col-type';
      tdType.innerHTML = `<i aria-hidden="true"></i><span></span>`;
      tdType.querySelector('span')!.textContent = e.label;
      const tdNo = document.createElement('td');
      tdNo.className = 'col-no';
      const link = document.createElement('a');
      link.href = `#s-${e.sentence}`;
      link.textContent = String(e.sentence);
      link.addEventListener('click', (ev) => {
        ev.preventDefault();
        const target = document.getElementById(`s-${e.sentence}`);
        target?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        target?.classList.add('is-flash');
        window.setTimeout(() => target?.classList.remove('is-flash'), 1200);
      });
      tdNo.appendChild(link);
      const tdMsg = document.createElement('td');
      tdMsg.className = 'col-msg';
      tdMsg.appendChild(renderMessage(e.message));
      tr.append(tdType, tdNo, tdMsg);
      tableBody.appendChild(tr);
    }
    tableWrap.hidden = total === 0;
    emptyEl.hidden = total !== 0;

    // 解説
    explainEl.replaceChildren();
    for (const ex of data.explanations) {
      const details = document.createElement('details');
      details.className = 'explain';
      details.open = data.explanations.length <= 2;
      details.style.setProperty('--row-accent', TYPE_VAR[ex.type]);
      const summary = document.createElement('summary');
      summary.innerHTML = `<i aria-hidden="true"></i><span></span>`;
      summary.querySelector('span')!.textContent = ex.title;
      details.appendChild(summary);
      const p = document.createElement('p');
      p.textContent = ex.lines.join('');
      details.appendChild(p);
      explainEl.appendChild(details);
    }
    explainEl.parentElement!.hidden = data.explanations.length === 0;
  }

  // 初期フォーカス（開いたらすぐ書ける）
  if (!/Mobi|Android/i.test(navigator.userAgent)) textarea.focus();
  // macOS なら ⌘ 表記
  const kbd = document.querySelector<HTMLElement>('#kbd-mod');
  if (kbd && /Mac|iPhone|iPad/.test(navigator.platform)) kbd.textContent = '⌘';
}

main();
