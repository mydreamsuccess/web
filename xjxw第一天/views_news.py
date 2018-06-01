# 导入蓝图模块
from flask import Blueprint,render_template, jsonify
# 创建蓝图对象
# 如果希望用户直接访问，则不添加前缀
from flask import request
from flask import session

from models import NewsCategory, UserInfo, NewsInfo

news_blueprint=Blueprint('news',__name__)

@news_blueprint.route('/')
def index():
    category_list=NewsCategory.query.all()
    if "user_id" in session:
        user=UserInfo.query.get(session["user_id"])
    else:
        user=None
    count_list=NewsInfo.query.order_by(NewsInfo.click_count.desc())[0:6]
    return render_template('news/index.html',category_list=category_list,title="首页",user=user,count_list=count_list)

@news_blueprint.route('/newslist')
def newslist():
    page=int(request.args.get('page','1'))
    category_id=int(request.args.get('category_id','0'))
    pagination=NewsInfo.query
    if category_id:
        pagination=pagination.filter_by(category_id=category_id)
    pagination=pagination.order_by(NewsInfo.update_time.desc()).paginate(page,4,False)
    news_list=pagination.items
    print(news_list)
    news_list2=[]
    for news in news_list:
        news_dict={
            'id':news.id,
            'title':news.title,
            'summary':news.summary,
            'pic_url':news.pic_url,
            'user_nick_name':news.user.nick_name,
            'user_avatar':news.user.avatar_url,
            "user_id":news.user_id,
            "update_time":news.update_time,
            'category_id':category_id
        }
        news_list2.append(news_dict)
    return jsonify(
        page=page,
        news_list=news_list2

    )