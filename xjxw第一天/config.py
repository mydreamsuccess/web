class Config(object):
    DEBUG=False
    # 配置数据库连接
    SQLALCHEMY_DATABASE_URI="mysql://root:mysql@localhost:3306/xjzx9"
    SQLALCHEMY_TRACK_MODIFICATIONS=True

class DevelopConfig(Config):
    DEBUG = True