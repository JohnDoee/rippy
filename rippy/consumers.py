from channels.generic.websocket import AsyncJsonWebsocketConsumer


class EventConsumer(AsyncJsonWebsocketConsumer):
    groups = ["event"]

    async def job_add(self, event):
        await self.send_json(event)

    async def job_update(self, event):
        await self.send_json(event)

    async def job_progress(self, event):
        await self.send_json(event)
