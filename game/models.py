from django.db import models

# Create your models here.


from django.contrib.auth.hashers import make_password

# Create your models here.

class Game(models.Model):
    code = models.CharField(max_length=20, unique=True)
    current_turn = models.CharField(max_length=20, default="blue")
    winner = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Piece(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="pieces")
    team = models.CharField(max_length=10)
    position = models.CharField(max_length=20)
    status = models.IntegerField(default=0)  # 0=locked, 1=unlocked
    player_id = models.CharField(max_length=20)
class UserRegisteration(models.Model):
   
    name=models.CharField(max_length=30)
    email=models.EmailField(max_length=254,unique=True)
   
    password=models.CharField(max_length=128)
    confrmpassword=models.CharField(max_length=128)
    status = models.CharField(
        max_length=10,
        choices=(("online", "Online"), ("offline", "Offline")),
        default="offline"
    )
    
    def save(self, *args, **kwargs):
      
        if self.password and (not self.pk or not UserRegisteration.objects.filter(id=self.pk, password=self.password).exists()):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    def __str__(self):
        return self.first_name 


       