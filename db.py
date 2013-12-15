#!/usr/bin/env python
# coding=utf-8
import torndb
import logging
import config 

log_name = "db.log"
logging.basicConfig(filename=log_name, filemode='a', leval=logging.INFO)

class MysqlHandler():
    def __init__(self):
        try:
            self.db = torndb.Connection(config.sql_ip, config.sql_database, config.sql_user, config.sql_pwd)
        except Exception as e:
            logging.ERROR(e)

    def add_user(self, email, pwd, avatar, valid):
        ''' args :  email : char
                    pwd : char md5()
            todo : storage the info of new user 
            return : void
        '''
        exe = 'insert into user(email, pwd, avatar, valid) values(%s, %s, %s, %s)'
        self.db.execute_lastrowid(exe, email, pwd, avatar, valid)

    def get_info_by_email(self, email):
        ''' args : email :char 
            get all the information of the user 
            return : a list about the user
        '''
        exe = 'select * from user where email=(%s)'
        return self.db.get(exe, email)
    
    def get_all_user_info(self):
        '''
        return : a list of all user information
        '''
        exe = 'select * from user'
        return self.db.query(exe)
    def get_all_unregister_user(self):
        '''
        retturn : a list 
        '''
        exe = 'select * from user where status=0'
        return self.db.query(exe)

    def change_status_by_email(self, email):
        ''' args :  email char 
            todo :  change the user's status to 1 to indicate that the user already confirm the mailbox , and clear the valid in the user table of  the user 
            return : void
        '''
        exe = "update user set status=1 ,valid='' where email=(%s)"
        self.db.execute_lastrowid(exe, email)
    
    def add_pict(self, title, des, email):
        '''
        '''
        exe = "select * from user where email=(%s)"
        user_id = self.db.get(exe, email)['id']
	url = "picture/no.jpg"
        exe = "insert into pict(title, des, user_id, url) values(%s, %s, %s, %s)"
        return self.db.execute_lastrowid(exe, title, des, user_id, url)

    def add_imgurl(self, pict_id, url):
        exe = "update pict set url=(%s) where id=(%s)"
        self.db.execute_lastrowid(exe, url, pict_id)
    
    def get_all_pict(self):
        '''
        return : all the pictures in the db as a list 
        '''
        exe = 'select * from pict'
        return self.db.query(exe)

    def get_pict_by_email(self, email):
        user_id = self.get_info_by_email(email)['id']
        exe = "select * from pict where user_id = (%s)"
        return self.db.query(exe, user_id)
    def get_all_comment(self):
        exe = 'select * from comment'
        return self.db.query(exe)

