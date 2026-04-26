# 作業時間管理Webアプリ

Djangoで実装された作業時間管理Webアプリケーションです。

## 機能

- **ワークログ管理**
  - 作業日、開始時刻、終了時刻の記録
  - タスクカテゴリの選択（テーブルで管理）
  - 案件名の選択（テーブルで管理）
  - 作業内容の詳細入力
  - Redmine番号の記録（オプション）
  - 備考の追加

- **CRUD機能**
  - ワークログの新規作成
  - 一覧表示（日付フィルタリング可）
  - ワークログの編集
  - ワークログの削除

- **管理画面**
  - Django標準の管理画面でカテゴリと案件名を管理

## セットアップ手順

### 1. 仮想環境の作成と有効化

```bash
# Pythonのバージョン確認（Python 3.8以上推奨）
python --version

# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化（Windows）
venv\Scripts\activate

# 仮想環境の有効化（Mac/Linux）
source venv/bin/activate
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. マイグレーション実行

```bash
cd WorkTimeManager
python manage.py migrate
```

マイグレーション実行時に以下のメッセージが出ますが、これは無視して問題ありません：
```
WARNINGS:
management.Category: (models.W042) Auto-created primary key used when not defini
ng a primary key type...
```

### 4. 管理画面用スーパーユーザー作成（初回のみ）

```bash
python manage.py createsuperuser
```

実行すると以下のプロンプトが表示されます：
- Username: (ユーザー名を入力)
- Email address: (メールアドレスを入力)
- Password: (パスワードを入力)
- Password (again): (パスワードを再入力)

### 5. 開発サーバー起動

```bash
python manage.py runserver
```

ブラウザで以下のURLにアクセスしてください：
- **メインページ**: http://localhost:8000/
- **管理画面**: http://localhost:8000/admin/

## 使用方法

### ワークログの作成

1. メインページ (http://localhost:8000/) にアクセス
2. 「新規作成」ボタンをクリック
3. 以下の情報を入力：
   - 作業日
   - 開始時刻
   - 終了時刻
   - カテゴリ（カテゴリが存在しない場合、管理画面で先に作成）
   - 案件名（案件名が存在しない場合、管理画面で先に作成）
   - 作業内容
   - Redmine番号（オプション）
   - 備考（オプション）
4. 「保存」ボタンをクリック

### ワークログの閲覧・フィルター

1. メインページでワークログの一覧を表示
2. 「フィルター」セクションで日付を指定してフィルター可能
3. 「作成」「編集」「削除」ボタンで各操作を実行

### カテゴリ・案件名の管理

1. 管理画面 (http://localhost:8000/admin/) にアクセス
2. ユーザー名とパスワードで認証
3. 「Management」セクション下の「Category」または「Project」をクリック
4. 追加・編集・削除が可能

## ファイル構造

```
WorkTimeManager/
├── manage.py
├── db.sqlite3
├── WorkTimeManager/
│   ├── settings.py       # Django設定
│   ├── urls.py           # URL設定
│   ├── asgi.py
│   └── wsgi.py
└── management/
    ├── models.py         # データモデル
    ├── views.py          # ビュー
    ├── urls.py           # アプリのURL設定
    ├── admin.py          # 管理画面設定
    ├── migrations/       # マイグレーションファイル
    └── templates/
        └── management/
            ├── base.html                    # ベーステンプレート
            ├── worklog_list.html            # ワークログ一覧
            ├── worklog_form.html            # 新規作成・編集フォーム
            └── worklog_confirm_delete.html  # 削除確認画面
```

## データベーススキーマ

### Category（カテゴリ）
| カラム | 型 |
|--------|-----|
| id | Integer (PK) |
| name | CharField(100) |

### Project（案件名）
| カラム | 型 |
|--------|-----|
| id | Integer (PK) |
| name | CharField(200) |

### WorkLog（作業ログ）
| カラム | 型 |
|--------|-----|
| id | Integer (PK) |
| date | DateField |
| start_time | TimeField |
| end_time | TimeField |
| category_id | ForeignKey(Category) |
| project_id | ForeignKey(Project) |
| content | TextField |
| redmine_no | Integer (NULL許可) |
| remarks | TextField (空欄許可) |
| created_at | DateTimeField (自動設定) |

## トラブルシューティング

### テンプレートが見つからないエラー
- templates/managementディレクトリが正しく作成されているか確認
- Django設定ファイルのAPP_DIRSが Trueに設定されているか確認

### ポート8000が既に使用中
```bash
# 別のポート（例：8001）で実行
python manage.py runserver 8001
```

### データベース エラー
```bash
# マイグレーションをリセット（開発環境でのみ）
rm db.sqlite3
python manage.py migrate
```

## 今後の拡張予定

- [ ] CSVエクスポート機能
- [ ] 日報レポート自動生成
- [ ] ユーザー管理機能
- [ ] 複数ユーザー対応
- [ ] API追加（REST API）
- [ ] テスト機能

## ライセンス

MIT License
