from .guild_events import GuildEvents
from .level import Level
from .role import Role
from .starboard import Starboard
from core import Stancil


async def setup(bot: Stancil):
    await bot.add_cog(GuildEvents(bot))
    await bot.add_cog(Level(bot))
    await bot.add_cog(Role(bot))
    await bot.add_cog(Starboard(bot))
