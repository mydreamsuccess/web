
from flask import Blueprint
from flask import g
from flask import request,current_app,jsonify
from models import UserInfo,NewsInfo
from flask import render_template,redirect,abort,session
from datetime import datetime

admin_blueprint=Blueprint('admin',__name__,url_prefix='/admin')

@admin_blueprint.before_request
def before_request():
    if request.path!="/admin/login":
        if "admin_user_id" not in session:
           return redirect("/admin/login")
        g.user=UserInfo.query.get(session['admin_user_id'])

@admin_blueprint.route('/login',methods=['GET','POST'])
def login():
    # 接收
    if request.method=='GET':
        return render_template("admin/login.html")
    elif request.method=='POST':
        dict1=request.form
        mobile=dict1.get('username')
        pwd=dict1.get('password')
    # 验证
        if not all([mobile,pwd]):
            abort(404)

        # 处理
        user=UserInfo.query.filter_by(mobile=mobile,isAdmin=True).first()
        # 判断
        if user:
            if user.check_pwd(pwd):
                session['admin_user_id']=user.id
                return redirect("/admin/")
            return render_template('admin/login.html',mobile=mobile,pwd=pwd,msg="密码错误")
        else:
            return render_template('admin/login.html',mobile=mobile,pwd=pwd,msg='账号错误')

@admin_blueprint.route('/')
def index():
    return render_template("admin/index.html")

@admin_blueprint.route('/user_list')
def user_list():
    page=int(request.args.get('page','1'))
    pagination=UserInfo.query.filter_by(isAdmin=False).paginate(page,9,False)
    user_list=pagination.items
    total_page=pagination.pages
    return render_template("admin/user_list.html",user_list=user_list,total_page=total_page,page=page)


@admin_blueprint.route('/news_edit')
def new_edit():
    return render_template("admin/news_edit.html")


@admin_blueprint.route('/news_review')
def news_review():
    return render_template("admin/news_review.html")
@admin_blueprint.route('/news_review_json')
def news_review_json():
    page=request.args.get('page','1')
    pagination=NewsInfo.query.order_by(NewsInfo.id.desc()).paginate(page,'10',False)
    news_list=pagination.items
    total_page=pagination.items
    news_list1 = []
    for news in news_list:
        news_dict1 = {
            "id":news.id,
            "title":news.title,
            "create_time":news.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            "status":news.status
        }
        news_list1.append(news_dict1)
    return jsonify(news_list=news_list1,total_page=total_page)


@admin_blueprint.route('/user_count')
def user_count():
    # 用户总数
    user_num=UserInfo.query.filter_by(isAdmin=False).count()
    print(user_num)
    # 用户日新增数
    now=datetime.now()
    day_first=datetime(now.year,now.month,now.day)
    user_day=UserInfo.query.filter_by(isAdmin=False).filter(UserInfo.create_time>=day_first).count()
    # 用户月新增数
    month_first=datetime(now.year,now.month,1)
    user_month=UserInfo.query.filter(UserInfo.isAdmin==False,UserInfo.create_time>=month_first).count()
    # 用户登入小时活跃度
    keys="login%d_%d_%d" % (now.year,now.month,now.day)

    hour_list=current_app.redis_client.hkeys(keys)
    hour_list=[hour.decode() for hour in hour_list]
    cout_list=[]
    for hour in hour_list:
        cout_list.append(int(current_app.redis_client.hget(keys,hour)))

    return render_template("admin/user_count.html",user_num=user_num,user_day=user_day,user_month=user_month,hour_list=hour_list,cout_list=cout_list)


@admin_blueprint.route('/news_type')
def news_type():
    return render_template("admin/news_type.html")

@admin_blueprint.route('/logout')
def logout():
    # print(888888)
    del session['admin_user_id']
    # print(1111)
    return redirect('/admin/login')

@admin_blueprint.route('/news_review_detail')
def news_review_detail():
    return render_template("admin/news_review_detail.html")

@admin_blueprint.route('/news_edit_detail')
def news_edit_detail():
    return render_template("admin/news_edit_detail.html")