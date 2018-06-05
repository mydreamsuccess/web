from flask_script.commands import Command
from datetime import datetime
from models import UserInfo,db
from flask import current_app
import random


class CreateAdminCommand(Command):
    def run(self):
        # 接收
        mobile=input("请输入账号：")
        pwd=input("请输入密码：")
        # 验证
        user_ex=UserInfo.query.filter_by(mobile=mobile).count()
        if user_ex>0:
            print("账号已存在，请重新输入")
            return
        user=UserInfo()
        user.mobile=mobile
        user.password=pwd
        user.isAdmin=True
        db.session.add(user)
        db.session.commit()
        print("创建账号成功！")
       # 保存

# 创建用户数据

class UserNumCommand(Command):
    def run(self):
        now=datetime.now()
        user_list1=[]
        for i in range(1000):
            user=UserInfo()
            user.nick_name=str(i)
            user.mobile=str(i)
            # user.password
            user.create_time=datetime(2018,random.randint(1,6),random.randint(1,28))
            user_list1.append(user)
        db.session.add_all(user_list1)
        db.session.commit()

class HourLoginCommand(Command):
    def run(self):
        now=datetime.now()
        # hash()
        key="login%d_%d_%d" % (now.year,now.month,now.day)
        for i in range(8,20):
            current_app.redis_client.hset(key,'%02d:15' % i,random.randint(200,2000))