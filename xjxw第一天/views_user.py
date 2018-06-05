import re

from  datetime import datetime
from flask import Blueprint,make_response,session
from flask import current_app,render_template

from utils.captcha.captcha import captcha
from utils.ytx_sdk import ytx_send
from flask import request
from flask import jsonify
import random
from models import db,UserInfo,NewsInfo,NewsCategory
user_blueprint=Blueprint('user',__name__,url_prefix='/user')
import functools
from flask import redirect
from utils.qiniu_xjzx import upload_pic
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

def login_hour_count():
    now=datetime.now()
    keys="login%d_%d_%d" % (now.year,now.month,now.day)
    login_prop=['08:15', '09:15', '10:15', '11:15', '12:15', '13:15', '14:15', '15:15', '16:15', '17:15', '18:15', '19:15']
    for index,item in enumerate(login_prop):
        if now.hour<index+8 or(now.hour==index+8 and now.minute>15):
            count=current_app.redis_client.hget(keys, item)
            if count is None:
                count =1
            else:
                count=int(count)
                count +=1
            current_app.redis_client.hset(keys,item,count)
            break
    # if now.hour>=9 and now.minute>=15:
    #     count = int(current_app.redis_client.hget(keys, "19:15"))
    #     count += 1
    #     current_app.redis_client.hset(keys, "19:15", count)
    else:
        count = current_app.redis_client.hget(keys, '19:15')
        if count is None:
            count = 1
        else:
            count = int(count)
            count += 1
        current_app.redis_client.hset(keys, "19:15", count)

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
            login_hour_count()
            session['user_id']=user.id
            return jsonify(result=3,avatar=user.avatar_url,nick_name=user.nick_name)
        else:
            return jsonify(result=4)
    else:
        return jsonify(result=2)


@user_blueprint.route('/logout',methods=['POST'])
def logout():
    session.pop('user_id')
    return jsonify(result=1)

def login_required(f):
    @functools.wraps(f)
    def fun2(*args,**kwargs):
        if "user_id" not in session:
            return redirect("/")
        return f(*args,**kwargs)
    return fun2


@user_blueprint.route('/')
@login_required
def index():
    user_id=session['user_id']
    user=UserInfo.query.get(user_id)
    return render_template("news/user.html",user=user,title="用户中心")


@user_blueprint.route('/base',methods=["GET","POST"])
@login_required
def base():
    user_id=session["user_id"]
    user=UserInfo.query.get(user_id)
    print("111111111111111111111111111111111")
    if request.method=='GET':
        print("999999999999999999999999")
        return render_template("news/user_base_info.html",user=user)

    elif request.method=='POST':
        dict1=request.form
        signature=dict1.get('signature')
        nick_name=dict1.get('nick_name')
        gender=dict1.get('gender')
        # print(45454)
        print(signature)
        print(nick_name)
        print(gender)
        # print(7878)
        user.signature=signature
        user.nick_name=nick_name
        if gender == 'True':
            gender = True
        else:
            gender = False
        user.gender = gender  # True if gender=='True' else False
        # print("22222222222")
        try:
            db.session.commit()
        except:
            current_app.logger_xjzx.error('修改用户基本信息连接数据库失败')
            return jsonify(result=2)
        # print("8888888888")
        return jsonify(result=1)

@user_blueprint.route('/pic',methods=['GET','POST'])
@login_required
def pic():
    user_id=session["user_id"]
    user=UserInfo.query.get(user_id)
    if request.method=='GET':
        return render_template('news/user_pic_info.html',user=user)
    elif request.method=='POST':
        f1=request.files.get('avatar')
        from utils.qiniu_xjzx import upload_pic
        f1_name=upload_pic(f1)
        user.avatar=f1_name
        db.session.commit()
        return jsonify(result=1,avatar_url=user.avatar_url)

@user_blueprint.route('/follow')
@login_required
def follow():
    user_id=session['user_id']
    user=UserInfo.query.get(user_id)
    page=int(request.args.get("page","1"))
    pagination=user.follow_user.paginate(page,4,False)
    user_list=pagination.items
    total_page=pagination.pages
    print(total_page)

    return render_template('news/user_follow.html',user_list=user_list,total_page=total_page,page=page)

@user_blueprint.route('/pwd',methods=["GET","POST"])
@login_required
def pwd():
    if request.method=="GET":
        return render_template('news/user_pass_info.html')
    elif request.method=='POST':
        msg="修改成功"
        dict1=request.form
        current_pwd=dict1.get("current_pwd")
        new_pwd=dict1.get("new_pwd")
        new_pwd2=dict1.get('new_pwd2')
        print(current_pwd)
        print(new_pwd)
        print(new_pwd2)
        if not all([current_pwd,new_pwd2,new_pwd]):
            return render_template("news/user_pass_info.html",msg="密码不能为空")
        if not re.match(r"[a-zA-Z0-9_]{6,20}",current_pwd):
            return render_template("news/user_pass_info.html",msg="当前密码错误")
        if not re.match(r"[a-zA-Z0-9_]{6,20}",new_pwd):
            return render_template("news/user_pass_info.html",msg="新密码格式错误（长度为6-20，内容为大小写a-z字母，0-9数字，下划线_）")
        if new_pwd !=new_pwd2:
            return render_template("news/user_pass_info.html",msg="两个新密码不一致")
        user_id=session["user_id"]
        user=UserInfo.query.get(user_id)
        if not user.check_pwd(current_pwd):
            return render_template("news/user_pass_info.html",msg="当前密码错误")
        user.password=new_pwd
        db.session.commit()
        return render_template("news/user_pass_info.html",msg="密码修改成功")


@user_blueprint.route('/collect')
@login_required
def collect():
    user_id=session["user_id"]
    user=UserInfo.query.get(user_id)
    page=int(request.args.get('page','1'))
    pagination=user.news_collect.order_by(NewsInfo.id.desc()).paginate(page,6,False)
    news_list=pagination.items
    total_page=pagination.pages
    return render_template('news/user_collection.html',news_list=news_list,total_page=total_page,page=page)

@user_blueprint.route('/release',methods=["GET","POST"])
@login_required
def release():
    category_list = NewsCategory.query.all()
    news_id=request.args.get("news_id")
    print(news_id)
    if request.method=="GET":
        if news_id is None:
            print("1212")
            return render_template('news/user_news_release.html',category_list=category_list,news=None)
        else:
            news=NewsInfo.query.get(int(news_id))
            print("121214")
            return render_template("news/user_news_release.html",category_list=category_list,news=news)
    elif request.method=="POST":
        dict1=request.form
        title=dict1.get("title")
        category_id=dict1.get("category")
        summary=dict1.get("summary")
        content=dict1.get("content")
        news_pic=request.files.get("news_pic")
        print(title)
        print(category_id)
        print(summary)
        print(content)
        print(news_pic)
        if news_id is None:
            if not all([title,category_id,summary,content,news_pic]):
                return render_template("news/user_news_release.html",category_list=category_list,msg="请将数据填写完整",news=None)
        else:
            if not all([title,category_id,summary,content]):
                return render_template("news/user_news_release.html",category_list=category_list,msg="请将数据填写完整")
        if news_pic:
            filename=upload_pic(news_pic)
        if news_id is None:
            news=NewsInfo()

        else:
            news=NewsInfo.query.get(news_id)
        news.category_id=int(category_id)
        if news_pic:
            news.pic=filename
        # print("11111111111111111111111111111")
        news.title=title
        news.summary=summary
        news.content=content
        news.status=1
        news.update_time=datetime.now()
        news.user_id=session["user_id"]
        # print("22222222222222222222222222222222")
        db.session.add(news)
        # print("555555555555555555555555555555")
        db.session.commit()
        # print("88888888888888888888888")

        return redirect("/user/newslist")


@user_blueprint.route('/newslist')
@login_required
def newslist():
    user_id=session["user_id"]
    user=UserInfo.query.get(user_id)
    page=int(request.args.get('page','1'))
    pagination=user.news.order_by(NewsInfo.id.desc()).paginate(page,6,False)
    news_list=pagination.items
    total_page=pagination.pages
    return render_template('news/user_news_list.html',news_list=news_list,page=page,total_page=total_page)