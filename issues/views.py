import json
from pathlib import Path

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import (
    ALLOWED_STATUSES,
    CriticalIssue,
    Issue,
    LowPriorityIssue,
    Reporter,
)

BASE_DIR = Path(__file__).resolve().parent.parent
ISSUES_FILE = BASE_DIR / 'issues.json'
REPORTERS_FILE = BASE_DIR / 'reporters.json'


def load_records(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_records(path, records):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=4, ensure_ascii=False)


def error(message, status):
    return JsonResponse({'error': message}, status=status)


def parse_body(request):
    """Return (data, error_response)."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, error('Invalid JSON', 400)
    if not isinstance(data, dict):
        return None, error('Invalid JSON: expected an object', 400)
    return data, None


def check_required(data, fields):
    for field in fields:
        if field not in data:
            return error(f'Missing required field: {field}', 400)
    return None


def parse_int_id(value, label='id'):
    """Return (int, error_response)."""
    if isinstance(value, bool):
        return None, error(f'{label} must be an integer', 400)
    try:
        return int(value), None
    except (TypeError, ValueError):
        return None, error(f'{label} must be an integer', 400)


@csrf_exempt
def reporters(request):
    if request.method == 'POST':
        data, err = parse_body(request)
        if err:
            return err
        err = check_required(data, ['id', 'name', 'email', 'team'])
        if err:
            return err
        reporter_id, err = parse_int_id(data['id'])
        if err:
            return err

        reporter = Reporter(reporter_id, data['name'], data['email'], data['team'])
        try:
            reporter.validate()
        except ValueError as e:
            return error(str(e), 400)

        records = load_records(REPORTERS_FILE)
        if any(r['id'] == reporter_id for r in records):
            return error('Reporter with this id already exists', 400)
        record = reporter.to_dict()
        records.append(record)
        save_records(REPORTERS_FILE, records)
        return JsonResponse(record, status=201)

    if request.method == 'GET':
        records = load_records(REPORTERS_FILE)
        id_param = request.GET.get('id')
        if id_param is None:
            return JsonResponse(records, safe=False, status=200)
        reporter_id, err = parse_int_id(id_param)
        if err:
            return err
        for record in records:
            if record['id'] == reporter_id:
                return JsonResponse(record, status=200)
        return error('Reporter not found', 404)

    return error('Method not allowed', 405)


@csrf_exempt
def issues(request):
    if request.method == 'POST':
        data, err = parse_body(request)
        if err:
            return err
        err = check_required(
            data, ['id', 'title', 'description', 'status', 'priority', 'reporter_id']
        )
        if err:
            return err
        issue_id, err = parse_int_id(data['id'])
        if err:
            return err
        reporter_id, err = parse_int_id(data['reporter_id'], 'reporter_id')
        if err:
            return err

        args = (
            issue_id, data['title'], data['description'],
            data['status'], data['priority'], reporter_id,
        )
        if data['priority'] == 'critical':
            issue = CriticalIssue(*args)
        elif data['priority'] == 'low':
            issue = LowPriorityIssue(*args)
        else:
            issue = Issue(*args)

        try:
            issue.validate()
        except ValueError as e:
            return error(str(e), 400)

        if not any(r['id'] == reporter_id for r in load_records(REPORTERS_FILE)):
            return error('Reporter not found', 404)

        records = load_records(ISSUES_FILE)
        if any(r['id'] == issue_id for r in records):
            return error('Issue with this id already exists', 400)

        response_data = issue.to_dict()
        response_data['message'] = issue.describe()
        records.append(issue.to_dict())
        save_records(ISSUES_FILE, records)
        return JsonResponse(response_data, status=201)

    if request.method == 'GET':
        records = load_records(ISSUES_FILE)
        id_param = request.GET.get('id')
        status_param = request.GET.get('status')

        if id_param is not None:
            issue_id, err = parse_int_id(id_param)
            if err:
                return err
            for record in records:
                if record['id'] == issue_id:
                    return JsonResponse(record, status=200)
            return error('Issue not found', 404)

        if status_param is not None:
            if status_param not in ALLOWED_STATUSES:
                return error(
                    f"Invalid status '{status_param}'. Allowed: {', '.join(ALLOWED_STATUSES)}",
                    400,
                )
            matches = [r for r in records if r['status'] == status_param]
            return JsonResponse(matches, safe=False, status=200)

        return JsonResponse(records, safe=False, status=200)

    return error('Method not allowed', 405)
