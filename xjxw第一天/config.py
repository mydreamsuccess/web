import redis
import os


class Config(object):
    DEBUG=False
    # 配置数据库连接
    # SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@localhost:3306/xjzx9'
    SQLALCHEMY_DATABASE_URI="mysql://name:password@host:port/database"
    SQLALCHEMY_TRACK_MODIFICATIONS=True
#
#     redis配置
    REDIS_HOST="localhost"
    REDIS_PORT="6379"
    REDIS_DB=9

#     session
    SECRET_KEY='itheima'


    SESSION_TYPE="redis"  #指定session保存到rides中
    SESSION_USE_SIGNER=True #唯一签名，通过键和值来从rides中取值
    SESSION_REDIS=redis.StrictRedis(host=REDIS_HOST,port=REDIS_PORT,db=REDIS_DB)
    PERMANANT_SESSION_LIFETIME=60*60*24*14 #session 有效期
    #获取文件路径
    BASE_DIR=os.path.dirname(os.path.abspath(__file__))
    # 变量名不变 七牛云配置
    QINIU_AK = 'H999S3riCJGPiJOity1GsyWufw3IyoMB6goojo5e'
    QINIU_SK = 'uOZfRdFtljIw7b8jr6iTG-cC6wY_-N19466PXUAb'
    QINIU_BUCKET = 'itcast20171104'
    QINIU_URL = 'http://oyvzbpqij.bkt.clouddn.com/'

class DevelopConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@localhost:3306/xjzx9'
    SQLALCHEMY_TRACK_MODIFICATIONS = True