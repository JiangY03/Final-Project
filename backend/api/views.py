from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

CLIENT_MOODS = defaultdict(list)  # client_id -> [{date:'YYYY-MM-DD', score:int, note:str, at: iso}]
CLIENT_ASSESSMENTS = defaultdict(list)  # client_id -> [{answers:list[int], total:int, level:str, crisis:bool, ai:dict, at: iso}]
CLIENT_SURVEYS = defaultdict(lambda: { 'sus': [], 'satisfaction': [] })  # client_id -> { sus: [answers], satisfaction: [entries] }
USERS = {}  # email -> { email, password, name }


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
  logger.info('Health check requested')
  return Response({'ok': True, 'status': 'healthy'})


def get_client_id(request):
  cid = request.headers.get('X-Client-Id') or request.GET.get('client_id') or request.POST.get('client_id')
  return cid


@api_view(['POST'])
@permission_classes([AllowAny])
def auth_login(request):
  email = (request.data or {}).get('email')
  password = (request.data or {}).get('password')
  logger.info('Login attempt email=%s', email)
  if not email or not password:
    return Response({'ok': False, 'message': '缺少邮箱或密码'}, status=400)

  # Validate against registered users if present; otherwise reject
  user = USERS.get(email)
  if not user or user.get('password') != password:
    return Response({'ok': False, 'message': '邮箱或密码不正确'}, status=401)

  client_id = f'email:{email}'
  name = user.get('name') or email.split('@')[0]
  return Response({
    'ok': True,
    'user': { 'id': client_id, 'email': email, 'name': name },
    'token': 'demo-token'
  })


@api_view(['POST'])
@permission_classes([AllowAny])
def auth_register(request):
  payload = request.data or {}
  email = (payload.get('email') or '').strip().lower()
  password = (payload.get('password') or '').strip()
  name = (payload.get('name') or '').strip() or (email.split('@')[0] if email else '')
  if not email or not password:
    return Response({'ok': False, 'message': '邮箱与密码必填'}, status=400)
  if email in USERS:
    return Response({'ok': False, 'message': '该邮箱已注册'}, status=409)
  USERS[email] = { 'email': email, 'password': password, 'name': name }
  logger.info('User registered email=%s', email)
  return Response({'ok': True})


@api_view(['POST'])
@permission_classes([AllowAny])
def auth_anon(request):
  cid = get_client_id(request)
  if not cid:
    cid = f'anon:{uuid.uuid4().hex[:12]}'
  logger.info('Anon login with client_id=%s', cid)
  return Response({'ok': True, 'user': {'id': cid, 'email': 'anon@local', 'name': 'Anonymous'}, 'token': 'anon-token'})


def today_str():
  return datetime.utcnow().date().isoformat()


def last_n_days_records(records, days):
  if not records:
    return []
  cutoff = datetime.utcnow().date() - timedelta(days=days - 1)
  filtered = [r for r in records if datetime.fromisoformat(r['date']).date() >= cutoff]
  return sorted(filtered, key=lambda r: r['date'])


@api_view(['GET'])
@permission_classes([AllowAny])
def moods_list(request):
  cid = get_client_id(request)
  if not cid:
    return Response({'ok': False, 'message': '缺少匿名ID（X-Client-Id 或 client_id）'}, status=400)
  days = int(request.GET.get('days', '7') or '7')
  data = last_n_days_records(CLIENT_MOODS.get(cid, []), max(1, min(days, 30)))
  logger.info('Moods list cid=%s days=%s count=%s', cid, days, len(data))
  return Response({'ok': True, 'data': data})


@api_view(['POST'])
@permission_classes([AllowAny])
def moods_add(request):
  cid = get_client_id(request)
  if not cid:
    return Response({'ok': False, 'message': '缺少匿名ID（X-Client-Id 或 client_id）'}, status=400)
  payload = request.data or {}
  score = int(payload.get('score') or 0)
  note = (payload.get('note') or '').strip()
  if score < 1 or score > 5:
    return Response({'ok': False, 'message': '分数必须在 1-5 之间'}, status=400)
  records = CLIENT_MOODS[cid]
  t = today_str()
  if any(r['date'] == t for r in records):
    return Response({'ok': False, 'message': '今天已记录'}, status=409)
  rec = { 'date': t, 'score': score, 'note': note, 'at': datetime.utcnow().isoformat() }
  records.append(rec)
  logger.info('Moods add cid=%s score=%s', cid, score)
  return Response({'ok': True, 'data': rec})


@api_view(['GET','POST'])
@permission_classes([AllowAny])
def moods_root(request):
  # For compatibility with frontend: GET /api/moods and POST /api/moods
  # Do not delegate to other decorated views to avoid DRF Request/HttpRequest mismatch
  if request.method == 'GET':
    cid = get_client_id(request)
    if not cid:
      return Response({'ok': False, 'message': '缺少匿名ID（X-Client-Id 或 client_id）'}, status=400)
    days = int(request.GET.get('days', '7') or '7')
    data = last_n_days_records(CLIENT_MOODS.get(cid, []), max(1, min(days, 30)))
    logger.info('Moods list(cid via root) cid=%s days=%s count=%s', cid, days, len(data))
    return Response({'ok': True, 'data': data})

  # POST
  cid = get_client_id(request)
  if not cid:
    return Response({'ok': False, 'message': '缺少匿名ID（X-Client-Id 或 client_id）'}, status=400)
  payload = request.data or {}
  try:
    score = int(payload.get('score') or 0)
  except Exception:
    return Response({'ok': False, 'message': '分数必须为整数'}, status=400)
  note = (payload.get('note') or '').strip()
  if score < 1 or score > 5:
    return Response({'ok': False, 'message': '分数必须在 1-5 之间'}, status=400)
  records = CLIENT_MOODS[cid]
  t = today_str()
  if any(r['date'] == t for r in records):
    return Response({'ok': False, 'message': '今天已记录'}, status=409)
  rec = { 'date': t, 'score': score, 'note': note, 'at': datetime.utcnow().isoformat() }
  records.append(rec)
  logger.info('Moods add(cid via root) cid=%s score=%s', cid, score)
  return Response({'ok': True, 'data': rec})


@api_view(['GET'])
@permission_classes([AllowAny])
def moods_summary(request):
  cid = get_client_id(request)
  if not cid:
    return Response({'ok': False, 'message': '缺少匿名ID（X-Client-Id 或 client_id）'}, status=400)
  recent = last_n_days_records(CLIENT_MOODS.get(cid, []), 7)
  count = len(recent)
  avg = round(sum(r['score'] for r in recent) / count, 2) if count else 0.0
  logger.info('Moods summary cid=%s count=%s avg=%s', cid, count, avg)
  return Response({'ok': True, 'data': { 'average': avg, 'count': count }})


def grade_phq9(total: int) -> str:
  if total <= 4:
    return 'none-minimal'
  if total <= 9:
    return 'mild'
  if total <= 14:
    return 'moderate'
  if total <= 19:
    return 'moderately severe'
  return 'severe'


@api_view(['POST'])
@permission_classes([AllowAny])
def assessment_submit(request):
  cid = get_client_id(request)
  if not cid:
    return Response({'ok': False, 'message': '缺少匿名ID（X-Client-Id 或 client_id）'}, status=400)
  payload = request.data or {}
  answers = payload.get('answers') or []
  if not isinstance(answers, list) or len(answers) != 9:
    return Response({'ok': False, 'message': '参数不合法：应为 9 个 0-3 分的数组'}, status=400)
  try:
    answers = [int(x) for x in answers]
  except Exception:
    return Response({'ok': False, 'message': '参数不合法：分数必须为整数'}, status=400)
  if any(x < 0 or x > 3 for x in answers):
    return Response({'ok': False, 'message': '参数不合法：每题分数需在 0-3'}, status=400)
  total = sum(answers)
  level = grade_phq9(total)
  crisis = answers[8] > 0  # Q9 index 8
  record = {
    'answers': answers,
    'total': total,
    'level': level,
    'crisis': crisis,
    'ai': {
      'summary': '占位：后续由 AI 生成个性化总结。',
      'recommendations': ['示例：每天一次情绪打卡', '示例：3 分钟呼吸练习', '示例：每周两次认知重构'],
      'risk_level': 'high' if crisis else ('moderate' if total >= 15 else 'low'),
    },
    'at': datetime.utcnow().isoformat(),
  }
  CLIENT_ASSESSMENTS[cid].append(record)
  logger.info('Assessment submit cid=%s total=%s level=%s crisis=%s', cid, total, level, crisis)
  return Response({'ok': True, 'data': {k: record[k] for k in ['total','level','crisis','ai','at']}})


@api_view(['GET'])
@permission_classes([AllowAny])
def assessment_last(request):
  cid = get_client_id(request)
  if not cid:
    return Response({'ok': False, 'message': '缺少匿名ID（X-Client-Id 或 client_id）'}, status=400)
  items = CLIENT_ASSESSMENTS.get(cid, [])
  last = items[-1] if items else None
  if not last:
    return Response({'ok': True, 'data': None})
  return Response({'ok': True, 'data': {k: last[k] for k in ['total','level','crisis','ai','at']}})


def contains_sensitive(text: str) -> bool:
  if not text:
    return False
  t = str(text).lower()
  keywords = [
    'suicide', "don't want to live", 'kill myself', 'end my life',
    '不想活', '想自杀', '自杀', '轻生', '寻短见', '活不下去'
  ]
  return any(k in t for k in keywords)


@api_view(['POST'])
@permission_classes([AllowAny])
def chat(request):
  cid = get_client_id(request)
  payload = request.data or {}
  message = (payload.get('message') or '').strip()
  logger.info('Chat message cid=%s len=%s', cid, len(message))

  if contains_sensitive(message):
    return Response({
      'ok': True,
      'type': 'crisis',
      'message': '我听到了你感到非常痛苦，甚至出现了伤害自己的念头。你的安全最重要。请立即联系身边可信赖的人或专业的热线支持。',
      'hotlines': [
        { 'label': '中国心理援助热线', 'number': '12320' },
        { 'label': '紧急电话', 'number': '110' },
        { 'label': '校园/社区辅导中心', 'number': '请联系本地机构' },
      ]
    })

  # Safety check passed. Here we would call AI, but now return a fallback supportive text.
  return Response({
    'ok': True,
    'type': 'support',
    'message': '抱抱你。我能理解这段时间对你并不容易。先做三次深呼吸，给自己一点空间。如果你愿意，可以试试“自助工具”里的呼吸计时或认知重构，我们也可以继续聊聊让你困扰的事情。'
  })


@api_view(['POST'])
@permission_classes([AllowAny])
def survey_sus(request):
  cid = get_client_id(request)
  if not cid:
    return Response({'ok': False, 'message': '缺少匿名ID（X-Client-Id 或 client_id）'}, status=400)
  answers = (request.data or {}).get('answers')
  if not isinstance(answers, list) or len(answers) != 10:
    return Response({'ok': False, 'message': '参数不合法：需 10 个 1-5 分的数组'}, status=400)
  try:
    answers = [int(x) for x in answers]
  except Exception:
    return Response({'ok': False, 'message': '参数不合法：分数必须为整数'}, status=400)
  if any(x < 1 or x > 5 for x in answers):
    return Response({'ok': False, 'message': '参数不合法：每题分数需在 1-5'}, status=400)
  CLIENT_SURVEYS[cid]['sus'].append({ 'answers': answers, 'at': datetime.utcnow().isoformat() })
  logger.info('Survey SUS saved cid=%s', cid)
  return Response({ 'ok': True })


@api_view(['POST'])
@permission_classes([AllowAny])
def survey_satisfaction(request):
  cid = get_client_id(request)
  if not cid:
    return Response({'ok': False, 'message': '缺少匿名ID（X-Client-Id 或 client_id）'}, status=400)
  payload = request.data or {}
  try:
    score = int(payload.get('score'))
  except Exception:
    return Response({'ok': False, 'message': '参数不合法：评分必须为 1-5'}, status=400)
  if score < 1 or score > 5:
    return Response({'ok': False, 'message': '参数不合法：评分必须为 1-5'}, status=400)
  comment = (payload.get('comment') or '').strip()
  CLIENT_SURVEYS[cid]['satisfaction'].append({ 'score': score, 'comment': comment, 'at': datetime.utcnow().isoformat() })
  logger.info('Survey satisfaction saved cid=%s score=%s', cid, score)
  return Response({ 'ok': True })
