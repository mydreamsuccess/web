from flask import Flask
# 导入蓝图对象
from views_admin import admin_blueprint
from views_news import news_blueprint
from views_user import user_blueprint
# 定义一个返回app对象的函数
def create_app(config):
    app=Flask(__name__)
    # 程序加载配置
    app.config.from_object(config)
    # 在app上注册蓝图
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(news_blueprint)
    app.register_blueprint(user_blueprint)

    return app