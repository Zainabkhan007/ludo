# views.py

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import UserRegisteration, Game, Piece
from .serializers import UserRegisterationSerializer, GameSerializer, PieceSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.core.mail import send_mail
from urllib.parse import quote
import pusher
import random
import string
import os

# initialize pusher
pusher_client = pusher.Pusher(
    app_id=settings.PUSHER_APP_ID,
    key=settings.PUSHER_KEY,
    secret=settings.PUSHER_SECRET,
    cluster=settings.PUSHER_CLUSTER,
    ssl=True
)

# 🎲 Roll dice
@api_view(["POST"])
def roll_dice(request, game_code):
    dice_value = random.randint(1, 6)
    
    try:
        game = Game.objects.get(code=game_code)
        if not game.current_turn:
            # agar pehli baar hai to first turn assign karo
            game.current_turn = "blue"  # ya koi bhi tumhara pehla player
            game.save()
            pusher_client.trigger("game-channel", "turn_change", {
                "type": "turn_change",
                "payload": {"currentPlayer": game.current_turn}
            })
        # warna kuch nahi, sirf dice bhejo
    except Game.DoesNotExist:
        return Response({"error": "Game not found"}, status=404)
        
    return Response({"dice": dice_value})


# 🎯 Get current game state
@api_view(["GET"])
def game_state(request, game_code):
    game = get_object_or_404(Game, code=game_code)
    pieces = Piece.objects.filter(game=game)
    serialized_pieces = PieceSerializer(pieces, many=True).data
    return Response({
        "game": game.code,
        "turn": game.current_turn,
        "winner": game.winner,
        "pieces": serialized_pieces
    })

# 🟢 Move piece
@api_view(["POST"])
def move_piece(request):
    data = request.data
    piece_id = data.get("piece_id")
    new_pos = data.get("position")
    game_code = data.get("game_code")

    try:
        piece = Piece.objects.get(player_id=piece_id, game__code=game_code)
        piece.position = new_pos
        piece.status = 1
        piece.save()

        pusher_client.trigger("game-channel", "piece-moved", {
            "type": "move",
            "payload": {
                "pieceId": piece_id,
                "position": new_pos,
            }
        })

        return Response({"success": True})
    except Piece.DoesNotExist:
        return Response({"error": "Piece not found"}, status=404)

# 🔄 Next turn
@api_view(["POST"])
def change_turn(request):
    data = request.data
    game_code = data.get("game_code")
    next_turn = data.get("next_turn")

    try:
        game = Game.objects.get(code=game_code)
        game.current_turn = next_turn
        game.save()

        pusher_client.trigger("game-channel", "turn_change", {
            "type": "turn_change",
            "payload": {
                "currentPlayer": next_turn,
            }
        })

        return Response({"success": True})
    except Game.DoesNotExist:
        return Response({"error": "Game not found"}, status=404)

# 🆕 Create new game
@api_view(["POST"])
def create_game(request):
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    game = Game.objects.create(code=code)
    return Response({"game_code": code})

# user authentication APIs below (no change, keeping them safe)
@api_view(["POST"])
def register(request):
    email = request.data.get('email')
    if not email:
        return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
    if UserRegisteration.objects.filter(email=email).exists():
        return Response({"error": "Email already registered."}, status=status.HTTP_400_BAD_REQUEST)
    password = request.data.get('password')
    password_confirmation = request.data.get('confrmpassword')
    if password != password_confirmation:
        return Response({"error": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)
    serializer = UserRegisterationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        user.status = "online"
        user.save()
        refresh = RefreshToken.for_user(user)
        request.session['user_id'] = user.id
        request.session['user_email'] = user.email
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'role': user.role,
            'user_id': user.id,
            'email': user.email,
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)
    return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(["POST"])
def logout(request):
    user_id = request.session.get("user_id")
    if user_id:
        try:
            user = UserRegisteration.objects.get(id=user_id)
            user.status = "offline"
            user.save()
        except UserRegisteration.DoesNotExist:
            pass
    request.session.flush()
    return Response({"message": "Logged out successfully"})

# admin login
@api_view(["POST"])
def admin_login(request):
    email = request.data.get("email")
    password = request.data.get("password")
    if email != settings.ADMIN_EMAIL or password != settings.ADMIN_PASSWORD:
        return Response({"error": "Invalid admin credentials"}, status=401)
    request.session['admin_logged_in'] = True
    return Response({"message": "Admin login successful"})

# list active
@api_view(["GET"])
def active_users(request):
    active = UserRegisteration.objects.filter(status="online")
    serializer = UserRegisterationSerializer(active, many=True)
    return Response(serializer.data)

# list all
@api_view(["GET"])
def list_all_users(request):
    if request.session.get("user_role") != "admin":
        return Response({"error": "Unauthorized"}, status=403)
    users = UserRegisteration.objects.all()
    serializer = UserRegisterationSerializer(users, many=True)
    return Response(serializer.data)

# block user
@api_view(["POST"])
def block_user(request, user_id):
    if request.session.get("user_role") != "admin":
        return Response({"error": "Unauthorized"}, status=403)
    try:
        user = UserRegisteration.objects.get(id=user_id)
        user.status = "blocked"
        user.save()
        return Response({"message": "User blocked"})
    except UserRegisteration.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

# delete user
@api_view(["DELETE"])
def delete_user(request, user_id):
    if request.session.get("user_role") != "admin":
        return Response({"error": "Unauthorized"}, status=403)
    try:
        user = UserRegisteration.objects.get(id=user_id)
        user.delete()
        return Response({"message": "User deleted"})
    except UserRegisteration.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

# password reset
@api_view(["POST"])
def password_reset(request):
    email = request.data.get("email")
    if not email:
        return Response({"error": "Email is required."}, status=400)
    try:
        user = UserRegisteration.objects.get(email=email)
    except UserRegisteration.DoesNotExist:
        return Response({"error": "User not found."}, status=400)
    signer = TimestampSigner()
    signed_token = signer.sign(user.email)
    encoded_token = quote(signed_token)
    reset_link = f"http://localhost:5173/reset-password?token={encoded_token}"
    send_mail(
        subject="Password Reset",
        message=f"Click here to reset your password: {reset_link}",
        from_email=os.getenv('DEFAULT_FROM_EMAIL', 'support@example.com'),
        recipient_list=[user.email],
        fail_silently=False
    )
    return Response({"message": "Password reset email sent."})

@api_view(["POST"])
def password_reset_confirm(request):
    token = request.data.get("token")
    new_password = request.data.get("new_password")
    confirm_password = request.data.get("confirm_password")
    if not token or not new_password or not confirm_password:
        return Response({"error": "Missing fields"}, status=400)
    if new_password != confirm_password:
        return Response({"error": "Passwords do not match"}, status=400)
    try:
        signer = TimestampSigner()
        email = signer.unsign(token, max_age=3600)
    except (BadSignature, SignatureExpired):
        return Response({"error": "Invalid or expired token"}, status=400)
    try:
        user = UserRegisteration.objects.get(email=email)
        user.password = new_password
        user.confrmpassword = new_password
        user.save()
    except UserRegisteration.DoesNotExist:
        return Response({"error": "User not found"}, status=400)
    return Response({"message": "Password reset successful."})
@api_view(["POST"])
def join_game(request):
    game_code = request.data.get("game_code")
    player_color = request.data.get("color")

    try:
        game = Game.objects.get(code=game_code)
        # yeh check karo agar color already taken hai ya nahi future me
        return Response({"success": True, "assigned_color": player_color})
    except Game.DoesNotExist:
        return Response({"error": "Game not found"}, status=404)