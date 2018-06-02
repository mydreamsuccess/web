# 导入蓝图模块
from flask import Blueprint, render_template, jsonify
# 创建蓝图对象
# 如果希望用户直接访问，则不添加前缀
from flask import request
from flask import session,abort

from models import NewsCategory, UserInfo, NewsInfo,db,NewsComment

news_blueprint = Blueprint('news', __name__)


@news_blueprint.route('/')
def index():
    category_list = NewsCategory.query.all()
    if "user_id" in session:
        user = UserInfo.query.get(session["user_id"])
    else:
        user = None

    count_list = NewsInfo.query.order_by(NewsInfo.click_count.desc())[0:6]
    return render_template('news/index.html', category_list=category_list, title="首页", user=user, count_list=count_list)


@news_blueprint.route('/newslist')
def newslist():
    page = int(request.args.get('page', '1'))
    category_id = int(request.args.get('category_id', '0'))
    pagination = NewsInfo.query
    if category_id:
        pagination = pagination.filter_by(category_id=category_id)
    pagination = pagination.order_by(NewsInfo.update_time.desc()).paginate(page, 4, False)
    news_list = pagination.items
    print(news_list)
    news_list2 = []
    for news in news_list:
        news_dict = {
            'id': news.id,
            'title': news.title,
            'summary': news.summary,
            'pic_url': news.pic_url,
            'user_nick_name': news.user.nick_name,
            'user_avatar': news.user.avatar_url,
            "user_id": news.user_id,
            "update_time": news.update_time,
            'category_id': category_id
        }
        news_list2.append(news_dict)
    return jsonify(
        page=page,
        news_list=news_list2

    )


@news_blueprint.route('/<int:news_id>')
def detail(news_id):
    news = NewsInfo.query.get(news_id)
    if news is None:
        abort(404)
    if 'user_id' in session:
        user=UserInfo.query.get(session["user_id"])
    else:
        user=None
    news.click_count += 1
    db.session.commit()
    count_list=NewsInfo.query.order_by(NewsInfo.click_count.desc())[0:6]


    return render_template('news/detail.html',news=news,title="文章详情页",user=user,count_list=count_list)

@news_blueprint.route('/collect/<int:news_id>',methods=["POST"])
def collect(news_id):
    action=int(request.form.get('action','1'))
    news=NewsInfo.query.get(news_id)
    if news is None:
        return jsonify(result=1)
    if 'user_id' not in session:
        return jsonify(result=2)
    user=UserInfo.query.get(session['user_id'])
    print(user)
    if action==1:
        print(666666666666)
        if news  in user.news_collect:
            print(88888888888888)
            return jsonify(result=4)
        print(00000000000000000)
        user.news_collect.append(news)

    else:
        print(555555555555555)
        if news not in user.news_collect:
            print(444444444444444)
            return jsonify(result=4)
        print(8888888888888888)
        user.news_collect.remove(news)
    print(2222222222222222222)
    db.session.commit()
    return jsonify(result=3)

@news_blueprint.route('/comment/add',methods=['POST'])
def comment():
    dict1=request.form
    news_id=dict1.get('news_id')
    msg=dict1.get('msg')
    if not all([news_id,msg]):
        return jsonify(result=1)
    news=NewsInfo.query.get(news_id)
    if news is None:
        return jsonify(result=2)
    if 'user_id' not in session:
        return jsonify(result=3)
    print(news.comment_count)
    news.comment_count += 1
    comment=NewsComment()
    comment.news_id=int(news_id)
    comment.user_id=session['user_id']
    comment.msg=msg
    db.session.add(comment)
    db.session.commit()
    return jsonify(result=4,comment_count=news.comment_count)

@news_blueprint.route('/comment/list/<int:news_id>')
def commentlist(news_id):
    comment_list=NewsComment.query.filter_by(news_id=news_id).order_by(NewsComment.like_count.desc())
    comment_list2=[]
    for comment in comment_list:
        comment_dict={
            'id':comment.id,
            'like_count':comment.like_count,
            'msg':comment.msg,
            'create_time':comment.create_time,
            'nick_name':comment.user.nick_name,
            'avatar':comment.user.avatar_url
        }
        comment_list2.append(comment_dict)
    return jsonify(comment_list=comment_list2)