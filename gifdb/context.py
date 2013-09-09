from search.models import UserScore

def userScore(request):
    try:
        score = UserScore.objects.get(user=request.user.id).score
    except UserScore.DoesNotExist:
        score = None
    return {'user_score': score}