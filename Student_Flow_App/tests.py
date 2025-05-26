# import json
# from django.test import TestCase
# from LMS_Project.Blobstorage import *
# from LMS_MSSQLdb_App.models import *
# def UPDATE_Counts():
#     try:
#         blob_client = get_blob_container_client()
#         count ={}
#         mcq_count = 0
#         coding_count = 0
#         videos_count = 0
#         notes_count = 0
#         test = []
#         print('start')
#         for blob in blob_client.list_blobs(name_starts_with='subjects/sq/'):
#             # print( blob.name.replace('subjects/sq/',''))   
#             if count.get(blob.name.replace('subjects/sq/','').split('/')[1],None) == None: 
#                 count.update({
#                     blob.name.replace('subjects/sq/','').split('/')[1]:{
#                         'mcq':0,
#                         'coding':0,
#                         'videos':0,
#                         'notes':0
#                     }
#                 })
#             if blob.name.split('/')[-1].split('.')[-1] not in test:
#                 test.append(blob.name.split('/')[-1].split('.')[-1])
#             if blob.name.split('/')[-1].endswith('.mp4'):
#                 videos_count = videos_count + 1
#                 count.get(blob.name.replace('subjects/sq/','').split('/')[1]).update({'videos':
#                                                                                       count.get(blob.name.replace('subjects/sq/','').split('/')[1]).get('videos')+1})
#             elif blob.name.split('/')[-1].endswith('.pdf'):
#                 notes_count = notes_count + 1
#                 count.get(blob.name.replace('subjects/sq/','').split('/')[1]).update({'notes':
#                                                                                       count.get(blob.name.replace('subjects/sq/','').split('/')[1]).get('notes')+1})
#             elif blob.name.split('/')[-1].endswith('.json'):
#                 if blob.name.split('/')[-2] == 'mcq':
#                     mcq_count = mcq_count + 1
#                     count.get(blob.name.replace('subjects/sq/','').split('/')[1]).update({'mcq':
#                                                                                       count.get(blob.name.replace('subjects/sq/','').split('/')[1]).get('mcq')+1})
#                 elif blob.name.split('/')[-2] == 'coding':
#                     coding_count = coding_count + 1
#                     count.get(blob.name.replace('subjects/sq/','').split('/')[1]).update({'coding':
#                                                                                       count.get(blob.name.replace('subjects/sq/','').split('/')[1]).get('coding')+1})
#             else:
#                 pass
#         print('count',notes_count,videos_count,mcq_count,coding_count)
#         qns = sub_topics.objects.all()
#         for qn in qns:
#             if qn.sub_topic_id.startswith('sq'):
#                 if count.get(qn.sub_topic_id,None) is not None:
#                     print(qn.sub_topic_id,count.get(qn.sub_topic_id,None))
#                     # qn.mcq = count.get(qn.sub_topic_id,None).get('mcq')
#                     # qn.coding = count.get(qn.sub_topic_id,None).get('coding')
#                     # qn.videos = count.get(qn.sub_topic_id,None).get('videos')
#                     # qn.notes = count.get(qn.sub_topic_id,None).get('notes')
#                     # qn.save()
#         print('test',test) 
        
#     except Exception as e:
#         print(e)
#         pass
# # UPDATE_Counts()