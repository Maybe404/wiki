"""将 FTS5 表从 unicode61 tokenizer 迁移到 trigram，支持中文字符级搜索。"""

from django.db import migrations

# 重建 FTS 表（连带触发器）—— 每条语句必须独立
DROP_OLD_AU = "DROP TRIGGER IF EXISTS documents_fts_au;"
DROP_OLD_AD = "DROP TRIGGER IF EXISTS documents_fts_ad;"
DROP_OLD_AI = "DROP TRIGGER IF EXISTS documents_fts_ai;"
DROP_OLD_TABLE = "DROP TABLE IF EXISTS documents_fts;"

CREATE_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    title,
    plain_text,
    tokenize='trigram'
);
"""

CREATE_INSERT_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS documents_fts_ai
AFTER INSERT ON documents_document BEGIN
    INSERT INTO documents_fts(rowid, title, plain_text)
    VALUES (new.rowid, new.title, '');
END;
"""

CREATE_DELETE_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS documents_fts_ad
AFTER DELETE ON documents_document BEGIN
    DELETE FROM documents_fts WHERE rowid = old.rowid;
END;
"""

CREATE_UPDATE_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS documents_fts_au
AFTER UPDATE OF title ON documents_document BEGIN
    DELETE FROM documents_fts WHERE rowid = old.rowid;
    INSERT INTO documents_fts(rowid, title, plain_text)
    VALUES (new.rowid, new.title, '');
END;
"""

# 将现有文档的 title 回填到新 FTS 表（plain_text 由应用层后续更新）
BACKFILL = """
INSERT INTO documents_fts(rowid, title, plain_text)
SELECT rowid, title, '' FROM documents_document WHERE is_deleted = 0;
"""

# 回滚：重建 unicode61 版本（不含数据）
DROP_TRIGRAM_AU = "DROP TRIGGER IF EXISTS documents_fts_au;"
DROP_TRIGRAM_AD = "DROP TRIGGER IF EXISTS documents_fts_ad;"
DROP_TRIGRAM_AI = "DROP TRIGGER IF EXISTS documents_fts_ai;"
DROP_TRIGRAM_TABLE = "DROP TABLE IF EXISTS documents_fts;"

CREATE_FTS_UNICODE61 = """
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    title,
    plain_text,
    tokenize='unicode61'
);
"""


class Migration(migrations.Migration):
    dependencies = [
        ("documents", "0002_fts5"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                DROP_OLD_AU,
                DROP_OLD_AD,
                DROP_OLD_AI,
                DROP_OLD_TABLE,
                CREATE_FTS,
                CREATE_INSERT_TRIGGER,
                CREATE_DELETE_TRIGGER,
                CREATE_UPDATE_TRIGGER,
                BACKFILL,
            ],
            reverse_sql=[
                DROP_TRIGRAM_AU,
                DROP_TRIGRAM_AD,
                DROP_TRIGRAM_AI,
                DROP_TRIGRAM_TABLE,
                CREATE_FTS_UNICODE61,
                CREATE_INSERT_TRIGGER,
                CREATE_DELETE_TRIGGER,
                CREATE_UPDATE_TRIGGER,
            ],
        ),
    ]
