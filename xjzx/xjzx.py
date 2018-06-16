from flask_script import Manager
from app import create_app
from config import DevelopConfig

app = create_app(DevelopConfig)
manager = Manager(app)

from models import db

db.init_app(app)

#扩展自定义的命令
from super_command import CreateAdminCommand,RegisterUserCommand,HourLoginCommand
#扩展创建管理员的命令
manager.add_command('createadmin',CreateAdminCommand)
manager.add_command('registeruser',RegisterUserCommand)
manager.add_command('hourlogin',HourLoginCommand)


from flask_migrate import Migrate, MigrateCommand
Migrate(app, db)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    # print(app.url_map)
    manager.run()
