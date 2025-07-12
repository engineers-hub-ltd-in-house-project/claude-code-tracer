# Claude Code Tracer - アーキテクチャ設計

## 概要

Claude Code TracerはPTY（Pseudo-Terminal）を使用して、Claude CLIセッションを透過的に監視・記録するシステムです。

## システム構成

```
┌────────────────────────────────────────────────────────────────┐
│                        User Terminal                           │
│                              │                                 │
│                              ▼                                 │
│                    ┌─────────────────┐                        │
│                    │ claude_tracer.py│                        │
│                    └────────┬────────┘                        │
│                             │                                 │
│                    ┌────────▼────────┐                        │
│                    │   PTY Monitor   │                        │
│                    │  (pty_monitor)  │                        │
│                    └────────┬────────┘                        │
│                             │                                 │
│         ┌───────────────────┼───────────────────┐            │
│         │                   │                   │            │
│         ▼                   ▼                   ▼            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Claude CLI   │  │   Privacy    │  │   Session    │      │
│  │  (claude)    │  │    Guard     │  │   Storage    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                               │              │
│                                    ┌──────────┴──────────┐   │
│                                    │                     │   │
│                             ┌──────▼──────┐      ┌──────▼──────┐
│                             │    Local    │      │  Supabase   │
│                             │   Storage   │      │   Storage   │
│                             └─────────────┘      └─────────────┘
└────────────────────────────────────────────────────────────────┘
```

## コンポーネント詳細

### 1. PTY Monitor (`pty_monitor.py`)

PTYを使用してClaude CLIプロセスを透過的に監視するコアコンポーネント。

**主な機能:**
- 擬似端末（PTY）の作成と管理
- 標準入出力のインターセプト
- ANSIエスケープシーケンスの処理
- リアルタイムでのセッション記録

**技術詳細:**
```python
# PTYの作成
master_fd, slave_fd = pty.openpty()

# Claude CLIプロセスの起動
process = subprocess.Popen(
    [command],
    stdin=slave_fd,
    stdout=slave_fd,
    stderr=slave_fd,
    preexec_fn=os.setsid
)

# 入出力の監視ループ
while True:
    r, w, e = select.select([sys.stdin, master_fd], [], [], 0.1)
    # 処理...
```

### 2. Privacy Guard (`privacy.py`)

機密情報を自動的に検出してマスキングするセキュリティコンポーネント。

**検出パターン:**
- APIキー（OpenAI、Anthropic、GitHub等）
- データベース接続文字列
- 個人情報（メールアドレス、電話番号）
- クレジットカード番号
- IPアドレス
- パスワード

**マスキング例:**
```
入力: "sk-ant-api03-1234567890abcdef"
出力: "[ANTHROPIC_API_KEY]"
```

### 3. Session Storage

セッション情報の永続化を管理。

**ローカルストレージ:**
- JSON形式でファイルに保存
- `./sessions/`ディレクトリに格納
- ファイル名: `pty-YYYYMMDD-HHMMSS.json`

**Supabaseストレージ:**
- リアルタイム同期
- Row Level Security (RLS)
- バックアップとレプリケーション

## データフロー

### 1. ユーザー入力の流れ

```
User Keyboard → stdin → PTY Monitor → Claude CLI
                           ↓
                    Session Recording
```

### 2. Claude応答の流れ

```
Claude CLI → PTY Monitor → stdout → User Terminal
                ↓
         Privacy Guard
                ↓
         Session Storage
```

### 3. セッション記録の流れ

```
1. ユーザーがコマンドを入力
2. PTY Monitorが入力をキャプチャ
3. Claude CLIに入力を転送
4. Claude CLIの応答をキャプチャ
5. ANSIエスケープシーケンスを除去
6. Privacy Guardで機密情報をマスキング
7. セッションストレージに保存
```

## セキュリティ設計

### 1. プライバシー保護

- **多層防御**: 複数のパターンマッチングで機密情報を検出
- **設定可能なレベル**: strict/moderate/minimal
- **カスタムパターン**: `config/privacy.yml`で追加可能

### 2. データ保護

- **ローカル保存**: ファイルシステムの権限で保護
- **Supabase**: RLS（Row Level Security）で保護
- **転送時暗号化**: HTTPS/TLS使用

### 3. アクセス制御

- **ローカル**: OSのファイルシステム権限
- **Supabase**: 認証トークンベース

## パフォーマンス最適化

### 1. リアルタイム処理

- **非ブロッキングI/O**: `select()`を使用
- **バッファリング**: 効率的な出力処理
- **最小限の遅延**: 透過的な操作を実現

### 2. メモリ使用

- **ストリーミング処理**: 大きな出力も効率的に処理
- **定期的なフラッシュ**: メモリ使用量を抑制

## 拡張性

### 1. プラグインアーキテクチャ

将来的な拡張のための設計：

```python
class MonitorPlugin:
    def on_user_input(self, text: str) -> str:
        pass
    
    def on_assistant_output(self, text: str) -> str:
        pass
    
    def on_session_end(self, session: Session):
        pass
```

### 2. ストレージプロバイダー

新しいストレージバックエンドを追加可能：

```python
class StorageProvider(ABC):
    @abstractmethod
    async def save_session(self, session: Session):
        pass
    
    @abstractmethod
    async def load_session(self, session_id: str) -> Session:
        pass
```

## エラーハンドリング

### 1. プロセス監視

- Claude CLIプロセスの異常終了を検出
- セッションの適切な終了処理

### 2. ストレージエラー

- ローカル保存失敗時の再試行
- Supabase接続エラー時のフォールバック

### 3. ユーザー割り込み

- Ctrl+C、Ctrl+Dの適切な処理
- セッションデータの保全

## 今後の拡張計画

### Phase 1（現在）
- ✅ PTYベースの透過的監視
- ✅ ローカルストレージ
- ✅ 基本的なプライバシー保護

### Phase 2
- [ ] Supabaseリアルタイム同期
- [ ] Web UIダッシュボード
- [ ] セッション分析機能

### Phase 3
- [ ] AIによる自動要約
- [ ] チーム共有機能
- [ ] プラグインシステム