#!/usr/bin/env python
"""
テストデータを作成するためのスクリプト
WorkTimeManager/manage.py shell で以下を実行:
"""

import os
import django

# Django設定の初期化
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WorkTimeManager.settings')
django.setup()

from management.models import Category, Project

# 既存データをクリアしない場合は、下のコメントアウトを外す
# Category.objects.all().delete()
# Project.objects.all().delete()

# テスト用のカテゴリを作成
categories = [
    'バグ修正',
    '新機能開発',
    'テスト',
    'ドキュメント作成',
    'リファクタリング',
    '保守',
    ' 会議',
]

for category in categories:
    obj, created = Category.objects.get_or_create(name=category)
    if created:
        print(f'カテゴリ作成: {category}')
    else:
        print(f'カテゴリ既存: {category}')

# テスト用の案件名を作成
projects = [
    'プロジェクトA',
    'プロジェクトB',
    'プロジェクトC',
    '基盤技術チーム',
    'インフラストラクチャ',
]

for project in projects:
    obj, created = Project.objects.get_or_create(name=project)
    if created:
        print(f'案件名作成: {project}')
    else:
        print(f'案件名既存: {project}')

print('テストデータの作成が完了しました。')
