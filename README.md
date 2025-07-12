# Claude Code Tracer

> Claude Code のインタラクティブセッションを追跡・記録し、Supabase に保存する開発支援ツール

[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 概要

Claude Code Tracer は、Claude Code（Anthropic の AI コーディングアシスタント）とのインタラクションを自動的に記録・分析するシステムです。開発者の生産性向上、学習効果の可視化、チーム内でのナレッジ共有を支援します。

### 主な機能

- 🔍 **リアルタイムセッション追跡**: Claude Code の全インタラクションを自動記録
- 🛡️ **プライバシー保護**: 機密情報の自動検出・マスキング
- 📊 **使用パターン分析**: AI による開発効率の分析とインサイト生成
- 🔄 **GitHub 統合**: 自動バックアップと履歴管理
- 📈 **ダッシュボード**: Web UI による視覚的な分析結果表示
- ⚡ **リアルタイム同期**: Supabase Realtime による即時データ更新

## クイックスタート

### 前提条件

- Python 3.13 以上
- Docker & Docker Compose
- Supabase アカウント
- Claude Code CLI（インストール済み）

### インストール

```bash
# リポジトリのクローン
git clone https://github.com/your-org/claude-code-tracer.git
cd claude-code-tracer

# 環境変数の設定
cp .env.example .env
# .env ファイルを編集して必要な情報を入力

# 開発環境の起動
make dev-setup
make dev-run
```

### 基本的な使い方

```bash
# Claude Code Tracer の起動
python -m claude_code_tracer

# バックグラウンドで自動追跡開始
claude-tracer start --daemon

# セッション履歴の確認
claude-tracer sessions list

# 特定セッションの詳細表示
claude-tracer sessions show <session-id>

# Web ダッシュボードの起動
claude-tracer web
```

## システムアーキテクチャ

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Claude Code   │────│  Chat Logger    │────│    Supabase     │
│   (Terminal)    │    │     System      │    │   PostgreSQL    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │                        │
                       ┌───────┴───────┐                │
                       │               │                │
                ┌─────────────┐ ┌─────────────┐         │
                │  Background │ │  Web UI     │         │
                │   Collector │ │ Dashboard   │         │
                └─────────────┘ └─────────────┘         │
                                       │                │
                               ┌───────┴────────────────┘
                               │
                        ┌─────────────┐
                        │   GitHub    │
                        │ Integration │
                        └─────────────┘
```

## 主要コンポーネント

### 1. Session Monitor
Claude Code の実行を監視し、セッション情報をリアルタイムで収集

### 2. Privacy Guard
機密情報（API キー、パスワード、個人情報など）を自動検出してマスキング

### 3. Analytics Engine
収集データから使用パターンを分析し、開発効率の改善提案を生成

### 4. Supabase Integration
リアルタイムデータ同期とセキュアなストレージを提供

## 設定

### 環境変数

```env
# Supabase 設定
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Claude Code 設定
ANTHROPIC_API_KEY=your-api-key

# GitHub 統合（オプション）
GITHUB_TOKEN=your-personal-access-token
GITHUB_REPO=your-org/backup-repo

# アプリケーション設定
LOG_LEVEL=INFO
PRIVACY_MODE=strict  # strict | moderate | minimal
AUTO_SYNC_INTERVAL=300  # 秒単位
```

### プライバシー設定

`config/privacy.yml` でカスタムパターンを定義可能:

```yaml
custom_patterns:
  - pattern: 'COMPANY_SECRET_\w+'
    description: '社内秘密キー'
    replacement: '[COMPANY_SECRET]'
    level: MAXIMUM
```

## 開発

### プロジェクト構造

```
src/claude_code_tracer/
├── core/               # コア機能
│   ├── monitor.py     # セッション監視
│   ├── privacy.py     # プライバシー保護
│   └── analyzer.py    # データ分析
├── api/               # FastAPI エンドポイント
├── models/            # データモデル
├── services/          # 外部サービス連携
└── utils/            # ユーティリティ
```

### テスト実行

```bash
# 単体テスト
make test

# 統合テスト
make test-integration

# カバレッジレポート
make coverage
```

### コントリビューション

1. Fork してブランチを作成 (`git checkout -b feature/amazing-feature`)
2. 変更をコミット (`git commit -m 'Add amazing feature'`)
3. ブランチをプッシュ (`git push origin feature/amazing-feature`)
4. Pull Request を作成

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルをご覧ください。

## サポート

- 📚 [ドキュメント](docs/)
- 🐛 [Issue Tracker](https://github.com/your-org/claude-code-tracer/issues)
- 💬 [Discussions](https://github.com/your-org/claude-code-tracer/discussions)

## 謝辞

- [Anthropic](https://anthropic.com) - Claude Code の開発
- [Supabase](https://supabase.com) - リアルタイムデータベース基盤
- [vibe-logger](https://github.com/thierryvolpiatto/vibe-logger) - AI-native ロギングの着想