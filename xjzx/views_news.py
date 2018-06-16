from flask import Blueprint, render_template, jsonify
from flask import abort
from flask import current_app
from flask import request
from flask import session

from models import db, NewsCategory, UserInfo, NewsInfo, NewsComment

# 如果希望用户直接访问，则不添加前缀
news_blueprint = Blueprint('news', __name__)


@news_blueprint.route('/')
def index():
    # 查询分类，用于展示
    category_list = NewsCategory.query.all()

    # 判断用户是否登录
    if 'user_id' in session:
        user = UserInfo.query.get(session['user_id'])
    else:
        user = None

    # 查询点击量最高的6条数据==>select * from ... order by ... limit 6
    count_list = NewsInfo.query.order_by(NewsInfo.click_count.desc())[0:6]

    return render_template(
        'news/index.html',
        category_list=category_list,
        title='首页',
        user=user,
        count_list=count_list
    )


@news_blueprint.route('/newslist')
def newslist():
    # 接收当前页码值
    page = int(request.args.get('page', '1'))
    # 查询数据并分页
    pagination = NewsInfo.query

    # 接收分类的编号，进行指定分类的查询
    category_id = int(request.args.get('category_id', '0'))
    if category_id:
        pagination = pagination.filter_by(category_id=category_id)

    pagination = pagination.order_by(NewsInfo.update_time.desc()).paginate(page, 4, False)
    # 获取当前页数据
    news_list = pagination.items
    # 此处不需要总页数，因为界面上不需要页码链接

    # 因为NewsInfo类型的对象，在js中是无法识别的，所以需要改成字典对象再返回
    news_list2 = []
    for news in news_list:
        news_dict = {
            'id': news.id,
            'title': news.title,
            'summary': news.summary,
            'pic_url': news.pic_url,
            'user_avatar': news.user.avatar_url,
            'user_id': news.user_id,
            'user_nick_name': news.user.nick_name,
            'update_time': news.update_time,
            'category_id': news.category_id
        }
        news_list2.append(news_dict)

    return jsonify(
        page=page,
        news_list=news_list2
    )

    pass


@news_blueprint.route('/<int:news_id>')
def detail(news_id):
    news = NewsInfo.query.get(news_id)
    # 如果提供的编号不能查到一个新闻对象，则抛出404错误
    if news is None:
        abort(404)

    # 实现右上角登录状态的判断
    if 'user_id' in session:
        user = UserInfo.query.get(session['user_id'])
    else:
        user = None

    # 查询点击量排行，并传递到模板
    # 将点击量+1
    news.click_count += 1
    db.session.commit()
    # 查询点击量最高的6条数据==>select * from ... order by ... limit 6
    count_list = NewsInfo.query.order_by(NewsInfo.click_count.desc())[0:6]
    # 将对象传递到模板中展示数据
    return render_template(
        'news/detail.html',
        news=news,
        title='文章详情页',
        user=user,
        count_list=count_list
    )


@news_blueprint.route('/collect/<int:news_id>', methods=['POST'])
def collect(news_id):
    # 接收参数action：当前是收藏还是取消收藏，默认为1,表示收藏
    action = int(request.form.get('action', '1'))
    # 获取当前新闻对象
    news = NewsInfo.query.get(news_id)
    if news is None:
        return jsonify(result=1)
    # 获取当前用户对象
    if 'user_id' not in session:
        return jsonify(result=2)
    # 如果用户登录则查询用户对象
    user = UserInfo.query.get(session['user_id'])
    # 判断是收藏还是取消
    if action == 1:  # 收藏
        # 判断当前新闻是否已经被用户收藏
        if news in user.news_collect:
            return jsonify(result=4)
        # 添加收藏：最终会将数据存储到关系表tb_news_collect
        user.news_collect.append(news)
    else:  # 取消收藏
        # 判断当前是否被收藏
        if news not in user.news_collect:
            return jsonify(result=4)
        # 取消：从列表中将数据删除
        user.news_collect.remove(news)
    # 提交到数据库
    db.session.commit()
    # 响应
    return jsonify(result=3)


@news_blueprint.route('/comment/add', methods=['POST'])
def comment_add():
    # 接收数据:新闻编号，评论内容
    dict1 = request.form
    news_id = dict1.get('news_id')
    msg = dict1.get('msg')
    # 验证
    if not all([news_id, msg]):
        return jsonify(result=1)
    # 判断新闻对象是否存在
    news = NewsInfo.query.get(news_id)
    if news is None:
        return jsonify(result=2)
    # 判断用户是否登录
    if 'user_id' not in session:
        return jsonify(result=3)
    # 将新闻对象的评论量+1
    news.comment_count += 1
    # 保存
    comment = NewsComment()
    comment.news_id = int(news_id)
    comment.user_id = session['user_id']
    comment.msg = msg
    db.session.add(comment)
    db.session.commit()
    # 响应
    return jsonify(result=4, comment_count=news.comment_count)


@news_blueprint.route('/comment/list/<int:news_id>')
def commentlist(news_id):
    # 根据新闻编号，查询对应的评论信息
    comment_list = NewsComment.query. \
        filter_by(news_id=news_id, comment_id=None). \
        order_by(NewsComment.like_count.desc(), NewsComment.id.desc())
    # 返回的数据为json，所以需要转换
    comment_list2 = []
    # 获取当前用户点赞列表
    if 'user_id' in session:
        user_id = session['user_id']
        # # 从config中读取redis服务器的配置
        # host = current_app.config.get('REDIS_HOST')
        # port = current_app.config.get('REDIS_PORT')
        # db_redis = current_app.config.get('REDIS_DB')
        # 将用户对评论存储到redis中
        # import redis
        # redis_client = redis.StrictRedis(host=host, port=port, db=db_redis)
        commentid_list = current_app.redis_client.lrange('commentup%d' % user_id, 0, -1)
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
    if action == 1:
        comment.like_count += 1
    else:
        comment.like_count -= 1
    db.session.commit()

    if action == 1:
        current_app.redis_client.rpush('commentup%d' % user_id, comment_id)
    else:
        current_app.redis_client.lrem('commentup%d' % user_id, 0, comment_id)

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

    return jsonify(result=2,follow_count=follow_user.follow_count)
