from search.models import UserScore

def userScore(request):
    try:
        score = UserScore.objects.get(user=request.user).score
    except UserScore.DoesNotExist:
        score = None
    return {'user_score': score}