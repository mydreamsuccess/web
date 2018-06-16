function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(function () {
    //获取评论数据
    vue_comment_list = new Vue({
        el: '.comment_list_con',
        delimiters: ['[[', ']]'],//将语法中的{{换成[[，将}}换成]]
        data: {
            comment_list: []
        }
    });
    get_comment_list();

    // 收藏
    $(".collection").click(function () {
        $.post('/collect/' + $('#news_id').val(), {
            'csrf_token': $('#csrf_token').val()
        }, function (data) {
            if (data.result == 2) {
                //未登录，则显示登录页面
                $('.login_btn').click();
            } else if (data.result == 3) {
                //收藏成功
                $('.collection').hide();
                $('.collected').show();
            }
        });
    })

    // 取消收藏
    $(".collected").click(function () {
        $.post('/collect/' + $('#news_id').val(), {
            'csrf_token': $('#csrf_token').val(),
            'action': 2
        }, function (data) {
            //对于其它返回值，是用于进行非法请求处理的，而此处为正常请求，不需要写其它值的处理
            if (data.result == 3) {
                //取消收藏成功
                $('.collection').show();
                $('.collected').hide();
            }
        });
    })

    // 评论提交
    $(".comment_form").submit(function (e) {
        e.preventDefault();
        $.post('/comment/add', {
            'news_id': $('#news_id').val(),
            'csrf_token': $('#csrf_token').val(),
            'msg': $('#msg').val()
        }, function (data) {
            if (data.result == 1) {
                alert('请输入评论内容');
            } else if (data.result == 4) {
                $('#msg').val('');
                $('.comment').text(data.comment_count);
                $('.comment_count>span').text(data.comment_count);
                get_comment_list();
            }
        });
    })

    $('.comment_list_con').delegate('a,input', 'click', function () {

        var sHandler = $(this).prop('class');

        if (sHandler.indexOf('comment_reply') >= 0) {
            $(this).next().toggle();
        }

        if (sHandler.indexOf('reply_cancel') >= 0) {
            $(this).parent().toggle();
        }

        if (sHandler.indexOf('comment_up') >= 0) {
            var $this = $(this);
            var action = 1;
            if (sHandler.indexOf('has_comment_up') >= 0) {
                action = 2;
                // $this.removeClass('has_comment_up')
            } else {
                action = 1;
                // $this.addClass('has_comment_up')
            }

            $.post('/commentup/' + $this.attr('commentid'), {
                'csrf_token': $('#csrf_token').val(),
                'action': action
            }, function (data) {
                if (data.result == 1) {
                    //处理成功,修改数量和样式
                    if (action == 1) {
                        $this.addClass('has_comment_up');
                    } else {
                        $this.removeClass('has_comment_up');
                    }
                    $this.find('em').text(data.like_count);
                } else if (data.result == 2) {
                    $('.login_btn').click();
                }
            });


        }

        if (sHandler.indexOf('reply_sub') >= 0) {
            $this=$(this);
            var msg=$this.prev().val();
            var news_id=$('#news_id').val();
            var csrf_token=$('#csrf_token').val();
            var comment_id=$this.attr('commentid');
            $.post('/commentback/'+comment_id,{
                'msg':msg,
                'news_id':news_id,
                'csrf_token':csrf_token
            },function (data) {
                if(data.result==1){
                    alert('评论不能为空');
                }else if(data.result==2){
                    $('.login_btn').click();
                }else if(data.result==3){
                    get_comment_list();
                    $this.prev().val('');
                    $this.parent().hide();
                }
            });
        }
    })

    // 关注当前新闻作者
    $(".focus").click(function () {
        $.post('/userfollow',{
            'csrf_token':$('#csrf_token').val(),
            'action':1,
            'follow_user_id':$('#user_id').val()
        },function (data) {
            if(data.result==1){
                    $('.login_btn').click();
            }else if(data.result==2){
                $('.focus').hide();
                $('.focused').show();
                $('.follows>b').text(data.follow_count);
            }
        })
    })

    // 取消关注当前新闻作者
    $(".focused").click(function () {
        $.post('/userfollow',{
            'csrf_token':$('#csrf_token').val(),
            'action':2,
            'follow_user_id':$('#user_id').val()
        },function (data) {
            if(data.result==1){
                    $('.login_btn').click();
            }else if(data.result==2){
                $('.focus').show();
                $('.focused').hide();
                $('.follows>b').text(data.follow_count);
            }
        })
    })


})

function get_comment_list() {
    $.get('/comment/list/' + $('#news_id').val(), function (data) {
        vue_comment_list.comment_list = data.comment_list
    })
}