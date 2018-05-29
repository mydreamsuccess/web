# 导入蓝图模块
from flask import Blueprint,render_template
# 创建蓝图对象
# 如果希望用户直接访问，则不添加前缀
news_blueprint=Blueprint('news',__name__)

@news_blueprint.route('/')
def index():
    return render_template('news/index.html')