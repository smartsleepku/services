from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import JsonResponse
from apps.users.models import User
from django.conf import settings
from celery.decorators import task
import sys, traceback

@task(bind=True, name="usertask")
def usertask(self, amount, csv_out_dir,survey_base, survey_uname, survey_pwd, survey_id):
    return User.bulk_create_users(amount, csv_out_dir,survey_base, survey_uname, survey_pwd, survey_id, po = self)

def create_users(request, amount):
    try:
        task = usertask.apply_async(
            args=[
                amount,
                settings.CSV_OUT_DIR,
                settings.LIMESURVEY_BASE,
                settings.LIMESURVEY_USR,
                settings.LIMESURVEY_PWD, 
                settings.LIMESURVEY_SURVEY_ID
                ]
            )
    except:
        e = sys.exc_info()[0]
        print(e)
        traceback.print_exc()
    return JsonResponse({'task_id':task.id}, safe=False)

def query_process_update(request, task_id):
    task = usertask.AsyncResult(task_id)
    return JsonResponse({'status':task.state,'info':task.info})

def delete_user(request, attendeecode):
    try:
        lime_opts = {
            'base':settings.LIMESURVEY_BASE,
            'user':settings.LIMESURVEY_USR,
            'pwd':settings.LIMESURVEY_PWD, 
            'survey_id':settings.LIMESURVEY_SURVEY_ID
        }
        mysql_opts = {
            'host':settings.MYSQL_HOST,
            'port':settings.MYSQL_PORT,
            'user':settings.MYSQL_USER,
            'pwd' :settings.MYSQL_PWD
        }
        #User.testit(attendeecode)
        User.delete_user(attendeecode, lime_opts, mysql_opts)
    except:
        e = sys.exc_info()[0]
        print(e)
        traceback.print_exc()
    return JsonResponse({})
                
                
                
    

