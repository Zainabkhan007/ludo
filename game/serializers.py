from .models import *
from rest_framework import serializers
from django.contrib.auth.hashers import check_password 
class PieceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Piece
        fields = "__all__"

class GameSerializer(serializers.ModelSerializer):
    pieces = PieceSerializer(many=True, read_only=True)

    class Meta:
        model = Game
        fields = "__all__"
class UserRegisterationSerializer(serializers.ModelSerializer):
 
   
    class Meta:
        model = UserRegisteration
        fields = '__all__'


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
   

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        

        try:
            user = UserRegisteration.objects.get(email=email, )
        except UserRegisteration.DoesNotExist:
            raise serializers.ValidationError("Invalid email .")

        if not check_password(password, user.password):
            raise serializers.ValidationError("Invalid password.")

        data['user'] = user
        return data

    