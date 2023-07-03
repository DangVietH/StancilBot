from discord.ext import commands, ipc
from discord.ext.ipc.server import Server
from discord.ext.ipc.objects import ClientPayload
from core import Stancil


class Routes(commands.Cog):
    def __init__(self, bot: Stancil):
        self.bot = bot

    @Server.route()
    async def get_user_data(self, data: ClientPayload):
        user = self.bot.get_user(data.user_id)
        return user._to_minimal_user_json()
