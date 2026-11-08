/* Smoke test (tools/ui_test.py runs it at 1280 px and at 390 px): every page address opens without errors, is not
   empty and doesn't scroll sideways, signed out, then as a new agent (a lesson, a case search, the training file's
   four tabs, every gadget), then as admin (every Admin tab). Python/JS errors are caught by ui_test.py from the
   browser log. Resolves to {ok, log}. */
(async function () {
  const log = [], bad = [];
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  async function until(fn, what, ms) {
    const end = Date.now() + (ms || 20000);
    while (Date.now() < end) { try { const v = fn(); if (v) return v; } catch (e) {} await sleep(150); }
    throw new Error('timed out waiting for: ' + what);
  }
  const $ = (s) => document.querySelector(s), $$ = (s) => Array.from(document.querySelectorAll(s));
  const errs = [];
  window.addEventListener('error', (e) => errs.push(String(e.message || e)));
  function type(input, value) {
    input.focus(); input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true }));
  }
  function button(re, root) { return $$((root || '') + ' button').find((b) => re.test(b.textContent) && b.offsetParent !== null); }
  async function open(hash, expect, landed) {
    if (location.hash !== hash) window.UI_READY = false;
    location.hash = hash;
    await until(() => window.UI_READY && (landed ? landed() : location.hash === hash), hash, 30000);
    await sleep(700);
    check(hash, expect);
  }
  function check(hash, expect) {
    const main = $('.ui-main');
    const text = main ? main.innerText.trim() : '';
    const w = document.documentElement.scrollWidth, vw = screen.width <= 500 ? screen.width : window.innerWidth;
    const problems = [];
    if (text.length < 40) problems.push('empty page');
    if (expect && !new RegExp(expect.source, 'i').test(text)) problems.push('missing ' + expect);
    if (w > vw + 1) {
      const wide = $$('body *').filter((e) => { const r = e.getBoundingClientRect(); return r.width && r.right > vw + 1; })
        .slice(0, 3).map((e) => e.tagName.toLowerCase() + '.' + String(e.className).split(' ').slice(0, 2).join('.'));
      problems.push('scrolls sideways (' + w + ' > ' + vw + ') ' + wide.join(' '));
    }
    if (errs.length) problems.push('errors: ' + errs.splice(0).join(' / '));
    if (problems.length) bad.push(hash + ': ' + problems.join('; '));
    log.push((problems.length ? 'BAD  ' : 'ok   ') + hash);
  }
  async function signUp(name, email, password) {
    location.hash = '#auth/signup';
    await until(() => window.UI_READY && $$('.au-card input').length >= 3, 'sign-up form');
    await sleep(400);
    const inputs = $$('.au-card input[type=text], .au-card input[type=email], .au-card input[type=password]');
    type(inputs[0], name); type(inputs[1], email); type(inputs[2], password);
    const tick = $('.au-card input[type=checkbox]'); if (tick && !tick.checked) tick.click();
    button(/Create account/, '.au-card .anvil-role-btn-block').click();
    const end = Date.now() + 40000;
    while (Date.now() < end) {
      if (!location.hash.startsWith('#auth') && window.UI_READY && $('.anvil-role-avatar button')) return true;  // home, or the page they were heading for
      const msg = $('.au-card .anvil-role-msg-error');
      if (msg && msg.offsetParent !== null && msg.textContent.trim()) { log.push('sign-up said: ' + msg.textContent.trim()); return false; }
      await sleep(200);
    }
    log.push('sign-up: still on ' + location.hash);
    return false;
  }
  async function signIn(email, password) {
    location.hash = '#auth';
    await until(() => window.UI_READY && $$('.au-card input[type=password]').length, 'sign-in form');
    await sleep(400);
    type($('.au-card input[type=email]'), email); type($('.au-card input[type=password]'), password);
    button(/Sign in/, '.au-card .anvil-role-btn-block').click();
    await until(() => location.hash === '#home' && window.UI_READY, 'signed in as ' + email, 30000);
  }
  async function signOut() {
    $('.anvil-role-avatar button').click();
    await sleep(300);
    button(/Sign out/, '.ui-menu').click();
    await until(() => {  // the account button goes once sign-out has finished
      const a = $('.anvil-role-avatar button');
      return location.hash === '#landing' && window.UI_READY && (!a || a.offsetParent === null);
    }, 'signed out');
  }
  try {
    // ---- signed out
    await open('#landing', /Learn to read it/);
    await open('#auth', /Welcome back/);
    await open('#auth/signup', /Create your account/);
    await open('#cases', /Sign in/, () => location.hash === '#cases' && $('.au-card'));  // members only: asks to sign in

    // ---- a new agent
    const ok = await signUp('Smoke Tester', 'smoke' + Date.now() + '@example.com', 'Os-' + Math.random().toString(36).slice(2) + '-Kq7');
    if (!ok) throw new Error('sign-up failed');
    await open('#home', /Agent Smoke/);
    await open('#academy', /training files/);
    await open('#academy/m1l1', /Pop quiz/);
    await open('#academy/nope', /doesn't exist/);
    await open('#cases', /filing cabinet/);
    await open('#cases/c1', /FIELD TERMINAL/);
    type($('.cd-search input'), 'biscuit');
    button(/Run/, '.cd-search').click();
    await until(() => /result|no results/.test(($('.cd-log') || {}).textContent || ''), 'a search reply', 20000);
    log.push('     case search: ' + $('.cd-log').textContent.trim().slice(0, 80));
    check('#cases/c1 (after a search)', /Notebook/);
    await open('#casebook', /casebook/);
    button(/Add the training file/).click();
    await until(() => /^#casebook\/.+/.test(location.hash) && window.UI_READY && $('.cb-pin'), 'the training file on the corkboard', 30000);
    const inv = location.hash.split('/')[1];
    check('#casebook/<training file>', /Corkboard/);
    for (const t of ['leads', 'checklist', 'report']) await open('#casebook/' + inv + '/' + t, /Corkboard/);
    await open('#kit', /The library/);
    for (const g of ['dorkbuilder', 'permutator', 'emailperm', 'exifreader', 'snowflake', 'grader']) await open('#kit/' + g, /Field Kit/);
    await open('#profile', /Service record/);
    await open('#landing', /Back to the office/);
    await signOut();

    // ---- admin (ADMIN_EMAILS in Accounts.py): sign up the first time, sign in after that
    const adminPw = 'Os-smoke-adm-93Kx-7q';
    if (!(await signUp('Admin Tester', 'arkulinskis@gmail.com', adminPw))) await signIn('arkulinskis@gmail.com', adminPw);
    for (const t of ['overview', 'feedback', 'users', 'training', 'bulletins', 'demo']) await open('#admin/' + t, /Admin/);
    await signOut();
    log.push(bad.length ? 'PROBLEMS: ' + bad.join(' | ') : 'PASSED');
    return { ok: !bad.length, log: log };
  } catch (e) {
    log.push(String(e && e.message || e));
    if (bad.length) log.push('PROBLEMS: ' + bad.join(' | '));
    return { ok: false, log: log };
  }
})();
