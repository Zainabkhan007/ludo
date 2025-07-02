import json
from channels.generic.websocket import AsyncWebsocketConsumer

class GameConsumer(AsyncWebsocketConsumer):
    connected_players = []  # static class-level list to track connected players
    colors = ["blue", "red", "green", "yellow"]

    async def connect(self):
        self.room_group_name = "ludo_room"

        # Add to group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accept connection
        await self.accept()
        print("✅ WebSocket Connected!")

        # Assign a color to this player
        if len(GameConsumer.connected_players) < 4:
            player_color = GameConsumer.colors[len(GameConsumer.connected_players)]
            GameConsumer.connected_players.append({
                "channel_name": self.channel_name,
                "color": player_color
            })
            print(f"🎨 Assigned color: {player_color}")
        else:
            player_color = None
            print("⚠️ No color assigned (room full)")

        # prepare active players list
        active_colors = [player["color"] for player in GameConsumer.connected_players]

        # notify everyone of active players
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "game_message",
                "message": {
                    "type": "player_config",
                    "payload": {
                        "activePlayers": active_colors
                    }
                }
            }
        )

    async def disconnect(self, close_code):
        # Remove from group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Remove from connected players
        GameConsumer.connected_players = [
            p for p in GameConsumer.connected_players
            if p["channel_name"] != self.channel_name
        ]
        print(f"👋 Disconnected. Remaining: {[p['color'] for p in GameConsumer.connected_players]}")

        # send updated player list
        active_colors = [player["color"] for player in GameConsumer.connected_players]
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "game_message",
                "message": {
                    "type": "player_config",
                    "payload": {
                        "activePlayers": active_colors
                    }
                }
            }
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        print("📥 Received from client:", data)

        # make sure there is a "type" field
        if "type" not in data:
            data["type"] = "unknown"

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "game_message",
                "message": data
            }
        )

    async def game_message(self, event):
        message = event["message"]

        # send message back to clients
        await self.send(text_data=json.dumps(message))
