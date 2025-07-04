from django import forms
from .models import Task
from .services.webhook_services import WebHookWorkFlowServices


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'code', 'description', 'is_completed']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入任务标题'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入任务代码'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '请输入任务描述（可选）'
            }),
            'is_completed': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'title': '任务标题',
            'code': '任务代码',
            'description': '任务描述',
            'is_completed': '是否完成'
        }

    def save(self, commit=True):
        # 触发推送流程
        data = {
            "code": self.instance.code,
            "rich_text_test": self.instance.title
        }
        services = WebHookWorkFlowServices(data)
        services.trigger_complete_workflow()
        return super().save(commit=commit)