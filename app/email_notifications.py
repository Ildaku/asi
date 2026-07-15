"""Уведомления по email через Unisender Go Web API."""

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Iterable, List, Optional

logger = logging.getLogger(__name__)


def _env(name: str, default: str = '') -> str:
    return (os.environ.get(name) or default).strip()


def get_notification_recipients() -> List[str]:
    raw = _env('NOTIFICATION_EMAILS')
    if not raw:
        return []
    return [part.strip() for part in raw.split(',') if part.strip()]


def is_mail_configured() -> bool:
    return bool(
        _env('UNISENDER_GO_API_KEY')
        and _env('UNISENDER_GO_API_URL')
        and _env('MAIL_DEFAULT_SENDER')
        and get_notification_recipients()
    )


def _send_url() -> str:
    base = _env('UNISENDER_GO_API_URL').rstrip('/')
    if base.endswith('/email/send.json'):
        return base
    return f'{base}/email/send.json'


def _format_date(value) -> str:
    if value is None:
        return '—'
    if hasattr(value, 'strftime'):
        return value.strftime('%d.%m.%Y')
    return str(value)


def send_notification_email(subject: str, html_body: str, text_body: str,
                            recipients: Optional[Iterable[str]] = None) -> bool:
    """Отправляет письмо через Unisender Go. Ошибки логируются, исключения не пробрасываются."""
    api_key = _env('UNISENDER_GO_API_KEY')
    from_email = _env('MAIL_DEFAULT_SENDER')
    from_name = _env('MAIL_DEFAULT_SENDER_NAME', 'Planner2')
    to_list = list(recipients) if recipients is not None else get_notification_recipients()

    if not api_key or not from_email or not to_list:
        logger.warning('Email notification skipped: missing API key, sender or recipients')
        return False

    payload = {
        'message': {
            'recipients': [{'email': email} for email in to_list],
            'body': {
                'html': html_body,
                'plaintext': text_body,
            },
            'subject': subject,
            'from_email': from_email,
            'from_name': from_name,
            'global_language': 'ru',
            'template_engine': 'none',
        }
    }

    data = json.dumps(payload).encode('utf-8')
    request = urllib.request.Request(
        _send_url(),
        data=data,
        method='POST',
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-API-KEY': api_key,
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode('utf-8')
            result = json.loads(body) if body else {}
        status = result.get('status')
        if status == 'success':
            logger.info('Email sent: %s -> %s', subject, ', '.join(to_list))
            return True
        logger.error('Unisender Go error: %s', result)
        return False
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode('utf-8', errors='replace')
        logger.error('Unisender Go HTTP %s: %s', exc.code, err_body)
        return False
    except Exception as exc:
        logger.error('Email send failed: %s', exc)
        return False


def notify_planned_production_date_changed(plan, old_date, new_date, changed_by: str) -> bool:
    """Уведомление о смене планируемой даты производства на панели менеджеров."""
    product_name = plan.product.name if plan.product else '—'
    batch = plan.batch_number or f'#{plan.id}'
    old_s = _format_date(old_date)
    new_s = _format_date(new_date)
    subject = f'Planner2: планируемая дата производства — {product_name}'

    text_body = (
        f'Изменена планируемая дата производства.\n\n'
        f'Продукт: {product_name}\n'
        f'Партия: {batch}\n'
        f'Было: {old_s}\n'
        f'Стало: {new_s}\n'
        f'Изменил: {changed_by}\n'
    )
    html_body = (
        f'<p>Изменена <strong>планируемая дата производства</strong>.</p>'
        f'<ul>'
        f'<li><strong>Продукт:</strong> {product_name}</li>'
        f'<li><strong>Партия:</strong> {batch}</li>'
        f'<li><strong>Было:</strong> {old_s}</li>'
        f'<li><strong>Стало:</strong> {new_s}</li>'
        f'<li><strong>Изменил:</strong> {changed_by}</li>'
        f'</ul>'
    )
    return send_notification_email(subject, html_body, text_body)
