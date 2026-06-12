// ============================================================
// 相場観ツール — 権限付与一覧 自動同期スクリプト
//
// 【セットアップ手順】
// 1. script.google.com で新しいプロジェクトを作成
// 2. このコードを貼り付ける
// 3. 「プロジェクトの設定」→「スクリプト プロパティ」に以下を追加:
//      GITHUB_TOKEN : ghp_xxxxxxxxxx（repo スコープのGitHub PAT）
// 4. setupTrigger() を一度だけ手動実行してトリガーを設定
// ============================================================

const SPREADSHEET_ID = '1rgZoSJDrsjqwM-9GTV5QayR6uHdQ0xiPMRM0bFEZ52I';
const SHEET_NAME     = '権限付与一覧';
const GITHUB_OWNER   = 'kokiasai-ai';
const GITHUB_REPO    = 'looker-redirect';
const GITHUB_FILE    = 'index.html';
const START_MARKER   = '// %%EMAIL_MAP_START%%';
const END_MARKER     = '// %%EMAIL_MAP_END%%';

// ── メイン関数（タイマーで自動実行） ─────────────────────
function syncPermissions() {
  const token = PropertiesService.getScriptProperties().getProperty('GITHUB_TOKEN');
  if (!token) {
    Logger.log('ERROR: スクリプトプロパティ "GITHUB_TOKEN" が設定されていません。');
    return;
  }

  // 1. シートから最新のメールリストを取得
  const emailMap = fetchEmailMap_();
  Logger.log(`シート読み込み完了: ${Object.keys(emailMap).length} 件`);

  // 2. JSマップ文字列を生成
  const jsMap = buildJsMap_(emailMap);

  // 3. 生成日時（JST）
  const now = new Date();
  const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
  const generatedAt = Utilities.formatDate(jst, 'Asia/Tokyo', 'yyyy-MM-dd HH:mm') + ' JST';

  // 4. GitHubから現在のindex.htmlを取得
  const apiUrl = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${GITHUB_FILE}`;
  const getResp = UrlFetchApp.fetch(apiUrl, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/vnd.github.v3+json'
    },
    muteHttpExceptions: true
  });

  if (getResp.getResponseCode() !== 200) {
    Logger.log('ERROR: GitHub ファイル取得失敗 (' + getResp.getResponseCode() + '): ' + getResp.getContentText());
    return;
  }

  const fileData     = JSON.parse(getResp.getContentText());
  const sha          = fileData.sha;
  const base64Clean  = fileData.content.replace(/\n/g, '');
  const currentBytes = Utilities.base64Decode(base64Clean);
  const currentHtml  = Utilities.newBlob(currentBytes).getDataAsString('UTF-8');

  // 5. マーカー間を新しいEMAIL_MAPで置換
  const startIdx = currentHtml.indexOf(START_MARKER);
  const endIdx   = currentHtml.indexOf(END_MARKER);

  if (startIdx === -1 || endIdx === -1) {
    Logger.log('ERROR: マーカーが見つかりません。index.html が正しく生成されているか確認してください。');
    return;
  }

  const newBlock   = `${START_MARKER}\n// 権限付与一覧（生成日時: ${generatedAt}）\n${jsMap}\n${END_MARKER}`;
  const newHtml    = currentHtml.slice(0, startIdx) + newBlock + currentHtml.slice(endIdx + END_MARKER.length);

  // 6. 変更がなければスキップ
  if (newHtml === currentHtml) {
    Logger.log('変更なし — 更新をスキップします。');
    return;
  }

  // 7. GitHubに更新をプッシュ
  const newBase64 = Utilities.base64Encode(Utilities.newBlob(newHtml, 'text/html', 'UTF-8').getBytes());

  const putResp = UrlFetchApp.fetch(apiUrl, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/vnd.github.v3+json',
      'Content-Type': 'application/json'
    },
    payload: JSON.stringify({
      message: `chore: 権限付与一覧を自動更新 (${generatedAt})`,
      content: newBase64,
      sha: sha
    }),
    muteHttpExceptions: true
  });

  const code = putResp.getResponseCode();
  if (code === 200 || code === 201) {
    Logger.log(`✅ GitHub 更新完了 (${generatedAt}) — ${Object.keys(emailMap).length} 件`);
  } else {
    Logger.log('ERROR: GitHub 更新失敗 (' + code + '): ' + putResp.getContentText());
  }
}

// ── 内部: シートからメールマップを取得 ───────────────────
function fetchEmailMap_() {
  const ss      = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet   = ss.getSheetByName(SHEET_NAME);
  const lastRow = sheet.getLastRow();
  if (lastRow < 3) return {};

  const emails = sheet.getRange(3, 5, lastRow - 2, 1).getValues(); // E列
  const tools  = sheet.getRange(3, 6, lastRow - 2, 1).getValues(); // F列
  const map    = {};

  for (let i = 0; i < emails.length; i++) {
    const email = (emails[i][0] || '').toString().trim().toLowerCase();
    const tool  = (tools[i][0]  || '').toString().trim();
    if (email && (tool === '相場観ツールA' || tool === '相場観ツールB')) {
      map[email] = tool === '相場観ツールA' ? 'A' : 'B';
    }
  }
  return map;
}

// ── 内部: JSマップ文字列を生成 ────────────────────────────
function buildJsMap_(emailMap) {
  const entries = Object.keys(emailMap).sort().map(email => {
    const safe = email.replace(/'/g, "\\'");
    return `  '${safe}':'${emailMap[email]}'`;
  });
  return `const EMAIL_MAP = {\n${entries.join(',\n')}\n};`;
}

// ── トリガー設定（初回1回だけ手動実行） ──────────────────
function setupTrigger() {
  // 既存トリガーをすべて削除
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));

  // 毎朝9時に実行
  ScriptApp.newTrigger('syncPermissions')
    .timeBased()
    .everyDays(1)
    .atHour(9)
    .inTimezone('Asia/Tokyo')
    .create();

  Logger.log('✅ トリガー設定完了: 毎日 09:00 JST に自動実行');
}

// ── 動作確認用（手動実行で即座にテスト） ─────────────────
function testRun() {
  Logger.log('=== テスト実行開始 ===');
  syncPermissions();
  Logger.log('=== テスト実行完了 ===');
}
