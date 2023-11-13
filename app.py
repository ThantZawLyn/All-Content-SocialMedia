import enum
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import pyidaungsu as pds
import os
import sqlalchemy as db
import re
from keras.models import load_model
import emoji
import time
from random import randint
from time import sleep
from googletrans import Translator
translator = Translator()
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import VARCHAR, Boolean, Column, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import BYTEA, ENUM
from sqlalchemy.orm import relationship
from sqlalchemy import update

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' # hide warning
# from ..constants import SQLALCHEMY_DATABASE_URI
#engine = create_engine(SQLALCHEMY_DATABASE_URI)
engine = create_engine('postgresql://fbs:yah7WUy1Oi8G@172.32.253.129:5432/fbs', echo=False)

Base = declarative_base(bind=engine)
session_creator = sessionmaker()
DBSession = session_creator()

class LikeType(enum.Enum):
    like = "like"
    love = "love"
    haha = "haha"
    wow = "wow"
    sad = "sad"
    angry = "angry"

class TaskType(str, enum.Enum):
    keyword: str = "keyword"
    source: str = "source"
    like: str = "like"
    comment: str = "comment"
    share: str = "share"
    personal_page: str = "personal_page"

class SubtaskType(str, enum.Enum):
    like: str = "like"
    comment: str = "comment"
    share: str = "share"
    personal_page: str = "personal_page"

class TaskStatus(str, enum.Enum):
    in_queue: str = "in_queue"
    in_progress: str = "in_progress"
    success: str = "success"
    retry: str = "retry"
    failed: str = "failed"

class Subtask(Base):
    __tablename__ = 'subtasks'
    id = Column('id', Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'))
    post = relationship("Post", back_populates="subtasks", uselist=False)

    subtask_type = Column(ENUM(SubtaskType))

    start_time = Column('start_time', DateTime)
    end_time = Column('end_time', DateTime)

    status = Column(ENUM(TaskStatus))

class SubtaskPersonalData(Base):
    __tablename__ = 'subtask_personal_data'
    id = Column('id', Integer, primary_key=True)
    subtask_id = Column(Integer, ForeignKey('subtasks.id'))
    subtask = relationship("Subtask")

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User")

class Post(Base):
    __tablename__ = 'posts'

    def __hash__(self):
        return hash(self.fb_post_id)

    def __eq__(self, other):
        return isinstance(other, Post) and self.fb_post_id == other.fb_post_id

    id = Column('id', Integer, primary_key=True)
    date = Column('date', DateTime)
    last_time_updated = Column('last_time_updated', DateTime)
    fb_post_id = Column('fb_post_id', VARCHAR(1024))
    fb_repost_id = Column('fb_repost_id', VARCHAR(128))
    fb_repost_link = Column('fb_repost_link', VARCHAR(2048))
    fb_post_link = Column('fb_post_link', VARCHAR(1024))
    fb_post_link_likes = Column('fb_post_link_likes', VARCHAR(1024))
    content_id = Column(Integer, ForeignKey('content.id'))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    stat_id = Column(Integer, ForeignKey('post_stat.id'))

    content = relationship("Content", back_populates="post", uselist=False)
    likes = relationship("Like", back_populates="post")
    comments = relationship("Comment", back_populates="post")
    shares = relationship("Share", back_populates="post")
    user = relationship("User", back_populates="post", uselist=False)
    task = relationship("Task", back_populates="post", uselist=False)
    stat = relationship("PostStat", back_populates="post", uselist=False)
    subtasks = relationship("Subtask", back_populates="post", uselist=True)

class PostStat(Base):
    __tablename__ = 'post_stat'
    id = Column('id', Integer, primary_key=True)
    likes = Column('likes', VARCHAR(32))
    comments = Column('comments', VARCHAR(32))
    shares = Column('shares', VARCHAR(32))

    post = relationship("Post", back_populates="stat", uselist=False)

    def is_equals(self, post_stat):
        return self.likes == post_stat.likes and self.comments == post_stat.comments and self.shares == post_stat.shares

class Content(Base):
    __tablename__ = 'content'
    id = Column('id', Integer, primary_key=True)
    text = Column('text', VARCHAR(1024))
    nlp_id = Column(Integer, ForeignKey('nlp.id'),  nullable=True)

    post = relationship("Post", back_populates="content", uselist=False)
    comment = relationship("Comment", back_populates="content", uselist=False)
    photos = relationship("Photo", back_populates="content", uselist=True)
    videos = relationship("Video", back_populates="content", uselist=True)

class NLP(Base):
    __tablename__ = 'nlp'
    id = Column('id', Integer, primary_key=True)
    Category = Column('category', VARCHAR(255))
    
class Photo(Base):
    __tablename__ = 'photos'
    id = Column('id', Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey('content.id'))
    photo_link = Column('photo_link', VARCHAR(1024))

    content = relationship("Content", back_populates="photos")

class Video(Base):
    __tablename__ = 'videos'
    id = Column('id', Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey('content.id'))
    video_link = Column('video_link', VARCHAR(1024))

    content = relationship("Content", back_populates="videos")

class Like(Base):
    __tablename__ = 'likes'

    id = Column(Integer, primary_key=True)

    post_id = Column(Integer, ForeignKey('posts.id'))
    post = relationship("Post", back_populates="likes")

    comment_id = Column(Integer, ForeignKey('comments.id'))
    comment = relationship("Comment", back_populates="likes")

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="likes")

    like_type = Column(ENUM(LikeType))

class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True)

    date = Column(DateTime)
    fb_comment_id = Column('fb_comment_id', VARCHAR(255))

    content_id = Column(Integer, ForeignKey('content.id'))
    content = relationship("Content", back_populates="comment")

    post_id = Column(Integer, ForeignKey('posts.id'))
    post = relationship("Post", back_populates="comments")

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="comments")

    parent_comment_id = Column(Integer, ForeignKey('comments.id'))
    parent_comment = relationship("Comment", back_populates="child_comments", remote_side=[id])
    child_comments = relationship("Comment", back_populates="parent_comment", remote_side=[parent_comment_id])

    likes = relationship("Like", back_populates="comment")
    likes_count = Column('likes_count', Integer)

class Share(Base):
    __tablename__ = 'shares'

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'))
    post = relationship("Post", back_populates="shares")

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="shares")

class UserUniversity(Base):
    __tablename__ = 'user_university'
    id = Column(Integer, primary_key=True)
    name = Column('name', VARCHAR(1024))
    info = Column('info', VARCHAR(1024))
    link = Column('link', VARCHAR(1024))

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="universities")

class UserJob(Base):
    __tablename__ = 'user_job'
    id = Column(Integer, primary_key=True)
    name = Column('name', VARCHAR(1024))
    info = Column('info', VARCHAR(1024))
    link = Column('link', VARCHAR(1024))

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="jobs")

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)

    name = Column("name", VARCHAR(1024))
    link = Column("link", VARCHAR(1024))
    sex = Column("sex", VARCHAR(8))
    city_of_birth = Column("city_of_birth", VARCHAR(128))
    current_city = Column("current_city", VARCHAR(128))
    birthday = Column("birthday", VARCHAR(128))
    fb_id = Column("fb_id", VARCHAR(32))
    check = Column("check",Boolean)
    
    likes = relationship("Like", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    shares = relationship("Share", back_populates="user")
    post = relationship("Post", back_populates="user")

    universities = relationship("UserUniversity", back_populates="user")
    jobs = relationship("UserJob", back_populates="user")

class Task(Base):
    __tablename__ = 'tasks'
    id = Column('id', Integer, primary_key=True)
    interval = Column('interval', Integer)
    retro = Column('retro', DateTime)
    until = Column('until', DateTime)
    received_time = Column('received_time', DateTime)
    finish_time = Column('finish_time', DateTime)
    status = Column(ENUM(TaskStatus))
    enabled = Column('enabled', Boolean)
    post = relationship("Post", back_populates="task")

class TaskKeyword(Base):
    __tablename__ = 'tasks_keyword'
    id = Column('id', Integer, primary_key=True)
    keyword = Column('keyword', VARCHAR(255))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    task = relationship("Task")

class TaskSource(Base):
    __tablename__ = 'tasks_source'
    id = Column('id', Integer, primary_key=True)
    source_id = Column('source_id', VARCHAR(255))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    task = relationship("Task")

class WorkerCredential(Base):
    __tablename__ = 'worker_credentials'
    id = Column('id', Integer, primary_key=True)
    inProgress = Column('inProgress', Boolean)
    inProgressTimeStamp = Column('in_progress_timestamp', DateTime)
    last_time_finished = Column('last_time_finished', DateTime)
    locked = Column('locked', Boolean)
    alive_timestamp = Column('alive_timestamp', DateTime)

    account_id = Column(Integer, ForeignKey('accounts.id'))
    proxy_id = Column('proxy_id', ForeignKey('proxy.id'))
    user_agent_id = Column('user_agent_id', ForeignKey('user_agent.id'))

    account = relationship("FBAccount", uselist=False)
    proxy = relationship("Proxy", uselist=False)
    user_agent = relationship("UserAgent", uselist=False)

class WorkingCredentialsTasks(Base):
    __tablename__ = 'worker_credentials_tasks'
    id = Column('id', Integer, primary_key=True)
    worker_credentials_id = Column(Integer, ForeignKey('worker_credentials.id'))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    type = Column('type', VARCHAR(16))
    start_timestamp = Column('start_timestamp', DateTime)
    finish_timestamp = Column('finish_timestamp', DateTime)

class Proxy(Base):
    __tablename__ = 'proxy'
    id = Column('id', Integer, primary_key=True)
    host = Column('host', VARCHAR(255))
    port = Column('port', Integer)
    login = Column('login', VARCHAR(255))
    password = Column('password', VARCHAR(255))
    available = Column('available', Boolean)
    last_time_checked = Column('last_time_checked', DateTime)
    attempts = Column('attempts', Integer)

class FBAccount(Base):
    __tablename__ = 'accounts'
    id = Column('id', Integer, primary_key=True)
    login = Column('login', VARCHAR(255))
    password = Column('password', VARCHAR(255))
    available = Column('available', Boolean, nullable=False)
    cookies = relationship("Cookies", uselist=False)
    availability_check = Column('availability_check', DateTime)

class Cookies(Base):
    __tablename__ = 'cookies'
    id = Column('id', Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id'))
    row_data = Column('row_data', BYTEA)

class UserAgent(Base):
    __tablename__ = 'user_agent'
    id = Column('id', Integer, primary_key=True)
    userAgentData = Column('userAgentData', VARCHAR(2048))
    window_size_id = Column(Integer, ForeignKey('window_size.id'))
    window_size = relationship("WindowSize")

class WindowSize(Base):
    __tablename__ = 'window_size'
    id = Column('id', Integer, primary_key=True)
    width = Column('width', Integer)
    height = Column('height', Integer)

def tokenize(line):
    sentence = pds.tokenize(line,form="word")
    return sentence
            
loaded_model_comment = load_model('model7.h5')
vectorizer_comment = pickle.load(open("vectorizer.pickle2", "rb"))

# LSTM
loaded_model_content = load_model('8class_lstm_27_4.h5')
vectorizer_content = pickle.load(open("vectorizer_8class_lstm_27_4.pickle", "rb"))
# loaded_model_content = load_model('lstm_1.2.h5')
# vectorizer_content = pickle.load(open("vectorizer_8class_lstm_1.2.pickle", "rb"))

stopwordslist = []
slist = []
with open("./stopword.txt", encoding = 'utf8') as stopwordsfile:
    stopwords = stopwordsfile.readlines()
    slist.extend(stopwords)

    for w in range(len(slist)):
        temp = slist[w]
        stopwordslist.append(temp.rstrip())

CleanPattern = re.compile(r'\d+|[၊။+#…!-/:-@[-`.{-~\t]|[A-za-z0-9]')
def clean_sentence(sentence):
    sentence = sentence.replace("_"," ")
    sent = CleanPattern.sub(" ",sentence)
    return sent
def remove_emoji(sentence):
    new_text=emoji.demojize(sentence)
    return new_text

def stop_word(sentence):
    new_sentence = []
    for word in sentence.split():
        if word not in stopwordslist:
            new_sentence.append(word)
    return(' '.join(new_sentence))

def tokenize(line):
    line= remove_emoji(line)
    line = clean_sentence(line)
    sentence = pds.tokenize(line,form="word")
    sentence = ' '.join([str(elem) for elem in sentence])
    sentence = stop_word(sentence)
    return sentence

# SVM
# filename = '8class_svm.sav'
# loaded_model = pickle.load(open(filename, 'rb'))
# vectorizer = pickle.load(open("vectorizer_8class_svm.pickle", "rb"))

start_time = time.time()

max_empty_attempts = 100
empty_attempts = 0

while True:
    records_found = False
    a = (DBSession.query(Content.text, Content.id)
                 .filter(Content.nlp_id == None)
                 .filter(Content.text != None)
                 .filter(Content.id >= 666511)
                 .order_by(Content.id.desc())
                 .limit(1))
    
    for row in a:
        records_found = True
        TEXT = row.text
        ID = row.id

        fb_content = DBSession.query(Post.content_id).filter(Post.content_id == ID).first() #check if content
        
        if fb_content: 
            print("\033[34mFacebook Content ID : \033[0m" + f"\033[34m{str(ID)}\033[0m")
            try:
                #print(len(TEXT))
                modified_text = TEXT
                if modified_text.startswith("http://") or modified_text.startswith("https://"):
                    modified_text = "This is link " + modified_text

                single_line_string = modified_text.replace("\n", " ")
                detect = pds.detect(single_line_string)
                print("\033[35mLanguage : \033[0m" + f"\033[35m{detect}\033[0m")
                #print(single_line_string)
                if detect == "zg":
                    text = pds.cvt2uni(single_line_string)
                    print(text)
                elif detect == "uni":
                    text = single_line_string
                    print(text)
                elif detect == "eng" and len(single_line_string) > 3000:
                    single_line_string = single_line_string[:3000]
                    translate_text = translator.translate(single_line_string, dest='my')
                    text = translate_text.text
                    print(text)
                elif detect == "eng" :
                    translate_text = translator.translate(single_line_string, dest='my')
                    text = translate_text.text
                    print(text)
                    # translate_text = translator.translate(single_line_string, dest='my')
                    # text = translate_text.text
                else:
                    # translate_text = translator.translate(single_line_string, dest='en')
                    # text = translate_text.text
                    # translate_text = translator.translate(text, dest='my')
                    # text = translate_text.text
                    text = single_line_string
                    print(text)

                user = tokenize(text)
                data2 = vectorizer_content.transform([user]).toarray()
                output = loaded_model_content.predict(data2)
                output = np.argmax(output)

                if output is None:
                    print("\033[32mNo output \033[0m")
                elif output == 0:
                    res = 4
                    print("\033[32mPolitics \033[0m")
                elif output == 1:
                    res = 5
                    print("\033[32mEntertainment \033[0m")
                elif output == 2:
                    res = 6
                    print("\033[32mBusiness \033[0m")
                elif output == 3:
                    res = 7
                    print("\033[32mSport \033[0m ")
                elif output == 4:
                    res = 11
                    print("\033[32mSocial \033[0m")
                elif output == 5:
                    res = 8
                    print("\033[32mCrime \033[0m")
                elif output == 6:
                    res = 9
                    print("\033[32mHealth \033[0m")
                elif output == 7:
                    res = 10
                    print("\033[32mEducation and Technology \033[0m")
                        
                stmt = (update(Content).where(Content.id == ID).values(nlp_id=res))
                DBSession.execute(stmt, execution_options={"synchronize_session": False})
                DBSession.commit() 
                
            except Exception as e:
                print("Error encountered:", e)
            
            print("----------------------------------------------------------------")

        # if not if_content:
        #     print("This is not a content : " + str(ID))
        #     DBSession.commit()
        else:
            print("\033[34mComment ID : \033[0m" + f"\033[34m{str(ID)}\033[0m")
            modified_text = TEXT
            if modified_text.startswith("http://") or modified_text.startswith("https://"):
                modified_text = "This is link " + modified_text

            single_line_string = modified_text.replace("\n", " ")
            detect = pds.detect(single_line_string)
            print("\033[35mLanguage : \033[0m" + f"\033[35m{detect}\033[0m")
            #print(single_line_string)
            if detect == "zg":
                text = pds.cvt2uni(single_line_string)
            elif detect == "uni":
                text = single_line_string
            elif detect == "eng" and len(single_line_string) > 3000:
                single_line_string = single_line_string[:3000]
                translate_text = translator.translate(single_line_string, dest='my')
                text = translate_text.text
            elif detect == "eng" :
                translate_text = translator.translate(single_line_string, dest='my')
                text = translate_text.text
                print(text)
                # translate_text = translator.translate(single_line_string, dest='my')
                # text = translate_text.text
            else:
                # translate_text = translator.translate(single_line_string, dest='en')
                # text = translate_text.text
                # translate_text = translator.translate(text, dest='my')
                # text = translate_text.text
                text = single_line_string
            print(text)

            user = tokenize(text)
            data2 = vectorizer_comment.transform([user]).toarray()
            output = loaded_model_comment.predict(data2)
            
            if output is None:
                print("\033[32mNo output \033[0m")
            elif output > 0.70 :
                res = 1
                print("\033[32mPositive \033[0m")  
            elif 0.05 < output < 0.70 :
                res = 2
                print("\033[32mNatural \033[0m") 
            elif output < 0.05 :
                res = 3
                print("\033[32mNegative \033[0m") 
            stmt = (update(Content).where(Content.id == ID).values(nlp_id=res))
            DBSession.execute(stmt, execution_options={"synchronize_session": False})
            #DBSession.commit() 
            print("----------------------------------------------------------------")
        #sleep(0.5)
    # if ID <800000:
    #     break
    if not records_found:
        print("No records found with nlp_id set to None.")
        #empty_attempts += 1
        sleep(120)
        # if empty_attempts >= max_empty_attempts:
        #     print("Max attempts reached without finding records. Exiting.")
        #     break
        
    
