# 导入蓝图模块
from flask import Blueprint, render_template, jsonify
# 创建蓝图对象
# 如果希望用户直接访问，则不添加前缀
from flask import current_app

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
    comment_list = NewsComment.query. \
        filter_by(news_id=news_id, comment_id=None). \
        order_by(NewsComment.like_count.desc(), NewsComment.id.desc())
    # 返回的数据为json，所以需要转换
    comment_list2 = []
    # 获取当前用户点赞列表
    if 'user_id' in session:
        user_id = session['user_id']
        print(user_id)
        commentid_list = current_app.redis_client.lrange('commentup%d' % user_id, 0, -1)
        print(comment_list)
        commentid_list = [int(cid) for cid in commentid_list]
    else:
        commentid_list = []

    # 将数据转换成字典
    for comment in comment_list:
        # 获取当前用户是否对这个评论点赞
        if comment.id in commentid_list:
            is_like = 1
        else:
            is_like = 0
        comment_dict = {
            'id': comment.id,
            'like_count': comment.like_count,
            'msg': comment.msg,
            'create_time': comment.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            'nick_name': comment.user.nick_name,
            'avatar': comment.user.avatar_url,
            'is_like': is_like
        }
        # 将评论的回复也包含在字典中
        '''
        {
        id:**,
        msg:**
        list:[
            {},{},{}
            ]
        }
        '''
        cback_list = []
        for cback in comment.comments:
            cback_dict = {
                'nick_name': cback.user.nick_name,
                'msg': cback.msg
            }
            cback_list.append(cback_dict)
        comment_dict['cback_list'] = cback_list

        comment_list2.append(comment_dict)
    return jsonify(comment_list=comment_list2)


# @news_blueprint.route('/comment/list/<int:news_id>')
# def commentlist(news_id):
#     comment_list=NewsComment.query.filter_by(news_id=news_id).order_by(NewsComment.like_count.desc())
#     comment_list2=[]
#     for comment in comment_list:
#         comment_dict={
#             'id':comment.id,
#             'like_count':comment.like_count,
#             'msg':comment.msg,
#             'create_time':comment.create_time,
#             'nick_name':comment.user.nick_name,
#             'avatar':comment.user.avatar_url
#         }
#         comment_list2.append(comment_dict)
#     return jsonify(comment_list=comment_list2)

@news_blueprint.route('/commentup/<int:comment_id>', methods=['POST'])
def commentup(comment_id):
    # 接收操作行为，1为点赞，2为取消
    action = int(request.form.get('action', '1'))
    # 获取用户的编号
    if 'user_id' not in session:
        return jsonify(result=2)
    user_id = session['user_id']
    # 将评论的点赞数量+1
    comment = NewsComment.query.get(comment_id)
    print(999999999999999)
    if action == 1:
        comment.like_count += 1
    else:
        comment.like_count -= 1
    db.session.commit()
    print(222222222)
    if action == 1:
        print(666666666666666)
        print(type(user_id))
        print(type(comment_id))
        assert isinstance(current_app, object)
        current_app.redis_client.rpush('commentup%d' % user_id,comment_id)
    else:
        current_app.redis_client.lrem('commentup%d' % user_id, 0,comment_id)

    return jsonify(result=1, like_count=comment.like_count)


@news_blueprint.route('/commentback/<int:comment_id>', methods=['POST'])
def commentback(comment_id):
    # 用户user_id回复了评论comment_id,内容为：msg
    msg = request.form.get('msg')
    news_id = int(request.form.get('news_id'))
    if not all([msg]):
        return jsonify(result=1)
    if 'user_id' not in session:
        return jsonify(result=2)
    user_id = session['user_id']
    # 创建评论对象
    comment = NewsComment()
    comment.news_id = news_id
    comment.user_id = user_id
    comment.comment_id = comment_id
    comment.msg = msg
    # 提交到数据库
    db.session.add(comment)
    db.session.commit()
    return jsonify(result=3)


@news_blueprint.route('/userfollow', methods=['POST'])
def userfollow():
    # 当前登录用户user_id关注提交的用户follow_user_id
    # 处理1：向对象的列表中添加对象
    # 处理2：将粉丝数增加
    action = int(request.form.get('action', '1'))
    follow_user_id = request.form.get('follow_user_id')
    follow_user = UserInfo.query.get(follow_user_id)
    # 将follow_user加到login_user
    if 'user_id' not in session:
        return jsonify(result=1)
    login_user = UserInfo.query.get(session['user_id'])
    if action == 1:  # 关注
        login_user.follow_user.append(follow_user)
        # 处理2：粉丝量+1
        follow_user.follow_count += 1
    else:  # 取消关注
        login_user.follow_user.remove(follow_user)
        # 处理2：粉丝量+1
        follow_user.follow_count -= 1
    # 提交到数据库
    db.session.commit()

    return jsonify(result=2, follow_count=follow_user.follow_count)
