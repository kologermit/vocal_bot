from Model import Model, Column
UserModel = Model(
    "users", [
    Column("telegram_id", "BIGINT NOT NULL"),
    Column("full_name", "TEXT NOT NULL"),
    Column("grade", "INT NOT NULL DEFAULT -1"),
    Column("user_name", "TEXT NOT NULL"),
    Column("state", "TEXT NOT NULL DEFAULT 'menu'"),

    Column("current_test", "JSON NOT NULL DEFAULT 'null'"),
    Column("accepted_tests", "JSON NOT NULL DEFAULT '[]'"),

    Column("accepted_theory", "JSON NOT NULL DEFAULT '[]'"),

    Column("first_message", "DATE"),
])

name_column = Column("name", "TEXT NOT NULL DEFAULT 'TestName'")
description_column = Column("description", "TEXT NOT NULL DEFAULT 'TestDescription'")
description_files_column = Column("files", "JSON NOT NULL DEFAULT '[]'")

TheoryModel = Model(
    "theory", [
        name_column, description_column,description_files_column,
    Column("paragraphs", "JSON NOT NULL DEFAULT '[]'"),
])

TestModel = Model(
    "test", [
        name_column, description_column, description_files_column,
        Column("questions", "JSON NOT NULL DEFAULT '[]'"),
        Column("tasks", "JSON NOT NULL DEFAULT '[]'"),
])

all_models = [UserModel, TheoryModel, TestModel]