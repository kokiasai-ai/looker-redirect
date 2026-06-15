#!/usr/bin/env python3
"""
相場観ツール index.html ジェネレーター

権限付与一覧シートから最新データを取得して index.html を再生成します。
実行前に: gcloud auth login（初回のみ）

使い方:
  python3 generate.py
"""

import subprocess, urllib.request, json, os
from datetime import datetime, timezone, timedelta

SPREADSHEET_ID = '1rgZoSJDrsjqwM-9GTV5QayR6uHdQ0xiPMRM0bFEZ52I'
SHEET_NAME     = '権限付与一覧'
SHEET_RANGE    = 'E:F'

URL_INTERNAL = 'https://datastudio.google.com/u/0/reporting/bd8c27bd-18b4-43d6-a581-7ac3da626f1f/page/p_0x50gs0bzd'
URL_TOOL_A   = 'https://datastudio.google.com/u/0/reporting/d9090716-b745-41b7-94db-535a98a049cd/page/p_j8if8nhxyd'
URL_TOOL_B   = 'https://datastudio.google.com/u/0/reporting/de57c57b-23c0-4e8b-96a6-8c941c677db5/page/p_j8if8nhxyd'

# ─── 1. アクセストークンを取得 ─────────────────────────────
def get_token():
    result = subprocess.run(
        ['gcloud', 'auth', 'print-access-token'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError('gcloud auth に失敗しました。`gcloud auth login` を実行してください。')
    return result.stdout.strip()

# ─── 2. シートを読み込む ──────────────────────────────────
def fetch_email_map(token):
    import urllib.parse
    range_encoded = urllib.parse.quote(f'{SHEET_NAME}!{SHEET_RANGE}')
    url = f'https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{range_encoded}'
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())

    rows = data.get('values', [])
    email_map = {}
    count_a = count_b = 0

    for row in rows[2:]:  # 1行目空行、2行目ヘッダーをスキップ
        if len(row) >= 2:
            email = row[0].strip().lower()
            tool  = row[1].strip()
            if email and tool:
                if tool == '相場観ツールA':
                    email_map[email] = 'A'
                    count_a += 1
                elif tool == '相場観ツールB':
                    email_map[email] = 'B'
                    count_b += 1

    print(f'  シート読み込み完了: {len(email_map)} 件 (A:{count_a}, B:{count_b})')
    return email_map

# ─── 3. JS ハッシュマップ文字列を生成（SHA-256でメール匿名化）─────
def build_js_map(email_map):
    import hashlib
    entries = []
    for email, tool in sorted(email_map.items()):
        h = hashlib.sha256(email.encode()).hexdigest()
        entries.append(f"  '{h}':'{tool}'")
    return "const EMAIL_HASH_MAP = {\n" + ",\n".join(entries) + "\n};"

# ─── 4. HTML を生成 ──────────────────────────────────────
def generate_html(js_map, generated_at):
    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>相場観ツール</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, sans-serif;
      background: linear-gradient(135deg, #0f2544 0%, #1a3f7c 50%, #2557a7 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }}

    .card {{
      background: #fff;
      border-radius: 20px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
      padding: 52px 44px 44px;
      max-width: 400px;
      width: 100%;
      text-align: center;
    }}

    .brand {{
      display: flex; align-items: center; justify-content: center;
      gap: 10px; margin-bottom: 8px;
    }}
    .brand-icon {{
      width: 40px; height: 40px;
      background: linear-gradient(135deg, #2557a7, #1a3f7c);
      border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
    }}
    .brand-icon svg {{ width: 22px; height: 22px; fill: #fff; }}
    .brand-name {{ font-size: 13px; font-weight: 600; color: #6b7280; letter-spacing: 0.05em; }}

    h1 {{ font-size: 22px; font-weight: 700; color: #111827; margin: 4px 0 6px; }}
    .subtitle {{ font-size: 13px; color: #6b7280; line-height: 1.6; margin-bottom: 36px; }}

    .state {{ display: none; }}
    .state.active {{ display: block; }}

    .spinner-wrap {{ padding: 8px 0 20px; }}
    .spinner {{
      width: 44px; height: 44px;
      border: 4px solid #e5e7eb; border-top-color: #2557a7;
      border-radius: 50%;
      animation: spin 0.75s linear infinite;
      margin: 0 auto 16px;
    }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    .loading-text {{ font-size: 14px; color: #6b7280; }}

    .g-signin-area {{ margin-top: 4px; }}
    .g-signin-area p {{ font-size: 12px; color: #9ca3af; margin-bottom: 12px; }}
    .g_id_signin {{ display: flex; justify-content: center; }}

    .success-icon {{
      width: 60px; height: 60px; background: #d1fae5; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      margin: 0 auto 16px; font-size: 30px;
    }}
    .success-label {{ font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #059669; margin-bottom: 6px; }}
    .success-title {{ font-size: 18px; font-weight: 700; color: #111827; margin-bottom: 8px; }}
    .success-sub {{ font-size: 13px; color: #6b7280; line-height: 1.6; margin-bottom: 20px; }}
    .progress-bar-wrap {{ background: #e5e7eb; border-radius: 9999px; height: 4px; overflow: hidden; margin-bottom: 16px; }}
    .progress-bar {{ height: 4px; background: #2557a7; border-radius: 9999px; animation: progress 1.5s ease forwards; }}
    @keyframes progress {{ from {{ width: 0%; }} to {{ width: 100%; }} }}
    .manual-link {{ font-size: 12px; color: #2557a7; text-decoration: none; }}
    .manual-link:hover {{ text-decoration: underline; }}

    .error-icon {{ font-size: 44px; margin-bottom: 12px; }}
    .error-title {{ font-size: 16px; font-weight: 700; color: #111827; margin-bottom: 8px; }}
    .error-msg {{ font-size: 13px; color: #6b7280; line-height: 1.7; white-space: pre-wrap; margin-bottom: 16px; }}
    .email-tag {{ display: inline-block; background: #f3f4f6; border-radius: 6px; padding: 3px 10px; font-size: 12px; color: #374151; font-family: monospace; margin-bottom: 20px; }}
    .btn-retry {{
      display: inline-flex; align-items: center; gap: 6px;
      padding: 10px 20px; border: 1.5px solid #d1d5db; border-radius: 8px;
      font-size: 13px; font-weight: 500; color: #374151; background: #fff;
      cursor: pointer; transition: background 0.15s;
    }}
    .btn-retry:hover {{ background: #f9fafb; }}

    .card-footer {{ margin-top: 28px; padding-top: 20px; border-top: 1px solid #f3f4f6; font-size: 11px; color: #9ca3af; }}
  </style>
</head>
<body>

<!-- ============================================================
     ⚠️  GOOGLE_CLIENT_ID を自分のOAuth 2.0 クライアントIDに置き換えてください
     取得方法: https://console.cloud.google.com/ → APIとサービス → 認証情報
              → 「認証情報を作成」→「OAuthクライアントID」→「ウェブアプリケーション」
              → 「承認済みのJavaScriptオリジン」に公開URLを追加
     ============================================================ -->
<div id="g_id_onload"
     data-client_id="GOOGLE_CLIENT_ID"
     data-callback="handleCredential"
     data-auto_select="true"
     data-cancel_on_tap_outside="false"
     data-context="signin">
</div>

<div class="card">
  <div class="brand">
    <div class="brand-icon">
      <svg viewBox="0 0 24 24"><path d="M9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4zm2.5 2.1h-15V5h15v14.1zm0-16.1h-15c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h15c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z"/></svg>
    </div>
    <span class="brand-name">Indeed 新卒事業部</span>
  </div>
  <h1>相場観ツール</h1>
  <p class="subtitle">ログイン中のGoogleアカウントを確認して<br>適切なダッシュボードに案内します</p>

  <div id="state-loading" class="state active">
    <div class="spinner-wrap">
      <div class="spinner"></div>
      <p class="loading-text">アカウントを確認中...</p>
    </div>
    <div class="g-signin-area" id="signin-fallback" style="display:none;">
      <p>Googleアカウントでサインインしてください</p>
      <div class="g_id_signin"
           data-type="standard" data-shape="rectangular"
           data-theme="outline" data-text="signin_with"
           data-size="large" data-locale="ja" data-logo_alignment="left">
      </div>
    </div>
  </div>

  <div id="state-redirect" class="state">
    <div class="success-icon">✓</div>
    <p class="success-label">アクセス確認済み</p>
    <p class="success-title" id="redirect-title">ダッシュボードに移動中</p>
    <p class="success-sub" id="redirect-sub">自動でリダイレクトします...</p>
    <div class="progress-bar-wrap"><div class="progress-bar"></div></div>
    <a class="manual-link" id="redirect-link" href="#" target="_blank">自動で移動しない場合はこちら →</a>
  </div>

  <div id="state-error" class="state">
    <div class="error-icon">🔒</div>
    <p class="error-title">アクセスできません</p>
    <p class="error-msg" id="error-msg"></p>
    <p class="email-tag" id="error-email"></p>
    <button class="btn-retry" onclick="retrySignin()">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M17.65 6.35A7.958 7.958 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg>
      別のアカウントで試す
    </button>
  </div>

  <div class="card-footer">アクセス申請は担当者までお問い合わせください</div>
</div>

<script src="https://accounts.google.com/gsi/client" async defer></script>
<script>
const URL_INTERNAL = '{URL_INTERNAL}';
const URL_TOOL_A   = '{URL_TOOL_A}';
const URL_TOOL_B   = '{URL_TOOL_B}';

// 権限付与一覧（生成日時: {generated_at}）
{js_map}

function showState(id) {{
  document.querySelectorAll('.state').forEach(el => el.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}}

function showRedirect(url, label) {{
  document.getElementById('redirect-title').textContent = label + ' に移動します';
  document.getElementById('redirect-sub').textContent = '1〜2秒後に自動でリダイレクトします。';
  document.getElementById('redirect-link').href = url;
  showState('state-redirect');
  setTimeout(() => {{ window.location.href = url; }}, 1500);
}}

function showError(msg, email) {{
  document.getElementById('error-msg').textContent = msg;
  const tag = document.getElementById('error-email');
  tag.textContent = email || '';
  tag.style.display = email ? 'inline-block' : 'none';
  showState('state-error');
}}

function retrySignin() {{
  showState('state-loading');
  document.getElementById('signin-fallback').style.display = 'block';
  google.accounts.id.prompt();
}}

function handleCredential(response) {{
  try {{
    const payload = JSON.parse(atob(response.credential.split('.')[1]));
    const email   = (payload.email || '').trim().toLowerCase();
    if (!email) {{ showError('メールアドレスを取得できませんでした。', ''); return; }}
    if (email.endsWith('@indeed.com')) {{ showRedirect(URL_INTERNAL, '社内用ダッシュボード'); return; }}
    const tool = EMAIL_MAP[email];
    if (tool === 'A')      {{ showRedirect(URL_TOOL_A, '相場観ツールA'); }}
    else if (tool === 'B') {{ showRedirect(URL_TOOL_B, '相場観ツールB'); }}
    else {{ showError('このアカウントにはアクセス権限が付与されていません。\\n担当者にご連絡ください。', email); }}
  }} catch (e) {{
    showError('認証処理中にエラーが発生しました: ' + e.message, '');
  }}
}}

window.addEventListener('load', function() {{
  setTimeout(() => {{
    if (document.getElementById('state-loading').classList.contains('active')) {{
      document.getElementById('signin-fallback').style.display = 'block';
    }}
  }}, 5000);
}});
</script>
</body>
</html>'''

# ─── main ────────────────────────────────────────────────
if __name__ == '__main__':
    print('📊 シートからデータを取得中...')
    token     = get_token()
    email_map = fetch_email_map(token)
    js_map    = build_js_map(email_map)

    JST = timezone(timedelta(hours=9))
    generated_at = datetime.now(JST).strftime('%Y-%m-%d %H:%M JST')

    html = generate_html(js_map, generated_at)

    output_path = os.path.join(os.path.dirname(__file__), 'index.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'✅ index.html を生成しました ({len(html):,} bytes)')
    print(f'   {output_path}')
    print()
    print('次のステップ: index.html の GOOGLE_CLIENT_ID を置き換えてから')
    print('             GitHub Pages にプッシュしてください。')
