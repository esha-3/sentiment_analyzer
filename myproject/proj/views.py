import json

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

from textblob import TextBlob

from .models import SentimentResult


def _classify(polarity: float) -> str:
    """Return a human-readable classification from a polarity score."""
    if polarity >= 0.3:
        return 'very_positive'
    elif polarity > 0.05:
        return 'positive'
    elif polarity >= -0.05:
        return 'neutral'
    elif polarity > -0.3:
        return 'negative'
    else:
        return 'very_negative'


def _get_custom_booster(text: str) -> float:
    """Return a polarity booster for common success/failure keywords in contextual sentences."""
    tokens = text.lower().split()
    boost = 0.0

    pos_boosts = {
        'passed': 0.45,
        'pass': 0.35,
        'cleared': 0.35,
        'win': 0.35,
        'won': 0.45,
        'achieved': 0.35,
        'succeed': 0.35,
        'succeeded': 0.45,
        'success': 0.35,
        'excellent': 0.4,
        'great': 0.35,
    }

    neg_boosts = {
        'failed': -0.45,
        'fail': -0.35,
        'failing': -0.35,
        'lost': -0.35,
        'lose': -0.35,
        'defeat': -0.35,
        'defeated': -0.45,
    }

    for token in tokens:
        clean_token = token.strip('.,!?;:"()')
        if clean_token in pos_boosts:
            boost += pos_boosts[clean_token]
        elif clean_token in neg_boosts:
            boost += neg_boosts[clean_token]

    return boost


def cors_json_response(data, status=200):
    """Return a JsonResponse with CORS headers enabled."""
    response = JsonResponse(data, status=status)
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
    response["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, DELETE"
    return response


@require_GET
def index(request):
    """Render the main sentiment-analysis page."""
    return render(request, 'proj/index.html')


@csrf_exempt
def analyze(request):
    """Run sentiment analysis on the submitted text and return JSON (with CORS support)."""
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
        response["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
        return response

    if request.method != 'POST':
        return cors_json_response({'error': 'Method not allowed.'}, status=405)

    try:
        body = json.loads(request.body)
        text = body.get('text', '').strip()
    except (json.JSONDecodeError, AttributeError):
        text = request.POST.get('text', '').strip()

    if not text:
        return cors_json_response({'error': 'Please enter some text to analyse.'}, status=400)

    # Base TextBlob NLP
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity

    # Contextual booster
    booster = _get_custom_booster(text)
    polarity = max(-1.0, min(1.0, polarity + booster))

    polarity = round(polarity, 4)
    subjectivity = round(subjectivity, 4)
    classification = _classify(polarity)

    # Persist to database
    SentimentResult.objects.create(
        text=text,
        polarity=polarity,
        subjectivity=subjectivity,
        classification=classification,
    )

    label_map = {
        'very_positive': 'Very Positive 🤩',
        'positive': 'Positive 😊',
        'neutral': 'Neutral 😐',
        'negative': 'Negative 😞',
        'very_negative': 'Very Negative 😡',
    }

    return cors_json_response({
        'polarity': polarity,
        'subjectivity': subjectivity,
        'classification': classification,
        'label': label_map[classification],
    })


@csrf_exempt
def history(request):
    """Return the 20 most recent analyses as JSON (with CORS support)."""
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
        response["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
        return response

    if request.method != 'GET':
        return cors_json_response({'error': 'Method not allowed.'}, status=405)

    results = SentimentResult.objects.all()[:20]
    data = [
        {
            'id': r.id,
            'text': r.text[:120] + ('…' if len(r.text) > 120 else ''),
            'polarity': r.polarity,
            'subjectivity': r.subjectivity,
            'classification': r.classification,
            'created_at': r.created_at.strftime('%b %d, %Y %H:%M'),
        }
        for r in results
    ]
    return cors_json_response({'results': data})


@csrf_exempt
def delete_analysis(request, pk):
    """Delete a specific sentiment result by primary key (with CORS support)."""
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
        response["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, DELETE"
        return response

    if request.method not in ['POST', 'DELETE']:
        return cors_json_response({'error': 'Method not allowed.'}, status=405)

    try:
        result = SentimentResult.objects.get(pk=pk)
        result.delete()
        return cors_json_response({'success': True})
    except SentimentResult.DoesNotExist:
        return cors_json_response({'error': 'Analysis result not found.'}, status=404)


@csrf_exempt
def clear_all(request):
    """Delete all sentiment results (with CORS support)."""
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
        response["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
        return response

    if request.method not in ['POST', 'DELETE']:
        return cors_json_response({'error': 'Method not allowed.'}, status=405)

    SentimentResult.objects.all().delete()
    return cors_json_response({'success': True})
