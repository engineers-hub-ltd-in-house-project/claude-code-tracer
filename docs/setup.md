# Claude Code Tracer - セットアップガイド

このガイドでは、Claude Code Tracer の環境構築から初期設定までを説明します。

## 前提条件

### 必須要件
- **Python**: 3.13 以上
- **Docker**: 20.10 以上
- **Docker Compose**: 2.0 以上
- **Claude Code**: インストール済み（`claude` コマンドが使用可能）
- **Supabase アカウント**: [https://supabase.com](https://supabase.com) で作成

### 推奨環境
- **OS**: macOS 13+, Ubuntu 22.04+, Windows 11 (WSL2)
- **メモリ**: 8GB 以上
- **ストレージ**: 10GB 以上の空き容量

## インストール手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-org/claude-code-tracer.git
cd claude-code-tracer
```

### 2. 環境変数の設定

環境変数テンプレートをコピーして編集:

```bash
cp .env.example .env
```

`.env` ファイルを開いて、以下の必須項目を設定:

```env
# Supabase 設定（必須）
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Claude/Anthropic 設定（必須）
ANTHROPIC_API_KEY=your-anthropic-api-key

# アプリケーション設定
SECRET_KEY=$(openssl rand -hex 32)  # 生成したキーを設定
```

### 3. Supabase プロジェクトの設定

#### 3.1 Supabase でプロジェクト作成
1. [Supabase Dashboard](https://app.supabase.com) にログイン
2. 「New Project」をクリック
3. プロジェクト名: `claude-code-tracer`
4. データベースパスワードを設定（安全に保管）
5. リージョンを選択（最寄りのリージョン推奨）

#### 3.2 API キーの取得
1. プロジェクトダッシュボード → Settings → API
2. 以下をコピー:
   - Project URL → `SUPABASE_URL`
   - anon public → `SUPABASE_KEY`
   - service_role → `SUPABASE_SERVICE_ROLE_KEY`

#### 3.3 データベーススキーマの適用
```bash
# スキーマ作成スクリプトを実行
python scripts/setup_db.py
```

### 4. 依存関係のインストール

#### Poetry を使用する場合（推奨）
```bash
# Poetry のインストール（未インストールの場合）
curl -sSL https://install.python-poetry.org | python3 -

# 依存関係のインストール
poetry install
```

#### pip を使用する場合
```bash
# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements-dev.txt
```

### 5. 開発環境の起動

#### Docker Compose を使用（推奨）
```bash
# 開発環境の起動
make docker-up

# ログの確認
make docker-logs
```

#### ローカル実行
```bash
# API サーバーの起動
make dev-api

# 別ターミナルで監視サービスの起動
make dev-monitor
```

## 初期設定

### 1. 動作確認

```bash
# API の動作確認
curl http://localhost:8000/health

# 期待される応答:
# {"status": "healthy", "version": "0.1.0"}
```

### 2. Claude Code との連携確認

```bash
# Claude Code Tracer を起動
claude-tracer start

# Claude Code を通常通り使用
claude "Create a simple Python function"

# セッション情報の確認
claude-tracer sessions list
```

### 3. Web ダッシュボードへのアクセス

ブラウザで [http://localhost:8000](http://localhost:8000) にアクセス

## トラブルシューティング

### よくある問題と解決方法

#### 1. Supabase 接続エラー
```
Error: Unable to connect to Supabase
```
**解決方法:**
- `.env` ファイルの Supabase 設定を確認
- ネットワーク接続を確認
- Supabase プロジェクトのステータスを確認

#### 2. Claude Code が検出されない
```
Error: Claude Code not found
```
**解決方法:**
- Claude Code がインストールされているか確認: `which claude`
- PATH に Claude Code が含まれているか確認
- `ANTHROPIC_API_KEY` が設定されているか確認

#### 3. Docker 関連のエラー
```
Error: Cannot connect to Docker daemon
```
**解決方法:**
- Docker Desktop が起動しているか確認
- Docker サービスの再起動: `sudo systemctl restart docker`
- ユーザーが docker グループに属しているか確認

### ログの確認

```bash
# アプリケーションログ
tail -f logs/claude-tracer.log

# Docker コンテナログ
docker-compose logs -f api

# システムログレベルの変更
export LOG_LEVEL=DEBUG
```

## 次のステップ

1. [開発ガイド](development.md) を読んで開発を開始
2. [API ドキュメント](api.md) で利用可能な API を確認
3. [アーキテクチャ](architecture.md) でシステム設計を理解

## サポート

問題が解決しない場合:
- [Issue Tracker](https://github.com/your-org/claude-code-tracer/issues) で報告
- [Discussions](https://github.com/your-org/claude-code-tracer/discussions) で質問