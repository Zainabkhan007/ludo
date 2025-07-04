from django.urls import path
from . import views

urlpatterns = [
    # game apis
    path("api/create-game/", views.create_game, name="create_game"),
    path("api/join-game/", views.join_game, name="join_game"),
    path("api/roll-dice/<str:game_code>/", views.roll_dice, name="roll_dice"),
    path("api/game-state/<str:game_code>/", views.game_state, name="game_state"),
    path("api/move-piece/", views.move_piece, name="move_piece"),
    path("api/change-turn/", views.change_turn, name="change_turn"),
    
    # user
    path("api/register/", views.register, name="register"),
    path("api/login/", views.login, name="login"),
    path("api/logout/", views.logout, name="logout"),
    path("api/admin-login/", views.admin_login, name="admin_login"),
    path("api/active-users/", views.active_users, name="active_users"),
    path("api/list-users/", views.list_all_users, name="list_all_users"),
    path("api/block-user/<int:user_id>/", views.block_user, name="block_user"),
    path("api/delete-user/<int:user_id>/", views.delete_user, name="delete_user"),
    path("api/password-reset/", views.password_reset, name="password_reset"),
    path("api/password-reset-confirm/", views.password_reset_confirm, name="password_reset_confirm"),
]
