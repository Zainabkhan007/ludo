# views.py
from django.http import JsonResponse
import pusher
from django.conf import settings

pusher_client = pusher.Pusher(
    app_id=settings.PUSHER_APP_ID,
    key=settings.PUSHER_KEY,
    secret=settings.PUSHER_SECRET,
    cluster=settings.PUSHER_CLUSTER,
    ssl=True
)

def move_piece(request):
    # for example you process a move:
    piece_id = request.GET.get("piece_id")
    new_position = request.GET.get("pos")
    
    # any database updates or validation here
    
    # then push the move to all clients
    pusher_client.trigger('game-channel', 'piece-moved', {
        'piece_id': piece_id,
        'new_position': new_position
    })
    return JsonResponse({"status": "OK"})
