import json
import logging
import requests
import threading
import time
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render
from django.utils import timezone
from django.core.cache import cache
# 配置日志
logger = logging.getLogger(__name__)
# 工作流程状态
WORKFLOW_STATUS = {
    'IDLE': 'idle',
    'TRIGGERED': 'triggered',
    'WAITING': 'waiting',
    'PROCESSING': 'processing',
    'COMPLETED': 'completed',
    'FAILED': 'failed'
}
# 配置钉钉webhook URLs
DINGTALK_TRIGGER_URL = "https://connector.dingtalk.com/webhook/flow/10324b9677ce213c6a900000"
DINGTALK_SYNC_URL = "https://connector.dingtalk.com/webhook/flow/10324b92a742212b6b590008"

class WebHookWorkFlow:
    def __init__(self, data):
        self.current_session = None
        self.status = WORKFLOW_STATUS['IDLE']
        self.start_time = None
        self.timeout = 300  # 5分钟超时
        self.data = data

    def start_workflow(self, session_id=None):
        """启动工作流程"""
        if not session_id:
            session_id = f"workflow_{int(time.time())}"

        self.current_session = session_id
        self.status = WORKFLOW_STATUS['TRIGGERED']
        self.start_time = timezone.now()

        # 存储到缓存
        cache.set(f'webhook_workflow_status_{session_id}', {
            'status': self.status,
            'start_time': self.start_time.isoformat(),
            'session_id': session_id,
            "data": self.data
        }, timeout=self.timeout)

        logger.info(f"工作流程启动: {session_id}")
        return session_id

    def set_waiting(self, session_id):
        """设置为等待状态"""
        self.status = WORKFLOW_STATUS['WAITING']
        cache.set(f'workflow_status_{session_id}', {
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else timezone.now().isoformat(),
            'session_id': session_id,
            'waiting_since': timezone.now().isoformat(),
            "data": self.data
        }, timeout=self.timeout)
        logger.info(f"工作流程等待中: {session_id}")

    def process_callback(self, session_id):
        """处理回调数据"""
        """处理回调数据"""
        self.status = WORKFLOW_STATUS['PROCESSING']
        cache.set(f'workflow_status_{session_id}', {
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else timezone.now().isoformat(),
            'session_id': session_id,
            'processing_since': timezone.now().isoformat(),
            'received_data': True,
            "data": self.data
        }, timeout=self.timeout)
        logger.info(f"工作流程处理中: {session_id}")

    def complete_workflow(self, session_id, result):
        """完成工作流程"""
        self.status = WORKFLOW_STATUS['COMPLETED']
        cache.set(f'workflow_status_{session_id}', {
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else timezone.now().isoformat(),
            'session_id': session_id,
            'completed_at': timezone.now().isoformat(),
            'result': result,
            "data": self.data
        }, timeout=self.timeout)
        logger.info(f"工作流程完成: {session_id}")

    def fail_workflow(self, session_id, error):
        """工作流程失败"""
        self.status = WORKFLOW_STATUS['FAILED']
        cache.set(f'workflow_status_{session_id}', {
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else timezone.now().isoformat(),
            'session_id': session_id,
            'failed_at': timezone.now().isoformat(),
            'error': str(error),
            "data": self.data
        }, timeout=self.timeout)
        logger.error(f"工作流程失败: {session_id}, 错误: {error}")

    @classmethod
    def get_status(cls, session_id):
        """获取工作流程状态"""
        return cache.get(f'workflow_status_{session_id}').get('status', "")

    @classmethod
    def get_workflow(cls, session_id):
        return cache.get(f'workflow_status_{session_id}')

    def is_timeout(self, session_id):
        # status_data = self.get_status(session_id)
        # if not status_data:
        #     return True
        #
        # start_time = datetime.fromisoformat(status_data['start_time'].replace('Z', '+00:00'))
        # return (timezone.now() - start_time).total_seconds() > self.timeout
        return False

class WebHookWorkFlowServices:
    def __init__(self, data):
        self.webhook_workflow = WebHookWorkFlow(data)
        self.data = data

    def trigger_complete_workflow(self):
        # 生成会话ID
        session_id = self.webhook_workflow.start_workflow()
        """触发完整的工作流程"""
        try:
            # 构造触发数据，包含回调信息
            trigger_data = {
                'action': 'trigger_sync',
                'timestamp': timezone.now().isoformat(),
                'source': 'django_task_system',
                'session_id': session_id,
                'webhook_url': f'https://4b11-2409-8a1e-9310-2000-edce-f141-9214-de83.ngrok-free.app/webhook/receiver/?session={session_id}',
                'callback_required': True,
                'message': '启动完整数据同步工作流程',
                **self.data
            }
            logger.info(f"发送触发请求: {session_id}")
            # 发送触发请求到第一个钉钉地址
            response = requests.post(
                DINGTALK_TRIGGER_URL,
                json=trigger_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            if response.status_code == 200:
                # 设置为等待状态
                self.webhook_workflow.set_waiting(session_id)

                logger.info(f"触发成功，等待回调: {session_id}")
                return {
                    'success': True,
                    'session_id': session_id,
                    'status': 'waiting_for_callback',
                    'message': '触发成功，等待第三方系统回调',
                    'webhook_url': f'https://daa2-2409-8a1e-9310-2000-edce-f141-9214-de83.grok-free.app/webhook/receiver/?session={session_id}',
                    'response': response.json()
                }
            else:
                error_msg = f"触发失败: HTTP {response.status_code}"
                self.webhook_workflow.fail_workflow(session_id, error_msg)
                return {
                    'success': False,
                    'session_id': session_id,
                    'error': error_msg,
                    'response_text': response.text
                }
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求异常: {str(e)}"
            if 'session_id' in locals():
                self.webhook_workflow.fail_workflow(session_id, error_msg)
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"触发异常: {str(e)}"
            if 'session_id' in locals():
                self.webhook_workflow.fail_workflow(session_id, error_msg)
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    @classmethod
    def merge_data(cls, data, request_data):
        rich_text_test_str = "/n".join(request_data.get("rich_text_test", []))
        data["rich_text_test"] = data["rich_text_test"] + (("/n" + rich_text_test_str) if rich_text_test_str != "" else "")
        return data

    @classmethod
    def sync_to_dingtalk(cls, merge_data):
        """
        将处理后的数据同步到钉钉
        支持特定格式的数据重组装
        """
        # 发送请求到钉钉
        response = requests.post(
            DINGTALK_SYNC_URL,
            json=merge_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        return response.json()