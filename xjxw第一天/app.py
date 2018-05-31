from flask import Flask

# 引入python自带的包
import logging
from logging.handlers import RotatingFileHandler
from flask_wtf import CSRFProtect
# 定义一个返回app对象的函数
def create_app(config):
    app=Flask(__name__)
    # 程序加载配置
    app.config.from_object(config)

    CSRFProtect(app)
    from flask_session import Session
    Session(app)
    # 导入蓝图对象
    from views_admin import admin_blueprint
    from views_news import news_blueprint
    from views_user import user_blueprint
    # 在app上注册蓝图
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(news_blueprint)
    app.register_blueprint(user_blueprint)

    # 设置日志等级
    # logging.basicConfig(level=logging.DEBUG)
    # file_log_hander=RotatingFileHandler(config.BASE_DIR+"/logs/xjzx.log",maxBytes=1024*1024*100,backupCount=10)
    # formatter=logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # file_log_hander.setFormatter(formatter)
    # logging.getLogger().addHandler(file_log_hander)
    # app.logging_xjzx=logging


    import logging
    from logging.handlers import RotatingFileHandler
    # 设置日志的记录等级
    logging.basicConfig(level=logging.DEBUG)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler(config.BASE_DIR + "/logs/xjzx.log", maxBytes=1024 * 1024 * 100,
                                           backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)
    app.logger_xjzx = logging

    return app
