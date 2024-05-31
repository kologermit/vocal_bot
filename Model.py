from typing import Any
from copy import deepcopy

class Column:
    __name__ = str()
    __type__ = str()

    def __init__(self, name: str, type: str=""):
        self.__name__ = name
        self.__type__ = type

    def get_name(self):
        return self.__name__
    
    def get_type(self):
        return self.__type__

class Model(object):
    def __init__(self, table: str, columns: list[Column]):
        self.__dict__["__table__"] = table
        self.__dict__["__columns__"] = columns

    def __deepcopy__(self, memo):
        my_copy = type(self)(self.__table__, self.__columns__)
        memo[id(self)] = my_copy
        for key, item in self.__dict__.items():
            my_copy.__dict__[key] = deepcopy(self.__dict__[key], memo)
        return my_copy
    
    @property
    def rowid(self):
        if self.__dict__.get("rowid"):
            return self.__dict__.get("rowid")
        return -1

    def get_table(self):
        return self.__table__
    
    def get_columns(self) -> list[Column]:
        return self.__columns__
        
    def get_columns_name(self):
        return [column.get_name() for column in self.__columns__]
    
    def is_attr(self, attr: str):
        return attr in self.__dict__
    
    def get_exists_attrs(self):
        res = list(
                map(lambda column: column.get_name(), 
                    filter(lambda column: column.get_name() in self.__dict__, self.__columns__)))
        return res
    
    def is_json_cloumn(self, column: str):
        for col in self.__columns__:
            if col.get_name() == column and "JSON" in col.get_type():
                return True
        return False
    
    def __str__(self):
        res = f"{self.__table__}[rowid={self.rowid} "
        for column in self.get_columns_name():
            res += f"{column}={self.__dict__.get(column)} "
        return res.strip() + "]"

    def __setattr__(self, name: str, data: Any):
        self.__dict__[name] = data

    setattr = __setattr__

    def __getattr__(self, name: str):
        return self.__dict__[name]
    
    getattr = __getattr__