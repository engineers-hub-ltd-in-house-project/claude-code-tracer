# Claude Code Tracer - セットアップガイド

## 前提条件

### 必須要件

- **Python**: 3.13以上
- **Claude CLI**: インストール済みで動作可能
- **OS**: Linux、macOS、またはWSL2（Windows）

### 推奨環境

- **パッケージマネージャー**: uv（高速）またはpoetry
- **ターミナル**: 256色対応の最新ターミナル

## インストール手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/claude-code-tracer.git
cd claude-code-tracer
```

### 2. Python環境のセットアップ

#### 方法A: uv を使用（推奨）

```bash
# uvのインストール（まだの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# プロジェクトのインストール
uv pip install -e .

# 開発環境の場合
uv pip install -e ".[dev]"
```

#### 方法B: poetry を使用

```bash
# poetryのインストール（まだの場合）
curl -sSL https://install.python-poetry.org | python3 -

# 依存関係のインストール
poetry install

# 仮想環境の有効化
poetry shell
```

#### 方法C: pip を使用

```bash
# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Linux/macOS
# または
venv\Scripts\activate  # Windows

# 依存関係のインストール
pip install -r requirements.txt
```

### 3. 環境設定

#### ローカルストレージモード（デフォルト）

特別な設定は不要です。セッションは`./sessions/`ディレクトリに自動的に保存されます。

```bash
# sessionsディレクトリが自動作成されます
python claude_tracer.py
```

#### Supabaseモード（オプション）

Supabaseを使用する場合：

1. `.env`ファイルの作成:
```bash
cp .env.example .env
```

2. `.env`ファイルの編集:
```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Privacy Settings
PRIVACY_MODE=strict  # strict, moderate, minimal
```

3. Supabaseプロジェクトの設定:
```sql
-- データベーステーブルの作成（Supabase SQL Editor で実行）
CREATE TABLE claude_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR UNIQUE NOT NULL,
    user_id UUID REFERENCES auth.users(id),
    project_path TEXT,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    status VARCHAR DEFAULT 'active',
    total_interactions INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE claude_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES claude_sessions(id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL,
    message_type VARCHAR NOT NULL,
    user_prompt TEXT,
    claude_response TEXT,
    timestamp TIMESTAMPTZ NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- インデックスの作成
CREATE INDEX idx_sessions_user_id ON claude_sessions(user_id);
CREATE INDEX idx_sessions_created_at ON claude_sessions(created_at);
CREATE INDEX idx_interactions_session_id ON claude_interactions(session_id);
```

### 4. プライバシー設定（オプション）

カスタムパターンを追加する場合は`config/privacy.yml`を編集：

```yaml
# config/privacy.yml
custom_patterns:
  - name: "社内APIキー"
    pattern: 'COMPANY_API_[A-Z0-9]+'
    replacement: "[COMPANY_API]"
    level: HIGH
    
  - name: "社内サーバー"
    pattern: '([a-z]+\.)?internal\.company\.com'
    replacement: "[INTERNAL_SERVER]"
    level: MEDIUM
```

## 動作確認

### 1. 基本的な動作確認

```bash
# ヘルプの表示
python claude_tracer.py --help

# Claude CLIが正しく検出されるか確認
which claude
```

### 2. テスト実行

```bash
# Claude CLIの監視を開始
python claude_tracer.py

# 別のターミナルでセッションを確認
python view_session.py --list
```

### 3. プライバシー機能のテスト

```bash
# プライバシーガードのテスト
python -m claude_code_tracer.core.privacy --test

# サンプルテキスト：
# API_KEY=sk-ant-api03-1234567890
# email: test@example.com
```

## トラブルシューティング

### Claude CLIが見つからない

```bash
# PATHの確認
echo $PATH

# Claudeの場所を探す
find / -name "claude" 2>/dev/null

# パスを指定して実行
python claude_tracer.py --command /path/to/claude
```

### 権限エラー

```bash
# 実行権限の付与
chmod +x claude_tracer.py
chmod +x view_session.py

# sessionsディレクトリの権限
chmod 755 sessions/
```

### Python依存関係の問題

```bash
# 依存関係の再インストール
pip install --upgrade -r requirements.txt

# または
uv pip sync requirements.txt
```

### Supabase接続エラー

1. `.env`ファイルの内容を確認
2. Supabase URLとキーが正しいか確認
3. ファイアウォール設定を確認

## 次のステップ

セットアップが完了したら：

1. [使用方法](usage.md)を読んで基本的な使い方を学ぶ
2. [アーキテクチャ](architecture.md)でシステムの仕組みを理解する
3. [開発ガイド](development.md)で拡張方法を学ぶ

## サポート

問題が解決しない場合：

- [Issues](https://github.com/yourusername/claude-code-tracer/issues)に報告
- [Discussions](https://github.com/yourusername/claude-code-tracer/discussions)で質問