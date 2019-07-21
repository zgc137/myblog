import json

from django.contrib.auth import login, logout

from users.forms import RegisterForm, LoginForm
from django.shortcuts import render, redirect,reverse
from django.views import View
from  django.views.decorators.csrf import ensure_csrf_cookie
from utils.json_fun import to_json_data
from utils.res_code import Code, error_map
from users.models import User
from django.utils.decorators import method_decorator

class RegisterView(View):
    '''
    /users/register/
    '''
    def get(self,request):

        return render(request, 'users/register.html')

    def post(self,request):
        '''
        1 get value
        2 check value
        3  sava value to mysql/redis
        4 give info custom
        :param request:
        :return:
        '''
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data)#.decode('utf8') 清除解码
        form = RegisterForm(data=dict_data)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            mobile = form.cleaned_data.get('mobile')

            user = User.objects.create_user(username=username, password=password, mobile=mobile)
            login(request, user)
            return to_json_data(errmsg="恭喜您，注册成功！")

        else:
            # 定义一个错误信息列表
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)

            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)

class LoginView(View):
    '''
    /users/login/
    '''
    #方法一是在每个需要的html页面嵌入{% csrf_token %}
    # @method_decorator(ensure_csrf_cookie)# csrf方法二
    def get(self,request):

        return render(request, 'users/login.html')

    def post(self, request):
        json_data = request.body
        if not json_data:
            return to_json_data(errno=Code.PARAMERR, errmsg=error_map[Code.PARAMERR])
        # 将json转化为dict
        dict_data = json.loads(json_data.decode('utf8'))  # 没有解码，会产生bug
        form = LoginForm(data=dict_data, request=request)
        if form.is_valid():
            return to_json_data(errmsg="恭喜您，登录成功！")
        else:
            # 定义一个错误信息列表
            err_msg_list = []
            for item in form.errors.get_json_data().values():
                err_msg_list.append(item[0].get('message'))
            err_msg_str = '/'.join(err_msg_list)  # 拼接错误信息为一个字符串

            return to_json_data(errno=Code.PARAMERR, errmsg=err_msg_str)

class LogoutView(View):
    """
    """
    def get(self, request):
        logout(request)

        return redirect(reverse("users:login"))