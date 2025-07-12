# Claude Code Tracer - 使用方法

## 基本的な使い方

### 1. Claude CLIの監視を開始

最も簡単な使い方：

```bash
$ python claude_tracer.py
```

これで以下のような画面が表示されます：

```
⚠️  Using local storage mode (no Supabase configured)
   Sessions will be saved to ./sessions/
🚀 Claude Code Tracer - PTY Monitor
==================================================
📝 Session ID: pty-20250712-223357
📁 Logs saved to: sessions/pty-20250712-223357.json
==================================================
Starting claude...

[Claude CLIが起動し、通常通り使用できます]
```

### 2. セッションの表示

#### セッション一覧を見る

```bash
$ python view_session.py --list

📂 Available Sessions:
----------------------------------------------------------------------
1. pty-20250712-223357.json
   Time: 2025-07-12 22:33:57 | Interactions: 2 | Status: completed
2. pty-20250712-221234.json
   Time: 2025-07-12 22:12:34 | Interactions: 5 | Status: completed
3. pty-20250712-215678.json
   Time: 2025-07-12 21:56:78 | Interactions: 10 | Status: completed
```

#### 特定のセッションを詳しく見る

```bash
$ python view_session.py pty-20250712-223357.json

🔍 Claude Code Tracer Session Viewer
======================================================================
📋 Session ID: pty-20250712-223357
📁 Project: /home/user/my-project
🕐 Start: 2025-07-12 22:33:57
🕑 End: 2025-07-12 22:34:33
📊 Total interactions: 2
🔧 Monitor type: pty
======================================================================

### Interaction 1 [2025-07-12 22:34:08]
----------------------------------------------------------------------
👤 USER:
   Pythonでフィボナッチ数列を生成する関数を書いて

🤖 CLAUDE:
   フィボナッチ数列を生成する関数をいくつかの方法で実装します。

   def fibonacci_iterative(n):
       """反復処理でn番目までのフィボナッチ数列を生成"""
       if n <= 0:
           return []
       elif n == 1:
           return [0]
       
       fib = [0, 1]
       for i in range(2, n):
           fib.append(fib[i-1] + fib[i-2])
       return fib[:n]
----------------------------------------------------------------------
```

## 高度な使い方

### デバッグモード

問題が発生した場合、デバッグモードで詳細情報を記録：

```bash
$ python claude_tracer.py --debug

⚠️  Using local storage mode (no Supabase configured)
   Sessions will be saved to ./sessions/
🚀 Claude Code Tracer - PTY Monitor
==================================================
📝 Session ID: pty-20250712-230000
📁 Logs saved to: sessions/pty-20250712-230000.json
🐛 Debug logs: sessions/debug-20250712-230000.log
==================================================
Starting claude...
```

デバッグログの確認：
```bash
$ tail -f sessions/debug-20250712-230000.log
```

### 別のコマンドを監視

Claude CLI以外のコマンドも監視できます：

```bash
# Pythonインタープリタを監視
$ python claude_tracer.py --command python

# 特定のパスのコマンドを監視
$ python claude_tracer.py --command /usr/local/bin/claude
```

### セッションの検索とフィルタリング

```bash
# 今日のセッションだけを表示
$ python view_session.py --list --today

# 特定のプロジェクトのセッションを検索
$ python view_session.py --list --project /home/user/my-project

# 長いセッション（10以上のインタラクション）を表示
$ python view_session.py --list --min-interactions 10
```

## プライバシー設定

### プライバシーモードの変更

`.env`ファイルで設定：

```env
# strict: すべての疑わしいパターンをマスク（デフォルト）
PRIVACY_MODE=strict

# moderate: 確実な機密情報のみマスク
PRIVACY_MODE=moderate

# minimal: 最小限のマスキング
PRIVACY_MODE=minimal
```

### カスタムパターンの追加

`config/privacy.yml`を編集：

```yaml
custom_patterns:
  # 社内のプロジェクトコード
  - name: "Project Code"
    pattern: 'PRJ-[0-9]{4}'
    replacement: "[PROJECT_CODE]"
    level: MEDIUM
    
  # 内部サーバー名
  - name: "Internal Server"
    pattern: 'srv[0-9]{2}\.internal\.com'
    replacement: "[INTERNAL_SERVER]"
    level: HIGH
```

### プライバシー機能のテスト

```bash
# 対話形式でテスト
$ python -m claude_code_tracer.core.privacy --test

# ファイルでテスト
$ python -m claude_code_tracer.core.privacy --test-file sample.txt
```

## セッションのエクスポート

### Markdown形式でエクスポート

```bash
# 単一セッションをMarkdownに
$ python export_session.py pty-20250712-223357.json --format markdown

# 複数セッションを一括エクスポート
$ python export_session.py --all --format markdown --output exported/
```

### JSON形式でエクスポート（バックアップ用）

```bash
# プライバシー情報を含めてエクスポート
$ python export_session.py --all --format json --include-raw

# クリーンなエクスポート（マスキング済みのみ）
$ python export_session.py --all --format json
```

## Supabaseとの連携

### リアルタイム同期の有効化

`.env`ファイルに適切な認証情報を設定後：

```bash
$ python claude_tracer.py

✅ Supabase configured: https://your-project.supabase.co
🚀 Claude Code Tracer - PTY Monitor
==================================================
📝 Session ID: pty-20250712-223357
📁 Syncing to Supabase in real-time
==================================================
Starting claude...
```

### Supabaseからセッションを取得

```bash
# 最新のセッションを同期
$ python sync_sessions.py --pull

# 特定の日付範囲のセッションを取得
$ python sync_sessions.py --pull --from 2025-07-01 --to 2025-07-12
```

## 実用的な使用例

### 1. 日々の開発作業の記録

```bash
# 朝、作業開始時に起動
$ python claude_tracer.py

# 一日の終わりにセッションを確認
$ python view_session.py --list --today

# 重要なセッションをMarkdownでエクスポート
$ python export_session.py pty-20250712-*.json --format markdown
```

### 2. チームでのナレッジ共有

```bash
# Supabaseを使って自動同期
$ python claude_tracer.py  # メンバーA

# 別のメンバーがセッションを確認
$ python sync_sessions.py --pull  # メンバーB
$ python view_session.py --list --user member-a
```

### 3. 学習内容の振り返り

```bash
# 特定のトピックを含むセッションを検索
$ grep -l "machine learning" sessions/*.json | xargs python view_session.py

# 週次レポートの生成
$ python generate_report.py --week --format markdown > weekly_report.md
```

## Tips & Tricks

### 1. エイリアスの設定

`.bashrc`や`.zshrc`に追加：

```bash
alias ct='python ~/claude-code-tracer/claude_tracer.py'
alias cts='python ~/claude-code-tracer/view_session.py'
```

### 2. 自動起動の設定

```bash
# tmuxでの自動起動
echo "python ~/claude-code-tracer/claude_tracer.py" >> ~/.tmux.conf
```

### 3. セッションの自動バックアップ

```bash
# cronジョブの設定（毎日午後11時にバックアップ）
0 23 * * * tar -czf ~/backups/claude-sessions-$(date +\%Y\%m\%d).tar.gz ~/claude-code-tracer/sessions/
```

## トラブルシューティング

### セッションが記録されない

1. デバッグモードで実行して詳細を確認
2. Claude CLIが正しく起動しているか確認
3. ディスク容量を確認

### 文字化けが発生する

1. ターミナルの文字コード設定を確認（UTF-8推奨）
2. `LANG`環境変数を確認
3. ターミナルエミュレータの設定を確認

### パフォーマンスの問題

1. 古いセッションファイルをアーカイブ
2. デバッグモードを無効化
3. ローカルストレージの代わりにSupabaseを使用

## 次のステップ

- [アーキテクチャ](architecture.md) - 内部動作の理解
- [API仕様](api.md) - プログラマティックな使用
- [開発ガイド](development.md) - 機能拡張の方法