from datetime import datetime

from flask import Blueprint, make_response, session, jsonify
from flask import current_app
from flask import redirect
from flask import render_template
from flask import request
from models import db, UserInfo, NewsInfo, NewsCategory

user_blueprint = Blueprint('user', __name__, url_prefix='/user')


@user_blueprint.route('/image_yzm')
def image_yzm():
    from utils.captcha.captcha import captcha
    # name表示一个随机的名称
    # yzm表示验证码字符串
    # buffer文件的二进制数据
    name, yzm, buffer = captcha.generate_captcha()

    # 将验证码字符串存入session中，用于后续请求时进行对比
    session['image_yzm'] = yzm

    response = make_response(buffer)
    # 默认返回的内容会被当作text/html解析，如下代码告诉浏览器解释为图片
    response.mimetype = 'image/png'

    return response


@user_blueprint.route('/sms_yzm')
def sms_yzm():
    # 获取数据：手机号，图片验证码
    dict1 = request.args
    mobile = dict1.get('mobile')
    image_yzm = dict1.get('image_yzm')

    # 对比图片验证码
    if image_yzm != session['image_yzm']:
        return jsonify(result=1)

    # 判断手机号是否已经存在

    # 随机生成一个数字（4位）
    import random
    yzm = random.randint(1000, 9999)

    # 保存到session
    session['sms_yzm'] = yzm

    from utils.ytx_sdk import ytx_send
    # ytx_send.sendTemplateSMS(mobile,{yzm,5},1)
    print(yzm)

    return jsonify(result=2)


@user_blueprint.route('/register', methods=['POST'])
def register():
    # 1.接收数据
    dict1 = request.form
    mobile = dict1.get('mobile')
    image_yzm = dict1.get('image_yzm')
    sms_yzm = dict1.get('sms_yzm')
    pwd = dict1.get('pwd')

    # 2.验证数据的有效性
    # 判断所有数据是否存在
    if not all([mobile, image_yzm, sms_yzm, pwd]):
        return jsonify(result=1)
    # 判断图片验证码是否正确
    if image_yzm != session['image_yzm']:
        return jsonify(result=2)
    # 判断短信验证码是否正确
    if int(sms_yzm) != session['sms_yzm']:
        return jsonify(result=3)
    # 判断密码的长度
    import re
    if not re.match(r'[a-zA-Z0-9_]{6,20}', pwd):
        return jsonify(result=4)
    # 判断手机号是否存在
    mobile_count = UserInfo.query.filter_by(mobile=mobile).count()
    if mobile_count > 0:
        return jsonify(result=5)

    # 3.创建对象
    user = UserInfo()
    user.nick_name = mobile
    user.mobile = mobile
    user.password = pwd

    # 4.提交
    try:
        db.session.add(user)
        db.session.commit()
    except:
        current_app.logger_xjzx.error('注册用户时数据库访问失败')
        return jsonify(result=6)

    # 返回响应
    return jsonify(result=7)


def login_hour_count():
    now = datetime.now()
    login_key = 'login%d_%d_%d' % (now.year, now.month, now.day)
    login_prop = ['08:15', '09:15', '10:15', '11:15', '12:15', '13:15', '14:15', '15:15', '16:15', '17:15', '18:15', '19:15']

    for index,item in enumerate(login_prop):
        if now.hour < index + 8 or (now.hour == index + 8 and now.minute <= 15):
            count=current_app.redis_client.hget(login_key, item)
            if count is None:
                count=1
            else:
                count = int(count)
                count += 1
            current_app.redis_client.hset(login_key, item, count)
            break
    if now.hour >= 19 and now.minute >= 15:
        count = current_app.redis_client.hget(login_key, item)
        if count is None:
            count = 1
        else:
            count = int(count)
            count += 1
        count += 1
        current_app.redis_client.hset(login_key, '19:15', count)
    # if now.hour<8 or (now.hour==8 and now.minute<=15):
    #     count=int(current_app.redis_client.hget(login_key,'08:15'))
    #     count+=1
    #     current_app.redis_client.hset(login_key,'08:15',count)
    # elif now.hour<9 or (now.hour==9 and now.minute<=15):
    #     count=int(current_app.redis_client.hget(login_key,'09:15'))
    #     count+=1
    #     current_app.redis_client.hset(login_key,'09:15',count)
    # elif now.hour<10 or (now.hour==10 and now.minute<=15):
    #     count=int(current_app.redis_client.hget(login_key,'10:15'))
    #     count+=1
    #     current_app.redis_client.hset(login_key,'10:15',count)


@user_blueprint.route('/login', methods=['POST'])
def login():
    # 接收
    dict1 = request.form
    mobile = dict1.get('mobile')
    pwd = dict1.get('pwd')

    # 验证
    if not all([mobile, pwd]):
        return jsonify(result=1)

    # 处理：查询select * from user_info where ... limit 0,1
    user = UserInfo.query.filter_by(mobile=mobile).first()
    # 如果mobile存在则返回对象，不存在则返回None
    if user:
        # 判断密码是否正确
        if user.check_pwd(pwd):
            # 登录成功
            # 统计每小时登录个数
            login_hour_count()
            # 进行状态保持
            session['user_id'] = user.id
            # 将头像、昵称称回给浏览器显示
            return jsonify(result=3, avatar=user.avatar_url, nick_name=user.nick_name)
        else:
            # 密码错误
            return jsonify(result=4)
    else:
        # 提示mobile错误
        return jsonify(result=2)


@user_blueprint.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id')
    return jsonify(result=1)


@user_blueprint.route('/show')
def show():
    session['hello'] = 'flask'
    if 'user_id' in session:
        return 'ok'
    else:
        return 'no'


import functools


# 定义验证登录的装饰器
def login_required(f):
    @functools.wraps(f)  # 返回f函数的名称，而不是用fun2代替这个函数的名称
    def fun2(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/')
        # 在视图函数上添加的装饰器，必须要将视图返回的response，再返回，传递给浏览器
        return f(*args, **kwargs)

    return fun2


@user_blueprint.route('/')
@login_required
def index():
    # 从session中获取用户编号，已经登录过，所以可以获取到
    user_id = session['user_id']
    # 查询用户对象，传递到模板中用于显示
    user = UserInfo.query.get(user_id)

    return render_template(
        'news/user.html',
        user=user,
        title='用户中心'
    )


@user_blueprint.route('/base', methods=['GET', 'POST'])
@login_required
def base():
    # 获取当前登录的用户编号
    user_id = session['user_id']
    # 查询当前用户对象
    user = UserInfo.query.get(user_id)

    # 如果是get请求则展示数据
    if request.method == 'GET':
        # 传递到模板中用于展示
        return render_template('news/user_base_info.html', user=user)
    elif request.method == 'POST':
        # 如果是post请求则修改数据并保存
        # 接收数据
        dict1 = request.form
        signature = dict1.get('signature')
        nick_name = dict1.get('nick_name')
        gender = dict1.get('gender')
        # 查询对象(展示和修改都需要，所以写在了上面)
        # 修改属性
        user.signature = signature
        user.nick_name = nick_name
        if gender == 'True':
            gender = True
        else:
            gender = False
        user.gender = gender  # True if gender=='True' else False
        # 提交保存
        try:
            db.session.commit()
        except:
            current_app.logger_xjzx.error('修改用户基本信息连接数据库失败')
            return jsonify(result=2)
        # 响应
        return jsonify(result=1)


@user_blueprint.route('/pic', methods=['GET', 'POST'])
@login_required
def pic():
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)
    if request.method == 'GET':
        return render_template('news/user_pic_info.html', user=user)
    elif request.method == 'POST':
        # 接收文件
        f1 = request.files.get('avatar')

        # 保存文件到七牛云，并返回文件名
        from utils.qiniu_xjzx import upload_pic
        f1_name = upload_pic(f1)

        # 将文件名保存到数据库
        user.avatar = f1_name

        # 提交
        db.session.commit()

        # 响应
        return jsonify(result=1, avatar_url=user.avatar_url)


@user_blueprint.route('/follow')
@login_required
def follow():
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)
    # 接收当前页码值参数
    page = int(request.args.get('page', '1'))
    # 对数据进行分页
    pagination = user.follow_user.paginate(page, 4, False)
    # 获取当前页的数据
    user_list = pagination.items
    # 获取总页数
    total_page = pagination.pages

    return render_template(
        'news/user_follow.html',
        user_list=user_list,
        total_page=total_page,
        page=page
    )


@user_blueprint.route('/pwd', methods=['GET', 'POST'])
@login_required
def pwd():
    if request.method == 'GET':
        # 为用户提供页面，输入密码
        return render_template('news/user_pass_info.html')
    elif request.method == 'POST':
        # 接收用户填写的数据，进行密码修改
        msg = '修改成功'
        # 1.接收数据
        dict1 = request.form
        current_pwd = dict1.get('current_pwd')
        new_pwd = dict1.get('new_pwd')
        new_pwd2 = dict1.get('new_pwd2')
        # 2.进行验证
        # 2.0验证数据是否存在
        if not all([current_pwd, new_pwd, new_pwd2]):
            return render_template(
                'news/user_pass_info.html',
                msg='密码都不能为空'
            )
        # 2.1验证密码格式
        import re
        if not re.match(r'[a-zA-Z0-9_]{6,20}', current_pwd):
            return render_template(
                'news/user_pass_info.html',
                msg='当前密码错误'
            )
        if not re.match(r'[a-zA-Z0-9_]{6,20}', new_pwd):
            return render_template(
                'news/user_pass_info.html',
                msg='新密码格式错误（长度为6-20，内容为大小写a-z字母，0-9数字，下划线_）'
            )
        # 2.2两个密码是否一致
        if new_pwd != new_pwd2:
            return render_template(
                'news/user_pass_info.html',
                msg='两个新密码不一致'
            )

        # 2.3旧密码是否正确
        user_id = session['user_id']
        user = UserInfo.query.get(user_id)
        if not user.check_pwd(current_pwd):
            return render_template(
                'news/user_pass_info.html',
                msg='当前密码错误'
            )

        # 3.修改
        user.password = new_pwd
        # 4.提交到数据库
        db.session.commit()
        # 5.响应
        return render_template(
            'news/user_pass_info.html',
            msg='密码修改成功'
        )


@user_blueprint.route('/collect')
@login_required
def collect():
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)
    # 获取当前页码的值
    page = int(request.args.get('page', '1'))
    # 通过对象的关联属性获取相关数据
    pagination = user.news_collect.order_by(NewsInfo.id.desc()).paginate(page, 6, False)
    # 获取当前页的数据
    news_list = pagination.items
    # 获取总页数
    total_page = pagination.pages

    return render_template(
        'news/user_collection.html',
        news_list=news_list,
        total_page=total_page,
        page=page
    )


@user_blueprint.route('/release', methods=['GET', 'POST'])
@login_required
def release():
    # 查询所有的分类，供编辑人员选择
    category_list = NewsCategory.query.all()
    # 接收新闻的编号
    news_id = request.args.get('news_id')

    if request.method == 'GET':
        if news_id is None:
            # 展示页面
            return render_template(
                'news/user_news_release.html',
                category_list=category_list,
                news=None
            )
        else:
            # 如果有新闻编号则进行修改，所以需要查询展示
            news = NewsInfo.query.get(int(news_id))
            return render_template(
                'news/user_news_release.html',
                category_list=category_list,
                news=news
            )
    elif request.method == 'POST':
        # 新闻的添加处理
        # 1.接收请求
        dict1 = request.form
        title = dict1.get('title')
        category_id = dict1.get('category')
        summary = dict1.get('summary')
        content = dict1.get('content')
        # 接收新闻图片
        news_pic = request.files.get('news_pic')

        if news_id is None:
            # 2.验证
            # 2.1.验证数据不为空
            if not all([title, category_id, summary, content, news_pic]):
                return render_template(
                    'news/user_news_release.html',
                    category_list=category_list,
                    msg='请将数据填写完整',
                    news=None
                )
        else:
            if not all([title, category_id, summary, content]):
                # 如果有新闻编号则进行修改，所以需要查询展示
                news = NewsInfo.query.get(int(news_id))

                return render_template(
                    'news/user_news_release.html',
                    category_list=category_list,
                    msg='请将数据填写完整',
                    news=news
                )

        # 上传图片
        if news_pic:
            from utils.qiniu_xjzx import upload_pic
            filename = upload_pic(news_pic)

        # 3.添加
        if news_id is None:
            news = NewsInfo()
        else:
            news = NewsInfo.query.get(news_id)
        news.category_id = int(category_id)
        if news_pic:
            news.pic = filename
        news.title = title
        news.summary = summary
        news.content = content
        news.status = 1
        news.update_time = datetime.now()
        news.user_id = session['user_id']

        # 4.提交到数据库
        db.session.add(news)
        db.session.commit()

        # 5.响应：转到列表页
        return redirect('/user/newslist')


@user_blueprint.route('/newslist')
@login_required
def newslist():
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)
    # 接收当前页码值
    page = int(request.args.get('page', '1'))
    # 查询当前页数据
    pagination = user.news.order_by(NewsInfo.update_time.desc()).paginate(page, 6, False)
    # 获取当前页的数据
    news_list = pagination.items
    # 获取总页数
    total_page = pagination.pages

    return render_template(
        'news/user_news_list.html',
        news_list=news_list,
        page=page,
        total_page=total_page
    )
