# クイックスタートガイド

作業時間管理Webアプリをすぐに使い始めるためのガイドです。

## ステップ1: 環境准備（初回のみ）

### Windows PowerShell を開く

プロジェクトディレクトリで PowerShell を起動：

```powershell
# TimeManagerプロジェクトディレクトリに移動
cd p:\TimeManager

# 仮想環境の作成
python -m venv venv

# 仮想環境を有効化
.\venv\Scripts\Activate.ps1

# 依存パッケージをインストール
pip install django
```

## ステップ2: データベース初期化（初回のみ）

```powershell
cd WorkTimeManager

# management_categoryテーブル作成
python manage.py makemigrations management

# マイグレーション実行
python manage.py migrate

# スーパーユーザー（管理者）を作成
python manage.py createsuperuser
# プロンプトに従ってユーザー名、メール、パスワードを入力

```

## ステップ3: サーバー起動

```powershell
# WorkTimeManager ディレクトリで以下を実行
python manage.py runserver
```

出力例：
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

## ステップ4: ブラウザでアクセス

### メインアプリケーション
```
http://localhost:8000/
```

### 管理画面（カテゴリ・案件名管理）
```
http://localhost:8000/admin/
```
- ユーザー名：作成したスーパーユーザーのもの
- パスワード：設定したパスワード

## 日常の使用フロー

毎日の起動：

```powershell
cd p:\TimeManager

# 仮想環境を有効化（前のセッションから続けている場合は不要）
.\venv\Scripts\Activate.ps1

# WorkTimeManager ディレクトリに移動
cd WorkTimeManager

# サーバーを起動
python manage.py runserver
```

## トラブルシューティング

### 「python: コマンドが見つかりません」エラー

```powershell
# Python がインストールされているか確認
python --version

# または
py --version
```

解決策：Python をインストールまたはパスを設定

### 仮想環境が有効にならない

```powershell
# 実行ポリシーを確認
Get-ExecutionPolicy

# 必要に応じて変更（管理者権限が必要）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### ポート 8000 が既に使用中

```powershell
# 別のポートで起動
python manage.py runserver 8080
# または
python manage.py runserver 0.0.0.0:9000
```

## ファイル説明

| ファイル | 目的 |
|---------|------|
| `manage.py` | Django プロジェクト管理ツール |
| `WorkTimeManager/` | Django 設定ディレクトリ |
| `management/` | アプリケーション本体 |
| `db.sqlite3` | SQLite データベース |
| `create_test_data.py` | テストデータ作成スクリプト |

## よくある質問

### Q: データベースをリセットしたい

```powershell
# db.sqlite3 を削除
Remove-Item db.sqlite3

# マイグレーション再実行
python manage.py migrate

# 管理者ユーザー再作成
python manage.py createsuperuser
```

### Q: 新しいカテゴリや案件名を追加したい

1. ブラウザで http://localhost:8000/admin/ にアクセス
2. 上記で作成したユーザー名/パスワードでログイン
3. Management セクションの Category または Project から追加

### Q: ワークログを一括削除したい

```powershell
# Django シェルで実行
python manage.py shell
>>> from management.models import WorkLog
>>> WorkLog.objects.all().delete()
>>> exit()
```

## 次のステップ

- README.md を参照して詳細な機能説明を確認
- 管理画面で初期データ（カテゴリ、案件名）を設定
- 実際にワークログを作成・管理してアプリを試す

---

質問や問題がある場合は、README.md のトラブルシューティングセクションを参照してください。
