import base64
import json
import os


from contextlib import contextmanager

from sqlalchemy import create_engine, engine
from sqlalchemy.engine.base import Engine



host = ""
username = "miview"
password = ""
db_port = 3306


def conn(db_name: str) -> Engine:
    db_uri = f"mysql://{username}:{password}@{host}:{db_port}/{db_name}?charset=utf8"
    return create_engine(db_uri, encoding="utf-8")


def get_user_folder_id(user_id):
    engine = conn("miview")
    sql = f"SELECT folder_id FROM user WHERE ID = {user_id}"
    folder_id = engine.execute(sql).first()[0]
    engine.dispose()
    return folder_id

def get_user_img_count(user_id):
    engine = conn("miview")
    sql = f"SELECT img_count FROM user WHERE ID = {user_id}"
    img_count = engine.execute(sql).first()[0]
    if img_count is None:
        img_count = 0
    engine.dispose()
    return img_count

def update_user_info(user_id,len_of_files):
    engine = conn("miview")
    sql = f"UPDATE user SET img_count = {len_of_files} WHERE ID = {user_id};"\
        f"INSERT INTO status(user_id, status) VALUES({user_id},'SUCCESS');"
    engine.execute(sql)
    
    engine.dispose()
