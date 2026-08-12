import discord
from discord.ext import commands

TOKEN = "TOKEN_CUA_BAN"
OWNER_ID = 123456789012345678  # Thay bằng Discord User ID của bạn

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="l!", intents=intents)

# Lưu ID các kênh test mà bot đã tạo
test_channels = {}


@bot.event
async def on_ready():
    print(f"Bot đã đăng nhập: {bot.user}")
    print("Bot test đã sẵn sàng!")


def is_owner():
    async def predicate(ctx):
        return ctx.author.id == OWNER_ID
    return commands.check(predicate)


@bot.command()
@is_owner()
async def nuke(ctx):
    """Tạo tối đa 5 kênh test an toàn."""

    guild = ctx.guild

    if guild.id not in test_channels:
        test_channels[guild.id] = []

    created = 0

    for i in range(1, 6):
        channel_name = f"test-nuke-{i}"

        # Nếu kênh đã tồn tại thì bỏ qua
        existing = discord.utils.get(guild.text_channels, name=channel_name)

        if existing:
            continue

        channel = await guild.create_text_channel(channel_name)

        test_channels[guild.id].append(channel.id)

        await channel.send(
            f"🧪 **Kênh kiểm thử {i}**\n"
            f"Bot đã tạo kênh này bằng `l!nuke`.\n"
            f"Đây chỉ là chế độ kiểm thử an toàn."
        )

        created += 1

    await ctx.send(
        f"✅ Đã tạo **{created}/5 kênh test**.\n"
        f"Dùng `l!resettest` để xóa các kênh test."
    )


@bot.command()
@is_owner()
async def resettest(ctx):
    """Xóa các kênh test do bot tạo."""

    guild = ctx.guild
    channel_ids = test_channels.get(guild.id, [])

    deleted = 0

    for channel_id in channel_ids.copy():
        channel = guild.get_channel(channel_id)

        if channel:
            try:
                await channel.delete(reason="Xóa kênh test")
                deleted += 1
            except discord.Forbidden:
                pass

    test_channels[guild.id] = []

    await ctx.send(
        f"🧹 Đã xóa **{deleted} kênh test**."
    )


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("❌ Bạn không có quyền sử dụng lệnh này.")
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        print(f"Lỗi: {error}")


bot.run(TOKEN)
