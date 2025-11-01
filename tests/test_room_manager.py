import asyncio

from room_manager import RoomManager


async def noop_send(_):
    pass


def test_add_and_get_room_users():
    async def scenario():
        manager = RoomManager()

        await manager.add_client('room1', 'client1', 'Alice', noop_send)
        await manager.add_client('room1', 'client2', 'Bob', noop_send)

        users = await manager.get_room_users('room1')
        assert len(users) == 2
        usernames = {user['username'] for user in users}
        assert usernames == {'Alice', 'Bob'}

    asyncio.run(scenario())


def test_remove_client_and_cleanup():
    async def scenario():
        manager = RoomManager()

        await manager.add_client('room1', 'client1', 'Alice', noop_send)
        await manager.add_client('room1', 'client2', 'Bob', noop_send)

        removed = await manager.remove_client('room1', 'client1')
        assert removed is True
        clients = await manager.get_clients_in_room('room1')
        assert clients == ['client2']

        removed = await manager.remove_client('room1', 'client2')
        assert removed is True
        clients = await manager.get_clients_in_room('room1')
        assert clients == []

    asyncio.run(scenario())


def test_broadcast_and_error_cleanup():
    async def scenario():
        manager = RoomManager()
        messages = []

        async def send_success(payload):
            messages.append(('client1', payload))

        async def send_failure(_):
            raise RuntimeError('send failed')

        await manager.add_client('room1', 'client1', 'Alice', send_success)
        await manager.add_client('room1', 'client2', 'Bob', send_failure)

        await manager.broadcast('room1', {'type': 'test'})

        assert messages == [('client1', {'type': 'test'})]
        clients = await manager.get_clients_in_room('room1')
        assert clients == ['client1']

        await manager.broadcast('room1', {'type': 'second'}, exclude='client1')
        assert messages == [('client1', {'type': 'test'})]

    asyncio.run(scenario())
