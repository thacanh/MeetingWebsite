from datetime import datetime

class RoomManager:
    def __init__(self):
        self.rooms = {}
    
    def add_client(self, room_id, client_id, username):
        if room_id not in self.rooms:
            self.rooms[room_id] = {}
        
        self.rooms[room_id][client_id] = {
            'username': username,
            'joined_at': datetime.now()
        }
    
    def remove_client(self, room_id, client_id):
        if room_id in self.rooms and client_id in self.rooms[room_id]:
            del self.rooms[room_id][client_id]
            
            if len(self.rooms[room_id]) == 0:
                del self.rooms[room_id]
    
    def get_clients_in_room(self, room_id):
        if room_id in self.rooms:
            return list(self.rooms[room_id].keys())
        return []
    
    def get_room_users(self, room_id):
        if room_id in self.rooms:
            return [
                {
                    'client_id': cid,
                    'username': info['username'],
                    'joined_at': info['joined_at'].isoformat()
                }
                for cid, info in self.rooms[room_id].items()
            ]
        return []
