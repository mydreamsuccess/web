# 导入蓝图模块
from flask import Blueprint
# 创建蓝图对象
# 如果希望用户直接访问，则不添加前缀
news_blueprint=Blueprint('news',__name__)