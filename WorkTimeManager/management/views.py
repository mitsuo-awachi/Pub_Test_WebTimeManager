from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from datetime import datetime, timedelta
import json
import os
import csv
import io
from .models import WorkLog, Category, Project, SubCategory


def sync_data_to_db(data):
    from .models import Category, Project, SubCategory

    # JSON のカテゴリ／案件を DB に登録または更新する
    for category in data.get('categories', []):
        Category.objects.update_or_create(
            id=category['id'],
            defaults={'name': category['name']},
        )

    for project in data.get('projects', []):
        Project.objects.update_or_create(
            id=project['id'],
            defaults={'name': project['name']},
        )

    # サブカテゴリを同期
    for subcategory in data.get('subcategories', []):
        category_id = subcategory['category_id']
        SubCategory.objects.update_or_create(
            id=subcategory['id'],
            defaults={'name': subcategory['name'], 'category_id': category_id},
        )

def save_data_to_json():
    """DBのデータをJSONファイルに保存する"""
    data_file = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'config', 'data.json'))
    
    categories = list(Category.objects.values('id', 'name').order_by('id'))
    projects = list(Project.objects.values('id', 'name').order_by('id'))
    subcategories = list(SubCategory.objects.values('id', 'name', 'category_id').order_by('id'))
    
    data = {
        'categories': categories,
        'projects': projects,
        'subcategories': subcategories,
    }
    
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data():
    data_file = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'config', 'data.json'))
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    sync_data_to_db(data)
    return data

class JsonDataRefreshMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = load_data()
        context['categories'] = data['categories']
        context['projects'] = data['projects']
        context['subcategories'] = data['subcategories']
        return context

# リスト表示ビュー
def worklog_list(request):
    worklogs = WorkLog.objects.select_related('category', 'project').all().order_by('-date')
    date_str = request.GET.get('date')
    category_id = request.GET.get('category')
    project_id = request.GET.get('project')

    if date_str:
        worklogs = worklogs.filter(date=date_str)
    else:
        # デフォルトは今月のデータを表示
        today = datetime.now().date()
        first_day = today.replace(day=1)
        worklogs = worklogs.filter(date__gte=first_day)

    if category_id:
        worklogs = worklogs.filter(category_id=category_id)
    if project_id:
        worklogs = worklogs.filter(project_id=project_id)

    data = load_data()
    category_map = {str(c['id']): c['name'] for c in data['categories']}
    project_map = {str(p['id']): p['name'] for p in data['projects']}
    subcategory_map = {str(s['id']): s['name'] for s in data['subcategories']}
    for worklog in worklogs:
        worklog.display_category_name = category_map.get(str(worklog.category_id), getattr(worklog.category, 'name', ''))
        worklog.display_project_name = project_map.get(str(worklog.project_id), getattr(worklog.project, 'name', ''))
        worklog.display_subcategory_name = subcategory_map.get(str(worklog.subcategory_id), getattr(worklog.subcategory, 'name', '')) if worklog.subcategory_id else ''

    total_seconds = sum(w.working_seconds for w in worklogs)

    context = {
        'worklogs': worklogs,
        'categories': data['categories'],
        'projects': data['projects'],
        'subcategories': data['subcategories'],
        'total_work_time': format_seconds_to_hours_minutes(total_seconds),
    }
    return render(request, 'management/worklog_list.html', context)


def format_seconds_to_hours_minutes(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours:d}:{minutes:02d}"


def monthly_summary(request):
    today = datetime.now().date()
    selected_month = request.GET.get('month') or today.strftime('%Y-%m')
    try:
        start_date = datetime.strptime(selected_month, '%Y-%m').date().replace(day=1)
    except ValueError:
        start_date = today.replace(day=1)
        selected_month = start_date.strftime('%Y-%m')

    if start_date.month == 12:
        next_month = start_date.replace(year=start_date.year + 1, month=1, day=1)
    else:
        next_month = start_date.replace(month=start_date.month + 1, day=1)

    worklogs = WorkLog.objects.select_related('project').filter(
        date__gte=start_date,
        date__lt=next_month,
    ).order_by('-date')

    total_seconds = sum(worklog.working_seconds for worklog in worklogs)
    project_totals = {}
    for worklog in worklogs:
        project_name = worklog.project.name if worklog.project else '未設定'
        project_totals.setdefault(project_name, 0)
        project_totals[project_name] += worklog.working_seconds

    project_summary = []
    for project_name, seconds in sorted(project_totals.items(), key=lambda item: item[1], reverse=True):
        project_summary.append({
            'project_name': project_name,
            'work_time': format_seconds_to_hours_minutes(seconds),
            'seconds': seconds,
            'ratio': f"{(seconds / total_seconds * 100):.1f}%" if total_seconds else '0.0%',
        })

    data = load_data()
    context = {
        'selected_month': selected_month,
        'total_work_time': format_seconds_to_hours_minutes(total_seconds),
        'worklogs_count': worklogs.count(),
        'project_summary': project_summary,
        'categories': data['categories'],
        'projects': data['projects'],
    }
    return render(request, 'management/monthly_summary.html', context)

def import_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            return render(request, 'management/import_csv.html', {'error': 'CSVファイルを選択してください。'})

        try:
            # CSVデータを読み込む
            csv_data = csv_file.read().decode('utf-8')
            csv_reader = csv.reader(io.StringIO(csv_data))

            imported_count = 0
            errors = []

            for row_num, row in enumerate(csv_reader, start=1):
                if len(row) != 8:
                    errors.append(f'行 {row_num}: 列数が正しくありません（{len(row)}列）')
                    continue

                try:
                    date_str, start_time_str, end_time_str, project_name, category_name, content, redmine_str, remarks = row

                    # 日付と時刻をパース
                    date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    start_time = datetime.strptime(start_time_str, '%H:%M').time()
                    end_time = datetime.strptime(end_time_str, '%H:%M').time()

                    # Redmine番号
                    redmine_no = int(redmine_str) if redmine_str.strip() else None

                    # 案件を取得または作成
                    project, _ = Project.objects.get_or_create(name=project_name.strip())

                    # カテゴリを取得または作成
                    category, _ = Category.objects.get_or_create(name=category_name.strip())

                    # WorkLogを作成
                    WorkLog.objects.create(
                        date=date,
                        start_time=start_time,
                        end_time=end_time,
                        project=project,
                        category=category,
                        content=content.strip(),
                        redmine_no=redmine_no,
                        remarks=remarks.strip(),
                    )

                    imported_count += 1

                except ValueError as e:
                    errors.append(f'行 {row_num}: データ形式が正しくありません - {str(e)}')
                except Exception as e:
                    errors.append(f'行 {row_num}: エラー - {str(e)}')

            # JSONファイルを更新
            save_data_to_json()

            context = {
                'success': f'{imported_count}件のデータをインポートしました。',
                'errors': errors if errors else None,
            }
            return render(request, 'management/import_csv.html', context)

        except Exception as e:
            return render(request, 'management/import_csv.html', {'error': f'ファイル処理エラー: {str(e)}'})

    return render(request, 'management/import_csv.html')

def admin_dashboard(request):
    return render(request, 'management/admin_dashboard.html')

# 新規作成ビュー
def worklog_create(request):
    if request.method == 'POST':
        try:
            worklog = WorkLog()
            worklog.date = datetime.strptime(request.POST['date'], '%Y-%m-%d').date()
            worklog.start_time = request.POST['start_time']
            end_time_str = request.POST.get('end_time')
            if end_time_str:
                worklog.end_time = end_time_str
            else:
                worklog.end_time = request.POST['start_time']
            worklog.category_id = request.POST['category']
            subcategory_id = request.POST.get('subcategory')
            worklog.subcategory_id = subcategory_id if subcategory_id else None
            worklog.project_id = request.POST['project']
            worklog.content = request.POST['content']
            worklog.redmine_no = request.POST.get('redmine_no') or None
            worklog.remarks = request.POST.get('remarks', '')
            worklog.save()
            return redirect('worklog_list')
        except Exception as e:
            data = load_data()
            context = {
                'error': str(e),
                'categories': data['categories'],
                'projects': data['projects'],
                'subcategories': data['subcategories'],
            }
            return render(request, 'management/worklog_form.html', context)
    
    data = load_data()
    context = {
        'categories': data['categories'],
        'projects': data['projects'],
        'subcategories': data['subcategories'],
        'today': datetime.now().date(),
    }
    return render(request, 'management/worklog_form.html', context)

# 編集ビュー
def worklog_update(request, pk):
    worklog = get_object_or_404(WorkLog, pk=pk)
    
    if request.method == 'POST':
        try:
            worklog.date = datetime.strptime(request.POST['date'], '%Y-%m-%d').date()
            worklog.start_time = request.POST['start_time']
            end_time_str = request.POST.get('end_time')
            if end_time_str:
                worklog.end_time = end_time_str
            else:
                worklog.end_time = request.POST['start_time']
            worklog.category_id = request.POST['category']
            subcategory_id = request.POST.get('subcategory')
            worklog.subcategory_id = subcategory_id if subcategory_id else None
            worklog.project_id = request.POST['project']
            worklog.content = request.POST['content']
            worklog.redmine_no = request.POST.get('redmine_no') or None
            worklog.remarks = request.POST.get('remarks', '')
            worklog.save()
            return redirect('worklog_list')
        except Exception as e:
            data = load_data()
            context = {
                'worklog': worklog,
                'categories': data['categories'],
                'projects': data['projects'],
                'subcategories': data['subcategories'],
                'error': str(e),
            }
            return render(request, 'management/worklog_form.html', context)
    
    data = load_data()
    context = {
        'worklog': worklog,
        'categories': data['categories'],
        'projects': data['projects'],
        'subcategories': data['subcategories'],
    }
    return render(request, 'management/worklog_form.html', context)

# 削除ビュー
def worklog_delete(request, pk):
    worklog = get_object_or_404(WorkLog, pk=pk)
    
    if request.method == 'POST':
        worklog.delete()
        return redirect('worklog_list')
    
    return render(request, 'management/worklog_confirm_delete.html', {'worklog': worklog})

# カテゴリ一覧ビュー
class CategoryListView(ListView):
    model = Category
    template_name = 'management/category_list.html'
    context_object_name = 'categories'
    ordering = ['name']

# カテゴリ作成ビュー
class CategoryCreateView(JsonDataRefreshMixin, CreateView):
    model = Category
    template_name = 'management/category_form.html'
    fields = ['name']
    success_url = reverse_lazy('category_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        save_data_to_json()  # JSONファイルを更新
        return response

# カテゴリ編集ビュー
class CategoryUpdateView(JsonDataRefreshMixin, UpdateView):
    model = Category
    template_name = 'management/category_form.html'
    fields = ['name']
    success_url = reverse_lazy('category_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        save_data_to_json()  # JSONファイルを更新
        return response

# カテゴリ削除ビュー
class CategoryDeleteView(DeleteView):
    model = Category
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('category_list')
    context_object_name = 'object'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = reverse_lazy('category_list')
        context['object_verbose_name'] = self.model._meta.verbose_name
        return context
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        save_data_to_json()  # JSONファイルを更新
        return response

# サブカテゴリ一覧ビュー
class SubCategoryListView(ListView):
    model = SubCategory
    template_name = 'management/subcategory_list.html'
    context_object_name = 'subcategories'
    ordering = ['category__name', 'name']

# サブカテゴリ作成ビュー
class SubCategoryCreateView(JsonDataRefreshMixin, CreateView):
    model = SubCategory
    template_name = 'management/subcategory_form.html'
    fields = ['name', 'category']
    success_url = reverse_lazy('subcategory_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        save_data_to_json()  # JSONファイルを更新
        return response

# サブカテゴリ編集ビュー
class SubCategoryUpdateView(JsonDataRefreshMixin, UpdateView):
    model = SubCategory
    template_name = 'management/subcategory_form.html'
    fields = ['name', 'category']
    success_url = reverse_lazy('subcategory_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        save_data_to_json()  # JSONファイルを更新
        return response

# サブカテゴリ削除ビュー
class SubCategoryDeleteView(DeleteView):
    model = SubCategory
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('subcategory_list')
    context_object_name = 'object'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = reverse_lazy('subcategory_list')
        context['object_verbose_name'] = self.model._meta.verbose_name
        return context
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        save_data_to_json()  # JSONファイルを更新
        return response

# 案件一覧ビュー
class ProjectListView(ListView):
    model = Project
    template_name = 'management/project_list.html'
    context_object_name = 'projects'
    ordering = ['name']

# 案件作成ビュー
class ProjectCreateView(JsonDataRefreshMixin, CreateView):
    model = Project
    template_name = 'management/project_form.html'
    fields = ['name']
    success_url = reverse_lazy('project_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        save_data_to_json()  # JSONファイルを更新
        return response

# 案件編集ビュー
class ProjectUpdateView(JsonDataRefreshMixin, UpdateView):
    model = Project
    template_name = 'management/project_form.html'
    fields = ['name']
    success_url = reverse_lazy('project_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        save_data_to_json()  # JSONファイルを更新
        return response

# 案件削除ビュー
class ProjectDeleteView(DeleteView):
    model = Project
    template_name = 'management/confirm_delete.html'
    success_url = reverse_lazy('project_list')
    context_object_name = 'object'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = reverse_lazy('project_list')
        context['object_verbose_name'] = self.model._meta.verbose_name
        return context
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        save_data_to_json()  # JSONファイルを更新
        return response
