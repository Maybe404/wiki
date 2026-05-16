"""Seed SkillVersion v0.1 from skills/html-document/SKILL.md.

Fails loudly if no superuser exists — do not create a fake user.
"""

import os

from django.db import migrations

SKILL_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    "skills",
    "html-document",
    "SKILL.md",
)


def seed_skill(apps, schema_editor):
    SkillVersion = apps.get_model("skills", "SkillVersion")
    User = apps.get_model("auth", "User")

    if SkillVersion.objects.filter(version="v0.1").exists():
        return

    superuser = User.objects.filter(is_superuser=True).first()
    if superuser is None:
        import warnings

        warnings.warn(
            "SkillVersion v0.1 seed skipped: no superuser found. "
            "Run `uv run manage.py createsuperuser` then re-run migrations, or seed manually.",
            stacklevel=2,
        )
        return

    skill_path = os.path.normpath(SKILL_PATH)
    if not os.path.exists(skill_path):
        raise RuntimeError(f"SKILL.md not found at {skill_path}")

    with open(skill_path, encoding="utf-8") as f:
        content = f.read()

    SkillVersion.objects.create(
        version="v0.1",
        content=content,
        notes="从 skills/html-document/SKILL.md 初始导入",
        is_active=True,
        created_by=superuser,
    )


def unseed_skill(apps, schema_editor):
    SkillVersion = apps.get_model("skills", "SkillVersion")
    SkillVersion.objects.filter(version="v0.1").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("skills", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_skill, unseed_skill),
    ]
