import sqlite3, json, logging
from Model import Model
from typing import Any
from copy import deepcopy

class DBManager:
    __conn__ = None
    __filename__ = None

    def __init__(self, filename: str):
        self.__conn__ = sqlite3.connect(filename, check_same_thread=False)
        self.__filename__ = filename

    def init_tables(self, models: list[Model]):
        for model in models:
            columns = model.get_columns()
            self.__conn__.execute(f"""CREATE TABLE IF NOT EXISTS {model.get_table()} (
                                 {",".join([f"{column.get_name()} {column.get_type()}" for column in columns])}
                                )""")
        self.__conn__.commit()

    def find_data(self, model: Model, find_by_id=False, condition: str = "true", condition_data: list[Any] = []) -> list[Model]:
        if find_by_id:
            condition = "rowid=?"
            condition_data = [model.rowid]
        sql = f"""SELECT rowid, {', '.join(model.get_columns_name())} FROM {model.get_table()} 
            WHERE {condition}"""
        result = []
        for data in self.__conn__.execute(sql, condition_data):
            new_model = deepcopy(model)
            new_model.rowid = data[0]
            for i, column in enumerate(model.get_columns()):
                if "JSON" in column.get_type():
                    new_model.setattr(column.get_name(), json.loads(data[i+1]))
                else:
                    new_model.setattr(column.get_name(), data[i+1])
            result.append(new_model)
        return result

    def save_data(self, model: Model):
        columns = model.get_exists_attrs()
        data = [model.getattr(column) for column in columns]
        for i, value in enumerate(deepcopy(data)):
            if model.is_json_cloumn(columns[i]):
                data[i] = json.dumps(value)
        if model.rowid == -1:
            sql = f"INSERT INTO {model.get_table()} ({', '.join(columns)}) \nVALUES ("
            sql += "?, " * len(columns)
            sql = sql.strip()[:-1] + ")"
            self.__conn__.execute(sql, data)
            self.__conn__.commit()
            for data in self.__conn__.execute("SELECT last_insert_rowid();"):
                model.rowid = data[0]
            return
        sql = f"UPDATE {model.get_table()} SET "
        for column in columns:
            sql += column + "=?,\n"
        sql = sql.strip()[:-1]  + "WHERE rowid=?"
        data.append(model.rowid)
        self.__conn__.execute(sql, data)
        self.__conn__.commit()

    def delete_data(self, model: Model, condition: str = None, condition_data: list[Any] = []):
        if condition is None:
            sql = f"DELETE FROM {model.get_table()} WHERE rowid=?"
            data = [model.rowid]
        else:
            sql = f"DELETE FROM {model.get_table()} WHERE {condition}"
            data = condition_data
        self.__conn__.execute(sql, data)
        self.__conn__.commit()