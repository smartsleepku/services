#from django.db import models
from djongo import models
from django.utils.translation import ugettext_lazy as _
import numpy as np
from numpy.random import randint as ri
import datetime
import requests
import os
import json
import sys, traceback
import mysql.connector

class Activity(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    userId = models.CharField(_("userId"), max_length=255, blank=False,default="")
    type = models.CharField(_("userId"), max_length=255, blank=False,default="")
    confidence = models.IntegerField()
    time = models.DateTimeField(auto_now_add=True, blank=True)
    resting = models.BooleanField(default=True)
    
    class Meta:
        db_table = "activities"
        managed=False
    
    def __str__(self):
        return f'{self.userId},{self.time}'

class Attendeelog(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    userId = models.CharField(_("userId"), max_length=255, blank=False,default="")
    gmtOffset = models.IntegerField()
    weekdayMorning = models.DateTimeField(auto_now_add=True, blank=True)
    weekdayEvening = models.DateTimeField(auto_now_add=True, blank=True)
    weekendMorning = models.DateTimeField(auto_now_add=True, blank=True)
    weekendEvening = models.DateTimeField(auto_now_add=True, blank=True)
    class Meta:
        db_table = "attendeelogs"
        managed=False
    
    def __str__(self):
        return f'{self.userId},{self.weekdayMorning}'

class Attendee(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    userId = models.CharField(_("userId"), max_length=255, blank=False,default="")
    gmtOffset = models.IntegerField()
    weekdayMorning = models.DateTimeField(auto_now_add=True, blank=True)
    weekdayEvening = models.DateTimeField(auto_now_add=True, blank=True)
    weekendMorning = models.DateTimeField(auto_now_add=True, blank=True)
    weekendEvening = models.DateTimeField(auto_now_add=True, blank=True)
    #devices = models.ArrayField(
    nextPush = models.DateTimeField(auto_now_add=True, blank=True)
    class Meta:
        db_table = "attendees"
        managed=False
    
    def __str__(self):
        return f'{self.userId},{self.weekdayMorning}'


class Debug(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    userId = models.CharField(_("userId"), max_length=255, blank=False,default="")    
    time = models.DateTimeField(auto_now_add=True, blank=True)
    model = models.CharField(_("model"), max_length=255, blank=False,default="")
    manufacturer = models.CharField(_("manufacturer"), max_length=255, blank=False,default="")
    systemVersion = models.CharField(_("systemVersion"), max_length=255, blank=False,default="")
    systemName = models.CharField(_("systemName"), max_length=255, blank=False,default="")

    class Meta:
        db_table = "debugs"
        managed=False
    
    def __str__(self):
        return f'{self.userId}:{self.model},{self.manufacturer},{self.systemName} {self.systemVersion}'

class HeartBeat(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    userId = models.CharField(_("userId"), max_length=255, blank=False,default="")
    time = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        db_table = "heartbeats"
        managed=False
    
    def __str__(self):
        return f'{self.userId}:{self.time}'

class Rest(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    userId = models.CharField(_("userId"), max_length=255, blank=False,default="")
    resting = models.BooleanField(default=True)
    startTime = models.DateTimeField(auto_now_add=True, blank=True)
    endTime = models.DateTimeField(auto_now_add=True, blank=True)
    
    class Meta:
        db_table = "rests"
        managed=False
    
    def __str__(self):
        return f'{self.userId}:{self.startTime} - {self.resting}'

class Session(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    userId = models.CharField(_("userId"), max_length=255, blank=False,default="")    
    #__v = models.IntegerField()

    class Meta:
        db_table = "sessions"
        managed=False
    
    def __str__(self):
        return f'{self.userId}'

class Sleep(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    userId = models.CharField(_("userId"), max_length=255, blank=False,default="")    
    time = models.DateTimeField(auto_now_add=True, blank=True)
    sleeping = models.BooleanField(default=False)

    class Meta:
        db_table = "sleeps"
        managed=False
    
    def __str__(self):
        return f'{self.userId}:{self.time} - {self.sleeping}'

class User(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    emailAddress = models.CharField(_("emailAddress"), max_length=255, blank=False,default="")
    password = models.CharField(_("password"), max_length=255, blank=False,default="")
    attendeeCode = models.CharField(_("attendeeCode"), max_length=255, blank=False,default="")

    class Meta:
        db_table = "users"
        managed=False
    
    def __str__(self):
        return f'{self.pk}:{self.attendeeCode}'

    def to_csv(self, fields=["_id","attendeeCode"]):
        v = [str(getattr(self,f)) for f in fields]
        return ",".join(v)

    @classmethod
    def _query_lime_survey(cls, survey_base, method, params):
        return requests.post(
                f'{survey_base}/index.php/admin/remotecontrol',
                json = {"method":method,"params":params,"id":1}
            )
    @classmethod
    def retrieve_token_id(cls, _id ,session_key, survey_id, survey_base):
        r = cls._query_lime_survey(survey_base, "list_participants",
            [session_key,survey_id,0,100000000,False,False,
            {'token':_id}])
        r = json.loads(r.content)['result']
        if type(r)==dict and 'status' in r and r['status'] == 'No survey participants found.':
            return None
        else:
            token,= json.loads(r.content)['result']
            return token['tid']

    @classmethod
    def delete_user(cls, attendeecode, survey_opts, mysql_opts):
        '''
        Delete a user from surveydb and mongodb
        '''
        try:
            user = cls.objects.get(attendeeCode=attendeecode)

            cnx = mysql.connector.connect(
                host=mysql_opts['host'],
                port=mysql_opts['port'],
                user=mysql_opts['user'],
                password=mysql_opts['pwd']
            )
            cur = cnx.cursor()
            survey_base,survey_uname,survey_pwd,survey_id = survey_opts['base'],\
                survey_opts['user'],\
                survey_opts['pwd'],\
                survey_opts['survey_id']
            
            session_key = cls._get_limesurvey_sessionkey(survey_uname,survey_pwd,survey_base)
            cur.execute('use smartsleep')
            
            cur.execute(f'SELECT id FROM lime_survey_{survey_id} where token="{str(user.pk)}"')
            response_id = cur.fetchone()
            if response_id != None:
                response_id, = response_id
                cur.execute(f'DELETE FROM lime_survey_{survey_id}_timings where id={response_id}')
                cur.execute(f'DELETE FROM lime_survey_{survey_id} where id={response_id}')

            tkn_id = cls.retrieve_token_id(str(user.pk) ,session_key, survey_id, survey_base)
            if tkn_id != None:
                r = cls._query_lime_survey(survey_base, "delete_participants", 
                    {'sSessionKey':session_key, 'iSurveyID':survey_id, 'aTokenIDs':[tkn_id]})
            cls._release_limesurvey_sessionkey(session_key,survey_base)
            cur.close()
            cnx.close()

            Activity.objects.filter(userId=str(user.pk)).delete()
            Attendeelog.objects.filter(userId=str(user.pk)).delete()
            Attendee.objects.filter(userId=str(user.pk)).delete()
            Debug.objects.filter(userId=str(user.pk)).delete()
            HeartBeat.objects.filter(userId=str(user.pk)).delete()
            Rest.objects.filter(userId=str(user.pk)).delete()
            Session.objects.filter(userId=str(user.pk)).delete()
            Sleep.objects.filter(userId=str(user.pk)).delete()
            user.delete()

        except:
            e = sys.exc_info()[0]
            print(e)
            traceback.print_exc()
        return True
            
    @classmethod
    def _get_limesurvey_sessionkey(cls,survey_uname,survey_pwd,survey_base):
        '''
        Obtain session key to work with limesurvey
        '''
        r =cls._query_lime_survey(survey_base, "get_session_key", 
        {'username':survey_uname,'password':survey_pwd})
        session_key = json.loads(r.content)['result']
        return session_key

    @classmethod
    def _release_limesurvey_sessionkey(cls,session_key,survey_base):
        '''
        Release limesurvey session key
        '''
        r =cls._query_lime_survey(survey_base, "release_session_key", {'sSessionKey':session_key})

    @classmethod
    def generate_available_users_csv(cls):
        avial = cls.objects.filter(emailAddress="")
        #dump avial to csv here

    @classmethod
    def generate_usernames(cls, count = 1000):
        '''
        Generates a list of unique usernames.
        Each username is made up from the formula
        `adjective-number-animal`
        Even though a number of usernames is specified, it is not guaranteed
        that this amount will be created due to uniqueness constraint
        Returns a list of usernames
        '''

        with open('apps/users/fixtures/adjectives.txt') as fadj,\
             open('apps/users/fixtures/animals.txt') as fani:
            adj = np.array(fadj.read().replace(' ','').replace(',','').lower().split('\n'))
            ani = np.array(fani.read().replace(' ','').replace(',','').lower().split('\n'))
            ulst = (np.char.array(adj[ri(0,len(adj),count)]) + '-' +
                    np.char.zfill(ri(0,99,count).astype(str),2) + '-' +
                    np.char.array(ani[ri(0,len(ani),count)])).tolist()
        return list(set(ulst))

    @classmethod
    def bulk_create_users(cls, amount, csv_out_dir,
            survey_base, survey_uname, survey_pwd, survey_id, po = None):
        '''
        Creates a collection of usernames and makes sure
        they are unique and does not exist in database already.
        Saves usernames to mongo storage and then stores them
        in limesurvey db also.
        Finally a csv file is created and saved to disk
        Input parameters:
        amount       <int> : e.g. 1000
        csv_out_dir  <str> : e.g. /var/www/mysite
        survey_base  <str> : e.g. http://localhost:8081
        survey_uname <str> : e.g. admin
        survey_pwd   <str> : e.g. admin
        survey_id    <int> : e.g. 765693
        po           <obj> : celery progress_observer (optional). 
                             If omitted, info is printed to std. out
        Output parameters:
        amount_created     <int>
        generated_filename <str>
        '''
        class dummy_po(object):
            def update_state(self, state, meta):
                print(state,meta)
        po = dummy_po() if po == None else po

        chunksize = 5000
        if amount<=chunksize:
            runs = [amount]
        else:
            runs = [chunksize]*int(np.floor(amount/chunksize)) + \
            ([amount%chunksize] if amount%chunksize!=0 else [])
        
        total_tasks = 9*len(runs)
        progress = lambda c,m:{"state":'PROGRESS', "meta":{'current': c, 'total': total_tasks,'msg':m}}
        task_cnt = 0
        batches = []
        for i,run in enumerate(runs):
            info = f'Chunk {i+1}/{len(runs)}'
            po.update_state(**progress(task_cnt,f'{info}: Generating usernames'))
            task_cnt += 1
            ulst = cls.generate_usernames(run)
            po.update_state(**progress(task_cnt,f'{info}: Checking uniqueness'))
            task_cnt += 1
            bad_names = [e.attendeeCode for e in cls.objects.filter(attendeeCode__in=ulst)]
            new_users = [cls(attendeeCode=u) for u in ulst if u not in bad_names]
            po.update_state(**progress(task_cnt,f'{info}: Updating mongodb with validated users'))
            task_cnt += 1
            cls.objects.bulk_create(new_users)
            po.update_state(**progress(task_cnt,f"{info}: Retrieving generated id's from mongodb"))
            task_cnt += 1
            us = cls.objects.filter(attendeeCode__in=[u.attendeeCode for u in new_users])
            po.update_state(**progress(task_cnt,f"{info}: Generating csv file"))
            task_cnt += 1
            fields = ["_id","attendeeCode"]
            csv = "\r\n".join([",".join(fields)] + [u.to_csv(fields) for u in us])
            fname = '{0:%d-%m-%Y-%H-%M_%S}'.format(datetime.datetime.now())
            fname = f'{fname}_{len(us)}.csv'
            survey_data = [{'token':str(u.pk)} for u in us]
            po.update_state(**progress(task_cnt,f"{info}: Obtaining survey session key"))
            task_cnt += 1
            session_key = cls._get_limesurvey_sessionkey(survey_uname,survey_pwd,survey_base)
            po.update_state(**progress(task_cnt,f"{info}: Updating survey database with new users"))
            task_cnt += 1
            generate_id = False
            cls._query_lime_survey(survey_base, "add_participants", [session_key,survey_id,survey_data,generate_id])
            po.update_state(**progress(task_cnt,f"{info}: Releasing survey session key"))
            task_cnt += 1
            cls._release_limesurvey_sessionkey(session_key,survey_base)
            po.update_state(**progress(task_cnt,f"{info}: Writing csv to disk"))
            task_cnt += 1
            with open(os.path.join(csv_out_dir,fname), 'w') as f:
                f.write(csv)
            batches.append({
                'amountcreated' : len(us),
                'filename': fname
            })

        return {
                'totalamountcreated':sum(map(lambda x:x['amountcreated'],batches)),
                "batches":batches
        }


    