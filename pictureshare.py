#!/usr/bin/env python
# coding=utf-8
import tornado.ioloop
import tornado.web
import os 
import tornado.httpserver
import logging
import random
import smtplib
import Image
import string 
import hashlib
import db
import config
from email.mime.text import MIMEText 

log_filename = "error.log"
logging.basicConfig(filename=log_filename, filemode='a', leval=logging.INFO)

def login_check(func):
    def wrapper(*args):
        ins = args[0]
        user = ins.get_secure_cookie("useremail")
        if user:
            return func(*args)
        else:
            raise Exception
    return wrapper

def random_str(length):
    a = list(string.ascii_letters)
    random.shuffle(a)
    return ''.join(a[:length])

def send_mail( dis_mail, sub, content ):
    mail_host = config.mail_host
    mail_user = config.mail_user
    mail_pwd = config.mail_pwd
    mail_postfix = config.mail_postfix
    me = "Picture Share register center<%s@%s>" % (mail_user, mail_postfix)
    msg = MIMEText(content, _charset='gb2312')
    msg['Subject'] = sub
    msg['From'] = me
    msg['To'] = dis_mail
    try:
        mail = smtplib.SMTP()
        mail.connect(mail_host)
        mail.login(mail_user, mail_pwd)
        mail.sendmail(me, dis_mail, msg.as_string())
        mail.close()
        return True
    except Exception as e :
        logging.ERROR(e)
        return False
class Login(tornado.web.RequestHandler):
    def get(self):
        if self.get_secure_cookie("useremail") != '':
            self.render("login.html")
        else:
            self.redirect("/")
    
    def post(self):
        login_email = "".join(self.get_argument("useremail").split())
        login_passwd = "".join(self.get_argument("userpasswd").split())
        user_info = []
        try:
            user_info = self.application.db.get_info_by_email(login_email)
        except Exception as e:
            logging.ERROR(e)
        key = hashlib.md5()
        key.update(login_passwd)
        login_md5_passwd = key.hexdigest()
        if user_info :
            if user_info['status'] == 1:
                if login_md5_passwd == user_info['pwd']:
                    self.set_secure_cookie("useremail", login_email)
                    self.redirect("/")
                else:
                    self.render("login.html")
            else:
                self.render("login.html")
        else:
            self.render("login.html")


class Logout(tornado.web.RequestHandler):
    @login_check
    def get(self):
	self.clear_cookie("useremail")
	self.redirect("/")

class Register(tornado.web.RequestHandler):
    def get(self):
        if not self.get_secure_cookie("useremail"):
            self.render("register.html")
        else:
            self.redirect("/")

    def post(self):
        re_email = ''.join(self.get_argument('email').split())
        re_pwd = ''.join(self.get_argument('pwd').split())
        re_pwd_confirm = ''.join(self.get_argument('pwd_confirm').split())
        email_list = self.application.db.get_all_user_info()
        
        for email in email_list:
            if re_email == email:
                self.render("register.html")
        if re_pwd != re_pwd_confirm:
            self.render("register.html")

        try:
            avatar = "avatar/no.jpg"
            valid = random_str(6)
            mail_content = "please remember the code: %s" % (valid)
            mail_sub = "mailbox confirm"
            i = 0 
            while not send_mail(re_email, mail_sub , mail_content ) :
                if i < 5:
                    i += 1
                else:
                    self.render("register.html")
            key = hashlib.md5()
            key.update(re_pwd)
            re_md5_pwd = key.hexdigest()
            self.application.db.add_user(re_email, re_md5_pwd, avatar, valid)
        except Exception as e:
            print "register4:  " + str(e)
        self.render("getvalid.html")


class GetValid(tornado.web.RequestHandler):
    def get(self):
        self.render("getvalid.html")

    def post(self):
        re_valid = ''.join(self.get_argument("valid").split())
        unregister_user = []
        try:
            unregister_user = self.application.db.get_all_unregister_user()
        except Exception as e:
            logging.INFO(str(e))
        for user in unregister_user:
            if re_valid == user['valid']:
                self.set_secure_cookie("useremail", user['email'])
                self.application.db.change_status_by_email(user['email'])
                self.redirect('/')
        self.render("getvalid.html")

class UploadPicture(tornado.web.RequestHandler):
    def post(self):
        email = self.get_secure_cookie("useremail")
        title = self.get_argument("title")
        des = self.get_argument("des")
        pict_list = self.request.files['myfile']
        for pict in pict_list:
            if not self.judge_picture(pict) :
                self.redirect("/person")
            pict_id = self.application.db.add_pict(title, des, email)
            self.handle_picture(pict, pict_id) 
    def judge_picture(self, pict):
        img_type_list = ['image/gif', 'image/jpeg', 'image/pjpeg', 'image/bmp', 'image/png', 'image/x-png']
        if pict['content_type'] not in img_type_list:
            return False
        return True
    def handle_picture(self, pict, pict_id):
        img_url = "picture/"
        image_format = pict['filename'].split('.').pop().lower()
        img_name = str(pict_id)
        tmp_name = img_url+img_name+'.'+image_format
        #this is a absolute path!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!11
        file = open("/home/xuxiaolong/server/pictureshare/static/picture/%s" % img_name + '.'+ image_format, 'web')
        file.write(pict['body'])
        self.application.db.add_imgurl(pict_id, tmp_name)
        file.close()
        self.redirect("/person")


class MainHandler ( tornado.web.RequestHandler) :
    def get( self ) :
        all_photo = self.application.db.get_all_pict()
        useremail = self.get_secure_cookie("useremail")
        if useremail:
            try:
                self.render( "index.html", all_photo=all_photo, email=useremail)
            except Exception as e :
                print "except:" + str(e)
        else:
            try:
                self.render("index.html", all_photo=all_photo, email="visitor")
            except Exception as e:
                print str(e)

class Person(tornado.web.RequestHandler):
    @login_check
    def get(self):
        email = self.get_secure_cookie("useremail")
        user_photo = self.application.db.get_pict_by_email(email)
        all_comment = self.application.db.get_all_comment()
        self.render("person.html" , email=email, user_photo=user_photo, comment = all_comment)


class Application (tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', MainHandler),
            (r'/login', Login),
	    (r'/logout', Logout),
            (r'/register', Register),
            (r'/getvalid', GetValid),
            (r'/person', Person),
            (r'/upload', UploadPicture),
        ]
        settings = dict(
            static_path = os.path.join(os.path.dirname(__file__), "static"),
            template_path = os.path.join(os.path.dirname(__file__), "templates"),
            cookie_secret = 'uBaJgTxCTIKRjuE/2sMBoqfKwwHmwUdGm8A1wMpp4AM=',
            login_url = "/login" ,
            debug = True ,
            )
        tornado.web.Application.__init__(self, handlers, **settings)
        self.db = db.MysqlHandler()

if __name__ == "__main__" :
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(12123)
    tornado.ioloop.IOLoop.instance().start()
