from dotenv import load_dotenv
import os

import asyncio

from async_timeout import timeout

import discord
from discord.ext import commands

load_dotenv()
TOKEN = os.environ["DISCORD_BOT_TOKEN"]


class VoiceError(Exception):
    pass


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx

        self.voice = None

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    async def audio_player_task(self):
        while True:
            await asyncio.sleep(0.001)

            if self.voice is None:
                continue

            if self.voice.is_playing():
                continue

            source = discord.FFmpegPCMAudio("test.wav")

            self.voice.play(source, after=self.catch_error)

    def catch_error(self, error=None):
        if error:
            raise VoiceError(str(error))

    async def stop(self):
        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage("这个命令不能在DM通道中使用。")

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        await ctx.send("发生错误: {}".format(str(error)))

    @commands.command(name="join", aliases=["hao"], invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        """Joins a voice channel."""

        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name="leave", aliases=["disconnect"])
    @commands.has_permissions(manage_guild=True)
    async def _leave(self, ctx: commands.Context):
        """Clears the queue and leaves the voice channel."""

        if self.voice_states[ctx.guild.id]:
            await ctx.voice_state.stop()
            del self.voice_states[ctx.guild.id]

    @_join.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError("您没有连接到任何语音频道。")

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError("机器人已经在一个语音通道中。")

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if self.bot.user.id != member.id:
            return

        if not before.channel:
            return

        guild_id = before.channel.guild.id
        if self.voice_states[guild_id]:
            if not after.channel:
                del self.voice_states[guild_id]
            else:
                if self.voice_states[guild_id].voice:
                    await self.voice_states[guild_id].voice.stop()
                self.voice_states[guild_id].voice = await after.connect()


bot = commands.Bot("ni", description="97")
bot.add_cog(Music(bot))


@bot.event
async def on_ready():
    print("Logged in as:\n{0.user.name}\n{0.user.id}".format(bot))


bot.run(TOKEN)