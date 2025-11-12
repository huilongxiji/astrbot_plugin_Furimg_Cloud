import os
from pathlib import Path

SYJ_RANDOM = "https://cloud.foxtail.cn/api/function/random?type="
SYJ_RANDOM_NAME = "https://cloud.foxtail.cn/api/function/random?name="
PICTURES_URL = "https://cloud.foxtail.cn/api/function/pictures?model=1&picture="
PULLLIST_URL = "https://cloud.foxtail.cn/api/function/pulllist?type=0&name="
PICTURE_URL = "https://cloud.foxtail.cn/api/function/pullpic?model=1&picture="

CHECK = "https://cloud.foxtail.cn/api/check"
LOGIN = "https://cloud.foxtail.cn/api/account/login"
TKAPPLY = "https://cloud.foxtail.cn/api/account/tkapply"
TKQUERY = "https://cloud.foxtail.cn/api/account/tkquery"

# 插件信息
PLUGIN_NAME = "Furimg_Cloud"
PLUGIN_AUTHOR = "huilongxiji"
PLUGIN_DESC = "这个是兽云祭官方api对接插件，用来获取一张精选的furry图片，可以是毛毛照片也可以是兽兽插画或者设定图，该插件的所有图片均来自群友投稿"
PLUGIN_VERSION = "1.0.1"
PLUGIN_REPO = "https://github.com/GEMILUXVII/astrbot_plugin_Furimg_Cloud"

# 路径常量
PLUGIN_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

# DATA_DIR通过StarTools.get_data_dir动态获取
# 这里只是定义一个占位变量，真正的目录会在初始化时设置
# 正确的数据目录应该是：data/plugin_data/cloudrank
DATA_DIR = None  # 由主模块初始化
