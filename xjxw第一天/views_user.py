import re
from flask import Blueprint,make_response,session
from flask import current_app

from utils.captcha.captcha import captcha
from utils.ytx_sdk import ytx_send
from flask import request
from flask import jsonify
import random
from models import db,UserInfo
user_blueprint=Blueprint('user',__name__,url_prefix='/user')

@user_blueprint.route('/image_yzm')
def image_yzm():
    name,yzm,buffer=captcha.generate_captcha()
    session['image_yzm']=yzm
    response=make_response(buffer)
    response.mimetype='image/png'
    return response

@user_blueprint.route('/sms_yzm')
def sms_yzm():
    # print("00000000000000000000000000000")
    dict1=request.args
    mobile=dict1.get('mobile')
    image_yzm=dict1.get('image_yzm')
    # print("11111111111111111111111111111111111111")
    if image_yzm !=session['image_yzm']:
        return jsonify(data=1)
    yzm=random.randint(1000,9999)
    session['sms_yzm']=yzm
    # ytx_send.sendTemplateSMS(mobile,{yzm,5},1)
    print(yzm)
    return jsonify(result=2)


@user_blueprint.route('/register',methods=['POST'])
def register():
#     接受数据
    dict1=request.form
    mobile=dict1.get('mobile')
    image_yzm=dict1.get('image_yzm')
    sms_yzm=dict1.get('sms_yzm')
    pwd=dict1.get('pwd')
    print(type(sms_yzm))
    print(type(pwd))
#      验证数据的有效性
    if not all ([mobile,image_yzm,sms_yzm,pwd]):
        return jsonify(result=1)
    if image_yzm!=session['image_yzm']:
        return jsonify(result=2)

    if int(sms_yzm)!=session['sms_yzm']:
        return jsonify(result=3)
    if not re.match(r"[a-zA-Z0-9_]{6,20}",pwd):
        return jsonify(result=4)
    # print("88888888888888888888888888888888")


    mobile_count = UserInfo.query.filter_by(mobile=mobile).count()
    # print("5555555555555555555555555555555555555")
    if mobile_count>0:
        return jsonify(result=5)
    user= UserInfo()
    user.nick_name=mobile
    user.mobile=mobile
    user.password=pwd

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        print(e)
        current_app.logger_xjzx.error('注册用户时数据库访问失败')
        return jsonify(result=6)
    # print("6666666666666666666666666666666666666666")
    return jsonify(result=7)


@user_blueprint.route('/login',methods=['Post'])
def login():
    dict1=request.form
    mobile=dict1.get('mobile')
    pwd=dict1.get('pwd')

    if not all([mobile,pwd]):
        return jsonify(result=1)
    user=UserInfo.query.filter_by(mobile=mobile).first()
    if user:
        if user.check_pwd(pwd):
            session['user_id']=user.id
            return jsonify(result=3,avatar=user.avatar,nick_name=user.nick_name)
        else:
            return jsonify(result=4)
    else:
        return jsonify(result=2)


@user_blueprint.route('/logout',methods=['POST'])
def logout():
    session.pop('user_id')
    return jsonify(result=1)
