# Claude Code Tracer - 開発ガイド

## 開発環境のセットアップ

### 必要なツール

- Python 3.13+
- Poetry または pip
- Docker & Docker Compose
- Git
- IDE (VS Code, PyCharm 推奨)

### 推奨 VS Code 拡張機能

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "ms-azuretools.vscode-docker",
    "redhat.vscode-yaml",
    "esbenp.prettier-vscode"
  ]
}
```

## プロジェクト構造

```
claude-code-tracer/
├── src/claude_code_tracer/     # メインパッケージ
│   ├── core/                   # コア機能
│   │   ├── monitor.py         # Claude Code 監視
│   │   ├── privacy.py         # プライバシー保護
│   │   └── analyzer.py        # データ分析
│   ├── api/                   # API エンドポイント
│   │   ├── main.py           # FastAPI アプリ
│   │   ├── routes/           # ルート定義
│   │   └── dependencies.py   # 依存性注入
│   ├── models/               # データモデル
│   │   ├── session.py       # セッションモデル
│   │   └── interaction.py   # インタラクションモデル
│   ├── services/            # サービス層
│   │   ├── supabase.py     # Supabase 連携
│   │   └── github.py       # GitHub 連携
│   └── utils/              # ユーティリティ
│       ├── config.py       # 設定管理
│       └── logging.py      # ログ設定
├── tests/                  # テスト
│   ├── unit/              # 単体テスト
│   ├── integration/       # 統合テスト
│   └── e2e/              # E2E テスト
└── scripts/              # スクリプト
    ├── setup_db.py       # DB セットアップ
    └── migrate.py        # マイグレーション
```

## コーディング規約

### Python スタイルガイド

- **フォーマッター**: Black (line-length: 88)
- **リンター**: Ruff
- **型チェック**: mypy (strict mode)
- **インポート順序**: isort

### 命名規則

```python
# クラス名: PascalCase
class SessionManager:
    pass

# 関数名・変数名: snake_case
def process_interaction(user_input: str) -> str:
    session_id = generate_session_id()
    return session_id

# 定数: UPPER_SNAKE_CASE
MAX_SESSION_DURATION = 3600
DEFAULT_PRIVACY_MODE = "strict"

# プライベートメソッド: 先頭にアンダースコア
def _validate_input(self, data: dict) -> bool:
    pass
```

### 型アノテーション

すべての関数に型アノテーションを付ける:

```python
from typing import List, Dict, Optional, Union
from datetime import datetime

async def get_sessions(
    user_id: str,
    start_date: Optional[datetime] = None,
    limit: int = 50
) -> List[Dict[str, Union[str, int, float]]]:
    """ユーザーのセッション一覧を取得"""
    pass
```

## 開発ワークフロー

### 1. ブランチ戦略

Git Flow を採用:

```bash
# 機能開発
git checkout -b feature/add-export-api

# バグ修正
git checkout -b bugfix/fix-session-timeout

# ホットフィックス
git checkout -b hotfix/security-patch
```

### 2. コミットメッセージ

Conventional Commits 形式:

```
feat: Add CSV export functionality
fix: Resolve session timeout issue
docs: Update API documentation
test: Add unit tests for privacy guard
refactor: Simplify session manager logic
chore: Update dependencies
```

### 3. Pull Request プロセス

1. ブランチを作成して変更を実装
2. テストを作成・実行
3. コードレビューのための PR 作成
4. CI チェックをパス
5. レビュー承認後にマージ

## テスト戦略

### テストの種類

#### 1. 単体テスト (Unit Tests)

```python
# tests/unit/test_privacy_guard.py
import pytest
from claude_code_tracer.core.privacy import PrivacyGuard

class TestPrivacyGuard:
    def test_detect_api_key(self):
        guard = PrivacyGuard()
        content = "My API key is sk-1234567890abcdef"
        masked, patterns = guard.scan_and_mask(content)
        
        assert "sk-1234567890abcdef" not in masked
        assert "API Key" in patterns
```

#### 2. 統合テスト (Integration Tests)

```python
# tests/integration/test_supabase_service.py
import pytest
from claude_code_tracer.services.supabase import SupabaseService

@pytest.mark.integration
class TestSupabaseService:
    async def test_create_session(self, supabase_service):
        session_data = {
            "session_id": "test-123",
            "project_path": "/test/path"
        }
        result = await supabase_service.create_session(session_data)
        
        assert result["session_id"] == "test-123"
```

#### 3. E2E テスト (End-to-End Tests)

```python
# tests/e2e/test_api_flow.py
import pytest
from httpx import AsyncClient

@pytest.mark.e2e
class TestAPIFlow:
    async def test_complete_session_flow(self, client: AsyncClient):
        # セッション作成
        response = await client.post("/api/v1/sessions", json={...})
        assert response.status_code == 201
        
        # インタラクション追加
        session_id = response.json()["session_id"]
        response = await client.post(f"/api/v1/sessions/{session_id}/interactions", json={...})
        assert response.status_code == 201
```

### テストカバレッジ

目標カバレッジ: 80% 以上

```bash
# カバレッジレポート生成
make coverage

# カバレッジ確認
coverage report
coverage html  # HTMLレポート生成
```

## デバッグ

### ログレベル設定

```python
# 環境変数で設定
LOG_LEVEL=DEBUG

# コード内で設定
import logging
logging.getLogger("claude_code_tracer").setLevel(logging.DEBUG)
```

### デバッグツール

#### 1. IPython/ipdb

```python
# ブレークポイント設定
import ipdb; ipdb.set_trace()

# または Python 3.7+
breakpoint()
```

#### 2. VS Code デバッガー

`.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "claude_code_tracer.api.main:app",
        "--reload",
        "--port", "8000"
      ],
      "env": {
        "LOG_LEVEL": "DEBUG"
      }
    }
  ]
}
```

## パフォーマンス最適化

### 1. 非同期処理

```python
import asyncio
from typing import List

async def process_sessions(session_ids: List[str]) -> List[dict]:
    """複数セッションを並行処理"""
    tasks = [process_single_session(sid) for sid in session_ids]
    return await asyncio.gather(*tasks)
```

### 2. キャッシング

```python
from functools import lru_cache
from typing import Optional
import redis

class CacheService:
    def __init__(self):
        self.redis = redis.Redis(decode_responses=True)
    
    async def get_or_set(self, key: str, factory, ttl: int = 300):
        """キャッシュまたは新規取得"""
        value = self.redis.get(key)
        if value is None:
            value = await factory()
            self.redis.setex(key, ttl, json.dumps(value))
        else:
            value = json.loads(value)
        return value
```

### 3. データベースクエリ最適化

```python
# N+1 問題の回避
sessions = await db.fetch_all(
    """
    SELECT s.*, 
           COUNT(i.id) as interaction_count
    FROM sessions s
    LEFT JOIN interactions i ON s.id = i.session_id
    WHERE s.user_id = $1
    GROUP BY s.id
    """,
    user_id
)
```

## セキュリティ

### 1. 入力検証

```python
from pydantic import BaseModel, validator

class SessionCreate(BaseModel):
    project_path: str
    
    @validator('project_path')
    def validate_path(cls, v):
        if '..' in v or v.startswith('/etc'):
            raise ValueError('Invalid path')
        return v
```

### 2. SQL インジェクション対策

```python
# 良い例: パラメータ化クエリ
await db.fetch_one(
    "SELECT * FROM sessions WHERE id = $1",
    session_id
)

# 悪い例: 文字列結合
# query = f"SELECT * FROM sessions WHERE id = '{session_id}'"
```

### 3. 機密情報の保護

```python
import os
from cryptography.fernet import Fernet

class SecretManager:
    def __init__(self):
        key = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> bytes:
        return self.cipher.encrypt(data.encode())
    
    def decrypt(self, encrypted: bytes) -> str:
        return self.cipher.decrypt(encrypted).decode()
```

## CI/CD

### GitHub Actions ワークフロー

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      - name: Run tests
        run: |
          make test
      - name: Check code quality
        run: |
          make quality
```

## トラブルシューティング

### よくある開発時の問題

#### 1. インポートエラー

```bash
# PYTHONPATH を設定
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"

# または setup.py を使用
pip install -e .
```

#### 2. 型チェックエラー

```bash
# mypy キャッシュをクリア
rm -rf .mypy_cache
mypy src
```

#### 3. テストデータベースエラー

```bash
# テスト用データベースをリセット
docker-compose down -v
docker-compose up -d postgres
python scripts/setup_db.py --test
```

## リリースプロセス

### 1. バージョン更新

```bash
# Poetry を使用
poetry version patch  # 0.1.0 -> 0.1.1
poetry version minor  # 0.1.1 -> 0.2.0
poetry version major  # 0.2.0 -> 1.0.0
```

### 2. チェンジログ更新

`CHANGELOG.md` を更新:
```markdown
## [0.2.0] - 2024-01-12
### Added
- CSV エクスポート機能
- リアルタイム通知

### Fixed
- セッションタイムアウトの問題
```

### 3. タグ作成とプッシュ

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to 0.2.0"
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin main --tags
```