from flask import Blueprint, jsonify
from flask import abort
from flask import current_app
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from datetime import datetime

from models import UserInfo, NewsInfo, db, NewsCategory
from utils.qiniu_xjzx import upload_pic

admin_blueprint = Blueprint('admin', __name__, url_prefix='/admin')


@admin_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('admin/login.html')
    elif request.method == 'POST':
        # 接收
        dict1 = request.form
        mobile = dict1.get('username')
        pwd = dict1.get('password')
        # 验证
        if not all([mobile, pwd]):
            abort(404)
        # 处理
        user = UserInfo.query.filter_by(isAdmin=True, mobile=mobile).first()
        if user is None:
            return render_template(
                'admin/login.html',
                mobile=mobile,
                pwd=pwd,
                msg='账号错误'
            )
        # 判断密码是否正确
        if user.check_pwd(pwd):
            session['admin_user_id'] = user.id
            return redirect('/admin/')
        else:
            return render_template(
                'admin/login.html',
                mobile=mobile,
                pwd=pwd,
                msg='密码错误'
            )


@admin_blueprint.route('/logout')
def logout():
    del session['admin_user_id']
    return redirect('/admin/login')


# 使用请求勾子，进行登录验证
# 使用蓝图注册勾子，表示只有在请求这个蓝图的视图时，才会执行这个请求勾子
@admin_blueprint.before_request
def before_request():
    # 判断是否访问登录视图，如果是则不需要验证
    if request.path != '/admin/login':
        if 'admin_user_id' not in session:
            return redirect('/admin/login')
        # 使用g变量，就表示一次请求响应中的全局变量
        # 一般结合勾子使用，设置后可以在视图、模板中访问这个值
        g.user = UserInfo.query.get(session['admin_user_id'])


@admin_blueprint.route('/')
def index():
    return render_template(
        'admin/index.html',
    )


@admin_blueprint.route('/user_count')
def user_count():
    # 用户总数
    user_total = UserInfo.query.filter_by(isAdmin=False).count()
    # 用户月新增数:2018-6-3,2018-6-4  2018-6-1 0:0:0
    '''
    分析：获取当前年、当前月，构造时间y-m-1 0:0:0
    只要比这个时间大，则说明是当月新注册
    '''
    now = datetime.now()
    month_first = datetime(now.year, now.month, 1)
    user_month = UserInfo.query. \
        filter_by(isAdmin=False). \
        filter(UserInfo.create_time >= month_first). \
        count()
    # 用户日新增数
    day_first = datetime(now.year, now.month, now.day)
    user_day = UserInfo.query. \
        filter_by(isAdmin=False). \
        filter(UserInfo.create_time >= day_first). \
        count()
    # 用户登录活跃数：按小时进行统计
    key = 'login%d_%d_%d' % (now.year, now.month, now.day)
    hour_list = current_app.redis_client.hkeys(key)
    hour_list = [hour.decode() for hour in hour_list]
    count_list = []
    for hour in hour_list:
        count_list.append(int(current_app.redis_client.hget(key, hour)))

    return render_template(
        'admin/user_count.html',
        user_total=user_total,
        user_month=user_month,
        user_day=user_day,
        hour_list=hour_list,
        count_list=count_list
    )


@admin_blueprint.route('/user_list')
def user_list():
    page = int(request.args.get('page', '1'))
    pagination = UserInfo.query. \
        filter(UserInfo.isAdmin == False). \
        order_by(UserInfo.id.desc()). \
        paginate(page, 9, False)
    user_list1 = pagination.items
    total_page = pagination.pages

    return render_template(
        'admin/user_list.html',
        user_list1=user_list1,
        page=page,
        total_page=total_page
    )


@admin_blueprint.route('/news_review')
def news_review():
    return render_template('admin/news_review.html')


@admin_blueprint.route('/news_review_detail/<int:news_id>', methods=['GET', 'POST'])
def news_review_detail(news_id):
    news = NewsInfo.query.get(news_id)
    if request.method == 'GET':
        return render_template('admin/news_review_detail.html', news=news)
    elif request.method == 'POST':
        action = request.form.get('action')
        reason = request.form.get('reason')
        if action == 'accept':
            news.status = 2
        else:
            news.status = 3
            news.reason = reason
        db.session.commit()
        return redirect('/admin/news_review')


@admin_blueprint.route('/news_review_json')
def news_review_json():
    page = int(request.args.get('page', '1'))
    input_txt = request.args.get('input_txt')
    pagination = NewsInfo.query
    if input_txt:
        pagination = pagination.filter(NewsInfo.title.contains(input_txt))
    pagination = pagination.order_by(NewsInfo.id.desc()).paginate(page, 10, False)
    news_list1 = pagination.items
    total_page = pagination.pages
    # 转json数据
    news_list2 = []
    for news in news_list1:
        news_dict = {
            'id': news.id,
            'title': news.title,
            'create_time': news.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': news.status
        }
        news_list2.append(news_dict)
    return jsonify(news_list=news_list2, total_page=total_page)


@admin_blueprint.route('/news_edit')
def news_edit():
    return render_template('admin/news_edit.html')


@admin_blueprint.route('/news_edit_detail/<int:news_id>', methods=['GET', 'POST'])
def news_edit_detail(news_id):
    news = NewsInfo.query.get(news_id)
    if request.method == 'GET':
        category_list = NewsCategory.query.all()
        return render_template(
            'admin/news_edit_detail.html',
            news=news,
            category_list=category_list
        )
    elif request.method == 'POST':
        dict1 = request.form
        title = dict1.get('title')
        category_id = dict1.get('category_id')
        summary = dict1.get('summary')
        content = dict1.get('content')
        # 接收图片文件
        pic = request.files.get('pic')
        if pic:
            pic_name = upload_pic(pic)
            news.pic = pic_name
        # 修改对象的属性
        news.title = title
        news.category_id = int(category_id)
        news.summary = summary
        news.content = content
        news.update_time = datetime.now()
        # 保存
        db.session.commit()
        # 响应
        return redirect('/admin/news_edit')


@admin_blueprint.route('/news_edit_json')
def news_edit_json():
    # 接收
    input_txt = request.args.get('input_txt')
    page = int(request.args.get('page', '1'))
    # 处理
    pagination = NewsInfo.query
    if input_txt:
        pagination = pagination.filter(NewsInfo.title.contains(input_txt))
    pagination = pagination.order_by(NewsInfo.id.desc()).paginate(page, 10, False)
    # 获取当前页数据
    news_list1 = pagination.items
    # 获取总页码值
    total_page = pagination.pages
    # 将news对象转json
    news_list2 = []
    for news in news_list1:
        news_dict = {
            'id': news.id,
            'title': news.title,
            'create_time': news.create_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        news_list2.append(news_dict)
    # 响应
    return jsonify(news_list=news_list2, total_page=total_page)


@admin_blueprint.route('/news_type')
def news_type():
    return render_template('admin/news_type.html')


@admin_blueprint.route('/news_type_list')
def news_type_list():
    category_list1 = NewsCategory.query.all()
    category_list2 = []
    for category in category_list1:
        category_dict = {
            'id': category.id,
            'name': category.name
        }
        category_list2.append(category_dict)
    return jsonify(category_list=category_list2)


@admin_blueprint.route('/news_type_add', methods=['POST'])
def news_type_add():
    name = request.form.get('name')
    # 验证：名称是否存在
    name_exists = NewsCategory.query.filter_by(name=name).count()
    if name_exists > 0:
        return jsonify(result=2)
    # 添加
    category = NewsCategory()
    category.name = name
    # 提交到数据库
    db.session.add(category)
    db.session.commit()
    # 响应
    return jsonify(result=1)


@admin_blueprint.route('/news_type_edit', methods=['POST'])
def news_type_edit():
    cid = request.form.get('id')
    name = request.form.get('name')
    # 判断名称是否重复
    name_exists = NewsCategory.query.filter_by(name=name).count()
    if name_exists > 0:
        return jsonify(result=2)
    # 修改
    category = NewsCategory.query.get(cid)
    category.name = name
    # 保存到数据库
    db.session.commit()
    # 响应
    return jsonify(result=1)
