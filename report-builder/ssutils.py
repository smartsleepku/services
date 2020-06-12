import bisect

from pymongo import MongoClient
import pandas as pd
from bokeh.plotting import show
from bokeh.plotting import figure, show, gridplot, curdoc
from bokeh.io import output_notebook, reset_output
from bokeh.models import Spacer, DatetimeTickFormatter, Legend
from bokeh.resources import INLINE
import numpy as np
import holoviews as hv
from datetime import datetime, timedelta
reset_output()
output_notebook(resources = INLINE, verbose=False, hide_banner=True)
#hv.extension('bokeh')

def print_dict(data):
    for key in data:
        print(f'{key:<14}: {data[key]:>4}')

def make_histogram_plot(name, hist, edges, x_label=None):
    p = figure(title=name + ' distribution', tools='', background_fill_color="#fafafa")
    p.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:],
           fill_color="navy", line_color="white", alpha=0.5)
    p.y_range.start = 0
    p.yaxis.formatter.use_scientific = False
    if x_label is None:
        x_label = name + ' count'
    p.xaxis.axis_label = x_label
    p.yaxis.axis_label = 'user count'
    p.grid.grid_line_color="white"
    p.toolbar.logo = None
    return p

def count_lonely_sleeps(heartbeats, sleeps, delta=timedelta(minutes=30)):
    """Return number of sleep events without close enough heartbeat event.
    
    ``heartbeats`` and ``sleeps`` should be sorted lists of datetime
    """
    counter = 0
    lo = 0
    for sleep in sleeps:
        pos = bisect.bisect(heartbeats, sleep, lo=lo)
        lo = pos
        if not ((pos-1 >= 0 and (sleep-heartbeats[pos-1]) < delta)
                or 
                (pos < len(heartbeats) and (heartbeats[pos]-sleep) < delta)):
            counter += 1
    return counter

class SsMongo(object):

    def __init__(self, hostname, username, password, port):
        self.client = MongoClient(hostname, port)
        #self.db = self.client["admin"]
        self.client["admin"].authenticate(username, password)
        self._now = None
    
    @property
    def now(self):
        """now value — if None, use current datetime during each call"""
        if self._now is None:
            return datetime.now()
        return self._now

    @now.setter
    def now(self, value):
        self._now = value

    def debug_stats(self):
        # Why are more rows returned than what is contained in heartbeat collection?
        cur = self.client.smartsleep.heartbeats.aggregate(
            [
                {
                    "$lookup" : {
                        "from" : "smartsleep.debugs",
                         "localField": "userId",
                         "foreignField": "userId",
                         "as": "debug_docs"
                    }
                },
                {
                    "$replaceRoot" : { 
                        "newRoot" : { 
                            "$mergeObjects" : [ 
                                { 
                                    "$arrayElemAt": [ 
                                        "$debug_docs", 0 
                                    ] 
                                }, 
                                "$$ROOT" 
                            ]
                        } 
                    }
               },
               { 
                   "$project" : { 
                       "debug_docs": 0
                   } 
               }
            ],
            allowDiskUse=True
        )
        return pd.DataFrame.from_records(cur)
        
    def phone_type_overview(self):
        distinct_ios = self.client.smartsleep.debugs.distinct(
            'userId',
            {'manufacturer': 'Apple'}
        )
        distinct_android = self.client.smartsleep.debugs.distinct(
            'userId',
            {'manufacturer': {'$ne': 'Apple'}}
        )
        return {'ios_count': len(distinct_ios),
                'android_count': len(distinct_android)}
    
    def get_phone_details(self, user_ids):
        """Return phone type and os version for each user in list ``user_ids``.
        """
        pipeline = [
            {'$match': # Get all records from last days
                {'userId' :
                    {"$in": user_ids
                    }
                }
            },
            {'$sort' : { 'time': -1 } # sort
            },
            {"$group": # group by user and only get latest record
                {"_id": "$userId",
                 'data': {'$first': {'time': '$time',
                                     'model': '$model',
                                     'manufacturer': '$manufacturer',
                                     'systemName': '$systemName',
                                     'systemVersion': '$systemVersion'}}
                }
            }
        ]
        phone_details = list(self.client.smartsleep.debugs.aggregate(pipeline, allowDiskUse=True))
        found_ids = [item['_id'] for item in phone_details]
        for user_id in user_ids:
            if user_id not in found_ids:
                phone_details.append({
                    '_id': user_id,
                    'data': {'time': None,
                             'model': 'N/A',
                             'manufacturer': 'N/A',
                             'systemName': 'N/A',
                             'systemVersion': 'N/A'}
                })
        return phone_details
    
    def expand_phone_details(self, phone_details):
        """Make dict from phone_details list.
        """
        summary = {}
        result = {}
        for item in phone_details:
            key = item['data']['systemName'] + ': ' + item['data']['systemVersion']
            summary[key] = summary.get(key, 0) + 1
            result[item['_id']] = key
        return summary, result
    
    def find_active_users(self, activeperiod_days = None):
        '''
        activeperiod_days should be a positive integer
        '''
        time_filt = {}
        if activeperiod_days != None:
            now = self.now
            time_filt = {
                "time" : { 
                    "$lt": now,
                    "$gte": now - timedelta(days=activeperiod_days)
                  }
            }
        distinct_hb = self.client.smartsleep.heartbeats.find(time_filt).distinct("userId")
        distinct_sl = self.client.smartsleep.sleeps.find(time_filt).distinct("userId")
        distinct_ac = self.client.smartsleep.activities.find(time_filt).distinct("userId")
        return set(distinct_hb+distinct_sl+distinct_ac)
    
    def find_inactive_event_users(self, collection='activity', activeperiod_days=7):
        """From active users in the system,
        return list of users with no changes in specific collection
        in the last ``activeperiod_days`` days.
        """
        now = self.now
        time_filt = {}
        if collection == 'attendeelogs':
            time_key = 'changedDatetime'
        else:
            time_key = 'time'
        if activeperiod_days != None:
            now = self.now
            time_filt = {
                "time" : { 
                    "$lt": now,
                    "$gte": now - timedelta(days=activeperiod_days)
                  }
            }
        active_users = self.client.smartsleep[collection].distinct("userId", time_filt)
        inactive_users = set(self.find_active_users(activeperiod_days)) - set(active_users)
        return list(inactive_users)
    
    def find_user_count(self, activeperiod_days = None):
        '''
        activeperiod_days should be a positive integer
        '''
        return len(self.find_active_users(activeperiod_days))
    
    def all_users(self):
        """Return list of all users."""
        distinct_users = list(self.client.smartsleep.attendees.distinct("userId"))
        return distinct_users
    
    def find_event_count(self, collection='activity', activeperiod_days=1):
        '''
        collection is one of 'heartbeats', 'activities', 'sleeps', 'attendeelogs'
        activeperiod_days should be a positive integer
        '''
        now = self.now
        if collection == 'attendeelogs':
            time_key = 'changedDatetime'
        else:
            time_key = 'time'
        pipeline = [
            {'$match': # Get all records from last days
                {time_key :
                    {"$lt": now,
                     "$gte": now - timedelta(days=activeperiod_days)
                    }
                }
            },
            {"$group": # group by user and count number of records for each user
                {"_id": "$userId",
                 'total': {'$sum': 1}
                }
            },
            {'$sort' : { 'total': 1 } # sort
            }
        ]
        recent_events = list(self.client.smartsleep[collection].aggregate(pipeline, allowDiskUse=True))
        recent_event_counts = [item['total'] for item in recent_events]
        return recent_event_counts
    
    def find_rest_null_count(self, activeperiod_days=1, threshold=-1):
        '''Return number of rest periods ending with null per user.
        
        activeperiod_days should be a positive integer
        '''
        now = self.now
        pipeline = [
            {'$match': # Get all records from last days with endTime=null
                {'startTime':
                    {"$lt": now,
                     "$gte": now - timedelta(days=activeperiod_days)
                    },
                 'endTime':
                    {'$eq': None
                    }
                }
            },
            {"$group": # group by user and count number of records for each user
                {"_id": "$userId",
                 'total': {'$sum': 1}
                }
            },
            {'$match': # Get all records with total > threshold
                {'total':
                    {"$gt": threshold
                    },
                }
            },
            {'$sort' : { 'total': 1 } # sort
            }
        ]
        recent_rests = list(self.client.smartsleep.rests.aggregate(pipeline, allowDiskUse=True))
        recent_rests_counts = [item['total'] for item in recent_rests]
        recent_rests_users = [item['_id'] for item in recent_rests]
        return recent_rests_counts, recent_rests_users
        
    def find_inactive_attendeelog_user_count(self, activeperiod_weeks=5):
        """From all users in the system,
        return number of users with no changes
        in the last ``activeperiod_weeks`` in per-week list.
        """
        now = self.now
        total_user_count = len(list(self.client.smartsleep.attendeelogs.find({}).distinct("userId")))
        result = []
        for i in range(activeperiod_weeks):
            pipeline = [
                {'$match': # Get all records from that week
                    {'changedDatetime' :
                        {"$lt": now - timedelta(days=i*7),
                         "$gte": now - timedelta(days=(i+1)*7)
                        }
                    }
                },
                {"$group": # group by user
                    {"_id": "$userId"
                    }
                },
                {'$count': "total" # count total number of active users
                }
            ]
            
            active_user_count = list(self.client.smartsleep.attendeelogs.aggregate(pipeline, allowDiskUse=True))
            if len(active_user_count) > 0:
                active_user_count = active_user_count[0]['total']
            else:
                active_user_count = 0
            #print('active', i, active_user_count)
            result.append(total_user_count - active_user_count)
        return result
        
    def find_isolated_sleeps(self, activeperiod_days=1):
        '''
        activeperiod_days should be a positive integer
        '''
        now = self.now
        time_key = 'time'
        pipeline = [
            {'$match': # Get all records from last days
                {time_key :
                    {"$lt": now,
                     "$gte": now - timedelta(days=activeperiod_days)
                    }
                }
            },
            {"$group": # group by user
                {"_id": "$userId",
                 'times': {'$push': '$time'}
                }
            }
        ]
        users_heartbeats = self.client.smartsleep.heartbeats.aggregate(pipeline, allowDiskUse=True)
        users_screens = self.client.smartsleep.sleeps.aggregate(pipeline, allowDiskUse=True)
        # Group sleeps and heartbeats data per-user
        combined_data = {}
        for item in users_heartbeats:
            if item['_id'] not in combined_data:
                combined_data[item['_id']] = {'heartbeats': [], 'sleeps': []}
            combined_data[item['_id']]['heartbeats'] = sorted(item['times'])
        for item in users_screens:
            if item['_id'] not in combined_data:
                combined_data[item['_id']] = {'heartbeats': [], 'sleeps': []}
            combined_data[item['_id']]['sleeps'] = sorted(item['times'])
        # Calculate number of isolated sleep events per user
        lonely_sleeps_per_user = []
        lonely_sleeps_users = []
        lonely_sleeps_user_count = 0
        for user_id in combined_data:
            lonely_sleeps = count_lonely_sleeps(combined_data[user_id]['heartbeats'], combined_data[user_id]['sleeps'])
            lonely_sleeps_per_user.append(lonely_sleeps)
            if lonely_sleeps > 0:
                lonely_sleeps_user_count += 1
                lonely_sleeps_users.append(user_id)
        return lonely_sleeps_per_user, lonely_sleeps_user_count, lonely_sleeps_users
    
    def find_sleep_imbalance(self, activeperiod_days=1, threshold_proportion=0.5, threshold_ratio=0.5):
        '''
        activeperiod_days should be a positive integer
        '''
        now = self.now
        time_key = 'time'
        pipeline = [
            {'$sort' : { 'time': 1 } # sort
            },
            {'$match': # Get all records from last 24 hours
                {time_key :
                    {"$lt": now,
                     "$gte": now - timedelta(days=activeperiod_days)
                    }
                }
            },
            {"$group": # group by user and push on/off value
                {"_id": "$userId",
                 'data': {'$push': {'onoff': '$sleeping','time': '$time'}},
                }
            },
        ]
        users_screens = list(self.client.smartsleep.sleeps.aggregate(pipeline, allowDiskUse=True))
        proportions = []
        ratios = []
        proportion_users = []
        ratio_users = []
        for user_record in users_screens:
            #print(user_record['_id'])
            same_count = 0
            on_count = 0
            prev = None
            for item in user_record['data']:
                if item['onoff']:
                    on_count += 1
                if prev != None:
                    if prev == item['onoff']:
                        same_count += 1
                prev = item['onoff']
                #print(item['time'], item['onoff'])
            off_count = len(user_record['data']) - on_count
            if off_count != 0:
                ratio = on_count / off_count
            elif on_count != 0:
                ratio = off_count / on_count
            else:
                ratio = 1
            if ratio > 1:
                    ratio = 1 / ratio
            ratios.append(ratio)
            if ratio < threshold_ratio:
                ratio_users.append(user_record['_id'])
            if len(user_record['data']) > 1:
                proportion = same_count / (len(user_record['data'])-1)
            else:
                proportion = 0
            proportions.append(proportion)
            if proportion > threshold_proportion:
                proportion_users.append(user_record['_id'])
            #print(proportion, ratio)
        return proportions, ratios, proportion_users, ratio_users
            
    
    def findByAtt(self, attendeecode):
        df = pd.DataFrame.from_records(
            self.client.smartsleep.users.find({"attendeeCode":attendeecode})
        )
        if df.empty:
            raise Exception("No user found")
            return -1
        else:
            return str(df._id[0])
    
    def make_density_plot(user, filter_date_from,filter_date_to):
        heartbeats         = pd.DataFrame.from_records(
            self.client.smartsleep.heartbeats.find({"userId":user})
        )
        sleeps             = pd.DataFrame.from_records(
            self.client.smartsleep.sleeps.find({"userId":user})
        )
        parts = []
        if not heartbeats.empty:
            heartbeats['time'] = pd.DatetimeIndex(
                heartbeats['time']) + timedelta(hours=1,minutes=0
            )
            heartbeats         = heartbeats[heartbeats.time >= filter_date_from]
            heartbeats         = heartbeats[heartbeats.time <= filter_date_to]
        if not heartbeats.empty:
            parts.append(hv.Spikes(heartbeats.time, label="heartbeats").
                         opts(spike_length=1,color="red").opts(tools=['hover']))
        if not sleeps.empty:
            sleeps['time']     = pd.DatetimeIndex(sleeps['time']) + timedelta(hours=1,minutes=0)
            sleeps             = sleeps[sleeps.time >= filter_date_from]
            sleeps             = sleeps[sleeps.time <= filter_date_to]
        if not sleeps.empty:
            if sleeps.sleeping.any():
                parts.append(hv.Spikes(sleeps[sleeps.sleeping].time, label="screen off").opts(
                    spike_length=1,color="blue").opts(tools=['hover']))
            if (~sleeps.sleeping).any():
                parts.append(hv.Spikes(sleeps[~sleeps.sleeping].time,label="screen on").opts(
                    spike_length=1,color="green").opts(tools=['hover']))
        print(f'{sleeps.shape[0]} sleeps')
        print(f'{heartbeats.shape[0]} heartbeats')
        return hv.Overlay(parts).opts(width=900,height=300,
                                      legend_position='top_left',
                                      toolbar='above', yaxis=None, padding=0.1
                                     )
