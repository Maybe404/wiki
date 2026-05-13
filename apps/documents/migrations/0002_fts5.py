from django.db import migrations

# Contentless FTS5 表：不依赖 content= 参数，由触发器与应用层手动维护。
# INSERT/DELETE 触发器同步 title；plain_text 由应用层（DocumentVersion 保存后）更新。
# UPDATE 触发器：title 改名时，DELETE 旧行 + INSERT 新行（plain_text 置空，等应用层更新）。

CREATE_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    title,
    plain_text,
    tokenize='unicode61'
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

DROP_UPDATE_TRIGGER = "DROP TRIGGER IF EXISTS documents_fts_au;"
DROP_DELETE_TRIGGER = "DROP TRIGGER IF EXISTS documents_fts_ad;"
DROP_INSERT_TRIGGER = "DROP TRIGGER IF EXISTS documents_fts_ai;"
DROP_FTS = "DROP TABLE IF EXISTS documents_fts;"


class Migration(migrations.Migration):
    dependencies = [
        ("documents", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[CREATE_FTS, CREATE_INSERT_TRIGGER, CREATE_DELETE_TRIGGER, CREATE_UPDATE_TRIGGER],
            reverse_sql=[DROP_UPDATE_TRIGGER, DROP_DELETE_TRIGGER, DROP_INSERT_TRIGGER, DROP_FTS],
        ),
    ]
