# 相場観ツール ランディングページ

ブラウザにログイン済みのGoogleアカウントを自動検出して、適切なLooker Studioダッシュボードにリダイレクトするランディングページです。

## リダイレクトロジック

| 条件 | 遷移先 |
|---|---|
| `@indeed.com` アカウント | 社内用ダッシュボード ① |
| 権限付与一覧 → 相場観ツールA | ダッシュボード A ② |
| 権限付与一覧 → 相場観ツールB | ダッシュボード B ③ |
| 未登録アカウント | アクセス不可メッセージ |

## ユーザー体験

1. URLを開く
2. **（ほぼ自動）** Googleアカウントが自動検出される（One Tap）
3. 1〜2秒でダッシュボードにリダイレクト

---

## セットアップ手順

### ステップ1: Google OAuth クライアントIDを取得

1. [Google Cloud Console](https://console.cloud.google.com/) を開く
2. プロジェクトを選択（なければ新規作成）
3. 「APIとサービス」→「認証情報」→「認証情報を作成」→「OAuthクライアントID」
4. アプリケーションの種類：「ウェブアプリケーション」
5. 名前：「相場観ツール」など
6. 「承認済みのJavaScriptオリジン」に公開URLを追加（後で追記可）
7. クライアントIDをコピー

### ステップ2: index.html のクライアントIDを書き換える

`index.html` 内の `GOOGLE_CLIENT_ID` を置き換える：

```html
<!-- 変更前 -->
data-client_id="GOOGLE_CLIENT_ID"

<!-- 変更後（例） -->
data-client_id="123456789-xxxxxxxxxxxx.apps.googleusercontent.com"
```

### ステップ3: GitHub Pages で公開する

```bash
# 1. GitHubで新しいリポジトリを作成（例: looker-redirect）
# 2. このディレクトリをプッシュ

cd /Users/kasai/cursor/looker-redirect
git init
git add index.html
git commit -m "Add looker redirect landing page"
git remote add origin https://github.com/YOUR_USERNAME/looker-redirect.git
git push -u origin main

# 3. GitHub のリポジトリページ → Settings → Pages
#    Source: Deploy from a branch → main → / (root) → Save
```

公開URL: `https://YOUR_USERNAME.github.io/looker-redirect/`

### ステップ4: OAuth の承認済みオリジンに GitHub Pages URL を追加

Google Cloud Console の OAuth クライアント設定に戻り、
「承認済みのJavaScriptオリジン」に `https://YOUR_USERNAME.github.io` を追加。

---

## 権限付与一覧が更新されたときの対応

新しいパートナーが追加されたら、以下を実行して index.html を再生成：

```bash
cd /Users/kasai/cursor/looker-redirect
python3 generate.py
```

その後、生成された `index.html` を GitHub にプッシュすれば反映されます。

```bash
git add index.html
git commit -m "Update email permissions"
git push
```

---

## ファイル構成

```
looker-redirect/
├── index.html     # ランディングページ本体（権限リスト埋め込み済み）
├── generate.py    # シートから最新データを取得してindex.htmlを再生成するスクリプト
└── README.md      # このファイル
```

## よくある質問

**Q: ユーザーが複数のGoogleアカウントにログインしている場合は？**  
A: Google One Tap のアカウント選択ダイアログが表示されます。

**Q: Googleにログインしていないユーザーは？**  
A: 5秒後に「Googleでサインイン」ボタンが表示されます。

**Q: 新しいパートナーが追加されてもすぐ反映される？**  
A: `generate.py` を実行してプッシュするまでは反映されません（手動更新が必要）。
