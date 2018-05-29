import  redis
import os


class Config(object):
    DEBUG=False
    # 配置数据库连接
    SQLALCHEMY_DATABASE_URI="mysql://name:password@host:port/database"
    SQLALCHEMY_TRACK_MODIFICATIONS=True

#     redis配置
    REDIS_HOST="localhost"
    REDIS_POTR="6379"
    REDIS_DB=9

#     session
    SECRET_KEY='itheima'
    SESSION_TYPR="redis"  #指定session保存到rides中
    SESSION_USE_SIGNER=True #唯一签名，通过键和值来从rides中取值
    SESSION_REDIS=redis.StrictRedis(host=REDIS_HOST,port=REDIS_POTR,db=REDIS_DB)
    PERMANANT_SESSION_LIFETIME=60*60*24*14 #session 有效期
    #获取文件路径
    BASE_DIR=os.path.dirname(os.path.abspath(__file__))
    # 变量名不变 七牛云配置
    # QINU_AK='Fwp5Pua_-cWafzw4yi7WmWdk5AP-sQSJWQwBL_7x'
    # QINU_SK='BdL_waCxtp63z3_lqO-jXPBirmZmaiuXHDlmsGyN'
    # QINIU_BUCKET=''
    # QINIU_URL=''

class DevelopConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@localhost:3306/xjzx9'
    SQLALCHEMY_TRACK_MODIFICATIONS = True