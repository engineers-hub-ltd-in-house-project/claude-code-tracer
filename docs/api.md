# Claude Code Tracer - API ドキュメント

## API 概要

Claude Code Tracer は RESTful API を提供し、セッションデータの取得、分析結果の確認、設定の管理などが可能です。

**Base URL**: `http://localhost:8000/api/v1`

**認証**: Bearer Token (JWT)

## 認証

### トークン取得

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

**レスポンス:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 認証ヘッダー

すべての API リクエストに以下のヘッダーを含める:
```
Authorization: Bearer <access_token>
```

## エンドポイント

### セッション管理

#### セッション一覧取得

```http
GET /sessions
```

**クエリパラメータ:**
- `limit` (integer, default: 50): 取得件数
- `offset` (integer, default: 0): オフセット
- `status` (string): フィルタリング (active, completed, error)
- `start_date` (datetime): 開始日時フィルタ
- `end_date` (datetime): 終了日時フィルタ

**レスポンス例:**
```json
{
  "sessions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "session_id": "session-123",
      "project_path": "/home/user/project",
      "start_time": "2024-01-12T10:30:00Z",
      "end_time": "2024-01-12T11:15:00Z",
      "total_interactions": 15,
      "total_cost_usd": 0.045,
      "status": "completed"
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

#### セッション詳細取得

```http
GET /sessions/{session_id}
```

**レスポンス例:**
```json
{
  "session": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "session-123",
    "project_path": "/home/user/project",
    "start_time": "2024-01-12T10:30:00Z",
    "end_time": "2024-01-12T11:15:00Z",
    "total_interactions": 15,
    "total_cost_usd": 0.045,
    "status": "completed",
    "metadata": {
      "model": "claude-sonnet-4",
      "tools": ["Read", "Write", "Bash"]
    }
  },
  "interactions": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "message_type": "user",
      "user_prompt": "Fix the authentication bug",
      "timestamp": "2024-01-12T10:31:00Z"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440002",
      "message_type": "assistant",
      "claude_response": "I'll help you fix the authentication bug...",
      "timestamp": "2024-01-12T10:31:15Z"
    }
  ]
}
```

#### セッション削除

```http
DELETE /sessions/{session_id}
```

**レスポンス:**
```json
{
  "message": "Session deleted successfully"
}
```

### インタラクション管理

#### インタラクション検索

```http
POST /interactions/search
Content-Type: application/json

{
  "query": "authentication",
  "session_ids": ["session-123", "session-456"],
  "date_range": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z"
  },
  "limit": 20
}
```

**レスポンス例:**
```json
{
  "interactions": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440003",
      "session_id": "session-123",
      "message_type": "user",
      "user_prompt": "How do I implement JWT authentication?",
      "timestamp": "2024-01-12T10:35:00Z",
      "relevance_score": 0.95
    }
  ],
  "total_results": 5
}
```

### 分析 API

#### 使用統計取得

```http
GET /analytics/usage-stats
```

**クエリパラメータ:**
- `period` (string): 期間 (day, week, month, year)
- `start_date` (date): 開始日
- `end_date` (date): 終了日

**レスポンス例:**
```json
{
  "period": "week",
  "stats": {
    "total_sessions": 45,
    "total_interactions": 523,
    "total_cost_usd": 2.34,
    "avg_session_duration_minutes": 25.3,
    "success_rate": 0.92
  },
  "daily_breakdown": [
    {
      "date": "2024-01-08",
      "sessions": 8,
      "interactions": 95,
      "cost_usd": 0.42
    }
  ]
}
```

#### 使用パターン分析

```http
POST /analytics/usage-patterns
Content-Type: application/json

{
  "days": 30,
  "include_clustering": true,
  "include_recommendations": true
}
```

**レスポンス例:**
```json
{
  "patterns": {
    "peak_hours": [10, 11, 14, 15],
    "common_operations": [
      {"operation": "code_generation", "frequency": 0.35},
      {"operation": "debugging", "frequency": 0.28},
      {"operation": "refactoring", "frequency": 0.22}
    ],
    "topic_clusters": [
      {
        "cluster_id": 0,
        "size": 45,
        "keywords": ["authentication", "JWT", "security"],
        "sample_prompts": [
          "Implement JWT authentication",
          "Add security headers"
        ]
      }
    ]
  },
  "recommendations": [
    "Consider using code templates for authentication tasks",
    "Peak usage at 10-11 AM suggests scheduling complex tasks then"
  ]
}
```

### 設定管理

#### プライバシー設定取得

```http
GET /settings/privacy
```

**レスポンス例:**
```json
{
  "privacy_mode": "strict",
  "custom_patterns": [
    {
      "pattern": "COMPANY_KEY_\\w+",
      "description": "Company API Keys",
      "enabled": true
    }
  ],
  "whitelisted_paths": [
    "/home/user/public-projects"
  ]
}
```

#### プライバシー設定更新

```http
PUT /settings/privacy
Content-Type: application/json

{
  "privacy_mode": "moderate",
  "custom_patterns": [
    {
      "pattern": "INTERNAL_\\w+",
      "description": "Internal identifiers",
      "enabled": true
    }
  ]
}
```

### リアルタイム API

#### WebSocket 接続

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  // 認証
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'your-jwt-token'
  }));
  
  // セッション購読
  ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'sessions',
    filters: {
      status: 'active'
    }
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Realtime update:', data);
};
```

**メッセージタイプ:**
- `session_started`: 新規セッション開始
- `session_updated`: セッション更新
- `session_ended`: セッション終了
- `interaction_added`: 新規インタラクション

### エクスポート API

#### データエクスポート

```http
POST /export/sessions
Content-Type: application/json

{
  "session_ids": ["session-123", "session-456"],
  "format": "json",  // json, csv, markdown
  "include_interactions": true,
  "mask_sensitive_data": true
}
```

**レスポンス:**
```json
{
  "export_id": "export-789",
  "status": "processing",
  "estimated_time_seconds": 30,
  "download_url": null
}
```

#### エクスポート状態確認

```http
GET /export/status/{export_id}
```

**レスポンス:**
```json
{
  "export_id": "export-789",
  "status": "completed",
  "download_url": "https://downloads.example.com/export-789.json",
  "expires_at": "2024-01-13T12:00:00Z"
}
```

## エラーハンドリング

### エラーレスポンス形式

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "start_date",
      "reason": "Invalid date format"
    }
  }
}
```

### HTTP ステータスコード

- `200 OK`: 成功
- `201 Created`: リソース作成成功
- `400 Bad Request`: リクエスト不正
- `401 Unauthorized`: 認証エラー
- `403 Forbidden`: 権限エラー
- `404 Not Found`: リソース未発見
- `429 Too Many Requests`: レート制限
- `500 Internal Server Error`: サーバーエラー

## レート制限

- 認証済みユーザー: 1000 リクエスト/時間
- 未認証ユーザー: 100 リクエスト/時間

レート制限情報はレスポンスヘッダーに含まれる:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1704208800
```

## SDK サンプル

### Python
```python
from claude_code_tracer import TracerClient

client = TracerClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# セッション一覧取得
sessions = client.sessions.list(limit=10)

# 分析実行
patterns = client.analytics.usage_patterns(days=30)
```

### TypeScript
```typescript
import { TracerClient } from '@claude-code-tracer/sdk';

const client = new TracerClient({
  baseUrl: 'http://localhost:8000',
  apiKey: 'your-api-key'
});

// セッション詳細取得
const session = await client.sessions.get('session-123');

// リアルタイム購読
client.realtime.subscribe('sessions', (event) => {
  console.log('Session update:', event);
});
```