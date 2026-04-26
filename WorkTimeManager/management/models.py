# from django.db import models

# Create your models here.
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

class Category(models.Model):
    name = models.CharField('カテゴリ名', max_length=100)
    def __str__(self): return self.name

class Project(models.Model):
    name = models.CharField('案件名', max_length=200)
    def __str__(self): return self.name

class WorkLog(models.Model):
    date = models.DateField('作業日')
    start_time = models.TimeField('開始時刻')
    end_time = models.TimeField('終了時刻')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name='カテゴリ')
    project = models.ForeignKey(Project, on_delete=models.PROTECT, verbose_name='案件名')
    content = models.TextField('作業内容')
    redmine_no = models.IntegerField('Redmine番号', blank=True, null=True)
    remarks = models.TextField('備考', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def working_hours(self):
        """開始時刻と終了時刻から作業時間を計算する（翌日0時を過ぎる場合対応）"""
        seconds = self.working_seconds
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours:d}:{minutes:02d}"

    @property
    def working_seconds(self):
        """作業時間を秒単位で返す"""
        from datetime import datetime as dt, timedelta
        start = dt.combine(dt.today(), self.start_time)
        end = dt.combine(dt.today(), self.end_time)

        if end < start:
            end += timedelta(days=1)

        return int((end - start).total_seconds())

    def __str__(self):
        return f"{self.date} {self.project.name}"


@receiver(post_save, sender=Category)
@receiver(post_save, sender=Project)
def update_json_on_save(sender, instance, **kwargs):
    """カテゴリまたは案件を作成・更新したときに JSON を更新する"""
    from .views import save_data_to_json
    save_data_to_json()


@receiver(post_delete, sender=Category)
@receiver(post_delete, sender=Project)
def update_json_on_delete(sender, instance, **kwargs):
    """カテゴリまたは案件を削除したときに JSON を更新する"""
    from .views import save_data_to_json
    save_data_to_json()
