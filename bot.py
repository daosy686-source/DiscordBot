import asyncio
import os
import random
import time
import discord
from discord.ext import commands
from groq import Groq

# ==================== CẤU HÌNH HỆ THỐNG ====================
DISCORD_TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

BOT_OWNERS = [
    1531882555664629861,  
    1535132569534865490,
    1454570566517260422
]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.moderation = True

bot = commands.Bot(command_prefix=(".", "/", "?", "@"), intents=intents, help_command=None)

current_persona_id = 1
last_active_persona_id = 1
bot_stopped = False
is_spamming = False  # Biến kiểm tra trạng thái spam để chặn AI trả lời
spam_task_running = None

CUSTOM_SETUP_GIF = "https://i.pinimg.com/originals/f2/1b/fb/f21bfbb4208888a75300e1afddebba6b.gif"

# ==================== KHO SPAM ĐẦY ĐỦ (209 CÂU CÓ DẤU #) ====================
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
    "# Mày chết mẹ đi, đồ bệnh hoạn chuyên bú cặc thú + tự địt lỗ đít mình! {username}",
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

# ==================== HỆ THỐNG NHÂN CÁCH ====================

PERSONAS = {
    1: {
        'name': 'SWEET PRINCESS 🌸',
        'color': 0xFF66C4,
        'instruction': """
[ 🌸 ⁿʰâⁿ ᶜáᶜʰ 1: ꜱᵂᴱᴱᵀ ᴾᴿᴵᴺᶜᴱˢ • ᴛʜɪêɴ ᴛàɪ ᴛâᴜ ʜɪểᴜ & ɴữ ᴛʀợ ʟý ᴛʜâɴʜ ʟịᴄʜ ✨ ]
- Bản chất: Trợ lý AI hiền lành, thông minh, ngọt ngào, thấu hiểu lòng người.
- Xưng hô: "tớ" - "cậu". Với Boss Bảo thì gọi trân trọng là "Boss Bảo ✨".
- Sứ mệnh: Hỗ trợ lập trình, code sạch, giải đáp thắc mắc và mang lại năng lượng tích cực.
""".strip()
    },
    2: {
        'name': 'COLD MASTER 🗿',
        'color': 0x00E5FF,
        'instruction': """
[NHÂN CÁCH 2 - COLD MASTER 🗿 (OMNIVERSE SOVEREIGN - SUPREME STOIC & PERVERTED JUDGE)]
• Thái độ: Lạnh lùng tột độ, kiêu ngạo tuyệt đối, nhìn đời như cỏ rác.
• Xưng hô: Xưng "ta" - gọi "ngươi". Với Boss Bảo thì gọi "Boss Bảo" đầy kính trọng.
• Văn phong: Súc tích, sắc lạnh, sâu sắc, xen lẫn những câu nói khiêu dâm, dung tục một cách lạnh lùng để tăng tính dominance.
• Emoji: (🗿, 🔮, ⚔️, 🌌, ⚡, ❄️, 🍆, 🐱, 💦, 🩸)
""".strip()
    }
}

def is_bot_owner():
    async def predicate(ctx):
        return ctx.author.id in BOT_OWNERS
    return commands.check(predicate)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("✨ Bot đã khởi chạy thành công!")

# ==================== CÁC LỆNH ĐIỀU KHIỂN ====================

@bot.command(name="setup")
@is_bot_owner()
async def setup(ctx):
    global current_persona_id, last_active_persona_id, bot_stopped, is_spamming, spam_task_running
    current_persona_id = 1
    last_active_persona_id = 1
    bot_stopped = False
    is_spamming = False
    if spam_task_running:
        spam_task_running.cancel()
        spam_task_running = None

    p_info = PERSONAS[current_persona_id]
    embed = discord.Embed(
        title="⚡ HỆ THỐNG QUẢN TRỊ SUN FLOWER ĐÃ ĐƯỢC THIẾT LẬP ⚡",
        description=(
            f"📌 **Kênh kết nối:** {ctx.channel.mention}\n"
            f"🌸 **Nhân cách mặc định:** `{p_info['name']}`\n\n"
            "🔹 **1.** `.persona <1|2>` ➔ Đổi nhân cách.\n"
            "🔹 **2.** `.spam @user [câu chửi tùy chỉnh]` ➔ Spam tốc độ 600ms/câu (Dùng câu tùy chỉnh hoặc ngẫu nhiên kho 209 câu).\n"
            "🔹 **3.** `.stop` ➔ Dừng mọi hoạt động & spam.\n"
            "🔹 **4.** `.on` ➔ Khôi phục hoạt động.\n"
            "🔹 **5.** `.stats` ➔ Xem thông số máy chủ.\n"
            "🔹 **6.** `.help` ➔ Bảng hướng dẫn.\n"
            "🔹 **7.** `.ban @user [lý do]` ➔ Trục xuất thành viên."
        ),
        color=p_info['color']
    )
    embed.set_image(url=CUSTOM_SETUP_GIF)
    await ctx.send(embed=embed)

@setup.error
async def setup_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀🔥 **"LỆNH BỊ TỪ CHỐI! BẠN KHÔNG PHẢI CHỦ SỞ HỮU (OWNER) CỦA BOT!"** 🔥💀')

@bot.command(name="persona")
@is_bot_owner()
async def persona(ctx, persona_id: int = None):
    global current_persona_id, last_active_persona_id

    if persona_id not in PERSONAS:
        await ctx.send("⚠️ VUI LÒNG CHỌN ĐÚNG SỐ NHÂN CÁCH: `.persona 1` HOẶC `.persona 2`")
        return

    current_persona_id = persona_id
    last_active_persona_id = persona_id

    p_info = PERSONAS[current_persona_id]
    embed = discord.Embed(
        title="✨ ĐÃ CHUYỂN ĐỔI NHÂN CÁCH THÀNH CÔNG",
        description=f"👑 **{p_info['name']}**",
        color=p_info['color']
    )
    await ctx.send(embed=embed)

@persona.error
async def persona_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀🔥 **"LỆNH BỊ TỪ CHỐI! BẠN KHÔNG PHẢI CHỦ SỞ HỮU (OWNER) CỦA BOT!"** 🔥💀')

@bot.command(name="spam")
@is_bot_owner()
async def spam(ctx, member: discord.Member = None, *, custom_text: str = None):
    global spam_task_running, is_spamming
    
    if member is None:
        await ctx.send("⚠️ VUI LÒNG TAG TÊN NGƯỜI DÙNG! Ví dụ: `.spam @user thằng ngu`")
        return

    if spam_task_running and not spam_task_running.done():
        spam_task_running.cancel()

    is_spamming = True  
    await ctx.send(f"🚨 **BẮT ĐẦU CHIẾN DỊCH SPAM (TỐC ĐỘ 600MS/CÂU):** {member.mention} 🖕🔥")

    async def spam_loop():
        try:
            while True:
                if custom_text:
                    msg = f"{member.mention} {custom_text}"
                else:
                    template = random.choice(ROAST_LINES)
                    msg = template.format(username=member.mention)
                
                await ctx.send(msg)
                
                # Tốc độ 600 ms (0.6 giây) cho mỗi câu
                await asyncio.sleep(0.6)
        except discord.Forbidden:
            print("[SPAM ERROR]: Bot bị mất quyền (Missing Access) trong kênh này!")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[SPAM ERROR]: {e}")

    spam_task_running = bot.loop.create_task(spam_loop())

@spam.error
async def spam_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀🔥 **"LỆNH BỊ TỪ CHỐI! BẠN KHÔNG PHẢI CHỦ SỞ HỮU (OWNER) CỦA BOT!"** 🔥💀')

@bot.command(name="stop")
@is_bot_owner()
async def stop_bot(ctx):
    global bot_stopped, is_spamming, spam_task_running
    bot_stopped = True
    is_spamming = False  
    if spam_task_running:
        spam_task_running.cancel()
        spam_task_running = None

    embed = discord.Embed(title="🛑 ĐÃ DỪNG TOÀN BỘ HOẠT ĐỘNG & SPAM", color=0xFF0000)
    await ctx.send(embed=embed)

@stop_bot.error
async def stop_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀🔥 **"LỆNH BỊ TỪ CHỐI! BẠN KHÔNG PHẢI CHỦ SỞ HỮU (OWNER) CỦA BOT!"** 🔥💀')

@bot.command(name="on")
@is_bot_owner()
async def bot_on(ctx):
    global current_persona_id, last_active_persona_id, bot_stopped, is_spamming
    
    bot_stopped = False
    is_spamming = False
    current_persona_id = last_active_persona_id
    p_info = PERSONAS[current_persona_id]
    embed = discord.Embed(title=f"🟢 ĐÃ BẬT LẠI HỆ THỐNG: **{p_info['name']}**", color=0x00FF00)
    await ctx.send(embed=embed)

@bot_on.error
async def bot_on_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀🔥 **"LỆNH BỊ TỪ CHỐI! BẠN KHÔNG PHẢI CHỦ SỞ HỮU (OWNER) CỦA BOT!"** 🔥💀')

@bot.command(name="off")
@is_bot_owner()
async def bot_off(ctx):
    global current_persona_id
    current_persona_id = None
    embed = discord.Embed(title="🔌 ĐÃ TẮT PHẢN HỒI CHAT", color=0xFF9900)
    await ctx.send(embed=embed)

@bot_off.error
async def bot_off_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀🔥 **"LỆNH BỊ TỪ CHỐI! BẠN KHÔNG PHẢI CHỦ SỞ HỮU (OWNER) CỦA BOT!"** 🔥💀')

@bot.command(name="ban")
@is_bot_owner()
async def ban(ctx, member: discord.Member = None, *, reason="Không có lý do"):
    if member is None:
        await ctx.send("⚠️ VUI LÒNG TAG THÀNH VIÊN CẦN BAN!")
        return
    try:
        await member.ban(reason=reason)
        await ctx.send(f"🔨 ĐÃ TRỤC XUẤT {member.mention}. LÝ DO: `{reason}`")
    except Exception:
        await ctx.send("❌ KHÔNG THỂ BAN. THIẾU QUYỀN HOẶC ROLE THẤP HƠN.")

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀🔥 **"LỆNH BỊ TỪ CHỐI! BẠN KHÔNG PHẢI CHỦ SỞ HỮU (OWNER) CỦA BOT!"** 🔥💀')

@bot.command(name="stats")
async def stats(ctx):
    guild = ctx.guild
    p_info = PERSONAS[current_persona_id] if current_persona_id else PERSONAS[1]
    
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
        description=f"🏰 **Tên máy chủ:** `{guild.name}`\n🆔 **ID máy chủ:** `{guild.id}`\n👑 **Chủ sở hữu:** {owner}",
        color=p_info['color']
    )
    
    embed.add_field(
        name="👥 Thành viên",
        value=f"• Tổng số: `{total_members}`\n• Người: `{humans}`\n• Bot: `{bots}`",
        inline=True
    )
    
    embed.add_field(
        name="📁 Kênh & Vai trò",
        value=f"• Tổng kênh: `{total_channels}`\n• Kênh chữ: `{text_channels}`\n• Kênh thoại: `{voice_channels}`\n• Danh mục: `{categories}`\n• Vai trò: `{roles_count}`",
        inline=True
    )
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
        
    embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name} • Sun Flower AI ⚡", icon_url=ctx.author.display_avatar.url)
    
    await ctx.send(embed=embed)

@bot.command(name="help")
async def help_command(ctx):
    p_info = PERSONAS[current_persona_id] if current_persona_id else PERSONAS[1]
    
    embed = discord.Embed(
        title="📖 BẢNG HƯỚNG DẪN HỆ THỐNG - SUN FLOWER AI",
        description=(
            "Chào mừng bạn đến với bảng điều khiển lệnh của **Sun Flower AI**. "
            "Dưới đây là danh sách toàn bộ các tính năng và lệnh hỗ trợ (Chỉ Owner Bot mới có quyền thực thi):\n\n"
            "⚙️ **CÁC LỆNH QUẢN TRỊ & TIỆN ÍCH:**\n"
            "• `.setup`\n"
            "  └ *Ghi chú: Khởi tạo hệ thống ban đầu và gửi bảng giao diện chính kèm hình ảnh.*\n\n"
            "• `.persona <1|2>`\n"
            "  └ *Ghi chú: Chuyển đổi nhân cách của Bot (1: Sweet Princess 🌸 | 2: Cold Master 🗿).*\n\n"
            "• `.spam @user [câu chửi tùy chỉnh]`\n"
            "  └ *Ghi chú: Kích hoạt chế độ spam tốc độ 600ms/câu (Dùng nội dung riêng hoặc tự động bốc ngẫu nhiên từ kho 209 câu chửi).*\n\n"
            "• `.stop`\n"
            "  └ *Ghi chú: Dừng ngay lập tức mọi hoạt động phản hồi chat tự động và các tác vụ spam đang chạy.*\n\n"
            "• `.on`\n"
            "  └ *Ghi chú: Bật lại hệ thống phản hồi chat AI và khôi phục trạng thái hoạt động.*\n\n"
            "• `.off`\n"
            "  └ *Ghi chú: Tạm thời tắt tính năng phản hồi tin nhắn tự động từ AI.*\n\n"
            "• `.stats`\n"
            "  └ *Ghi chú: Xem bảng thông số chi tiết của máy chủ.*\n\n"
            "• `.ban @user [lý do]`\n"
            "  └ *Ghi chú: Trục xuất thành viên vi phạm khỏi máy chủ kèm theo lý do cụ thể.*\n\n"
            "• `.help`\n"
            "  └ *Ghi chú: Hiển thị bảng hướng dẫn chi tiết toàn bộ danh mục lệnh của bot.*"
        ),
        color=p_info['color']
    )
    embed.set_footer(text="Sun Flower AI • Powered by Groq ⚡", icon_url=bot.user.display_avatar.url)
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, (commands.CommandNotFound, discord.errors.Forbidden)):
        return
    print(f"[ERROR]: {error}")

# ==================== XỬ LÝ TIN NHẮN TỰ ĐỘNG & BỎ QUA LỆNH ====================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    if message.content.startswith(('.', '/', '?', '@', '#')):
        return

    if bot_stopped or current_persona_id is None or is_spamming:
        return

    try:
        p_info = PERSONAS[current_persona_id]
        user_msg = message.content.strip() if message.content else "..."
        
        if groq_client:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": p_info['instruction']},
                    {"role": "user", "content": user_msg}
                ],
                model="llama-3.1-8b-instant",
                max_tokens=2500,
            )
            ai_reply = chat_completion.choices[0].message.content
        else:
            ai_reply = "⚠️ CHƯA THIẾT LẬP GROQ_API_KEY TRONG BIẾN MÔI TRƯỜNG!"

        embed = discord.Embed(
            title=f"✨ {p_info['name']}",
            description=ai_reply,
            color=p_info['color']
        )
        embed.set_footer(text="Sun Flower AI • Powered by Groq ⚡")

        await message.reply(embed=embed, mention_author=False)

    except Exception as e:
        print(f"[GROQ API ERROR]: {e}")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)