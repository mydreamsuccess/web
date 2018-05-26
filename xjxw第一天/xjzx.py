# 导入扩展命令包
from flask_script import Manager
# 导入app对象
from app import create_app
# 导入config对象
from config import DevelopConfig
# 导入数据库对象
from models import db
# 导入迁移包
from flask_migrate import Migrate,MigrateCommand
app=create_app(DevelopConfig)
# 扩展命令
manager=Manager(app)
# 链接数据库和app对象
db.init_app(app)
# 进行迁移命令
Migrate(app,db)
manager.add_command('db',MigrateCommand)




if __name__ == '__main__':
    manager.run()
