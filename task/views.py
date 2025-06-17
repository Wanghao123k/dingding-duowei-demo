import json
import logging

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_http_methods

from .models import Task
from .forms import TaskForm

# 配置日志
logger = logging.getLogger(__name__)

def task_list(request):
    """任务列表视图"""
    search_query = request.GET.get('search', '')
    tasks = Task.objects.all()

    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # 计算统计信息
    total_tasks = Task.objects.count()
    completed_count = Task.objects.filter(is_completed=True).count()
    pending_count = total_tasks - completed_count
    completion_rate = round((completed_count / total_tasks * 100) if total_tasks > 0 else 0, 1)

    paginator = Paginator(tasks, 10)  # 每页显示10个任务
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_tasks': total_tasks,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'completion_rate': completion_rate,
    }
    return render(request, 'tasks/task_list.html', context)


def task_create(request):
    """创建任务视图"""
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            messages.success(request, f'任务 "{task.title}" 创建成功！')
            return redirect('task_list')
    else:
        form = TaskForm()

    context = {
        'form': form,
        'title': '创建任务'
    }
    return render(request, 'tasks/task_form.html', context)


def task_update(request, pk):
    """更新任务视图"""
    task = get_object_or_404(Task, pk=pk)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            messages.success(request, f'任务 "{task.title}" 更新成功！')
            return redirect('task_list')
    else:
        form = TaskForm(instance=task)

    context = {
        'form': form,
        'task': task,
        'title': '编辑任务'
    }
    return render(request, 'tasks/task_form.html', context)


def task_delete(request, pk):
    """删除任务视图"""
    task = get_object_or_404(Task, pk=pk)

    if request.method == 'POST':
        task_title = task.title
        task.delete()
        messages.success(request, f'任务 "{task_title}" 删除成功！')
        return redirect('task_list')

    context = {
        'task': task
    }
    return render(request, 'tasks/task_delete.html', context)


def task_detail(request, pk):
    """任务详情视图"""
    task = get_object_or_404(Task, pk=pk)
    context = {
        'task': task
    }
    return render(request, 'tasks/task_detail.html', context)

@require_http_methods(['GET', 'POST'])
def webhook_receiver(request):
    """接受第三方系统推送的数据，并立即转发到第二个钉钉地址"""
    session_id = request.GET.get('session')

    try:
        # 解析请求数据
        if request.content_type == "application/json":
            data = json.loads(request.body.decode('utf-8'))
        else:
            data = dict(request.POST)

        logger.info(f"接收到webhook数据 [Session: {session_id}]: {data}")
    except json.JSONDecodeError:
        error_msg = "JSON解析错误"
        if session_id:
            workflow_manager.fail_workflow(session_id, error_msg)
        logger.error(error_msg)
        return JsonResponse({
            'success': False,
            'message': error_msg,
            'session_id': session_id
        }, status=400)
    except Exception as e:
        error_msg = f"Webhook处理异常: {str(e)}"
        if session_id:
            workflow_manager.fail_workflow(session_id, error_msg)
        logger.error(error_msg)
        return JsonResponse({
            'success': False,
            'message': error_msg,
            'session_id': session_id
        }, status=500)