from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models


class SkillVersion(models.Model):
    version = models.CharField(max_length=20, unique=True)
    content = models.TextField()
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="skill_versions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["is_active"],
                condition=models.Q(is_active=True),
                name="single_active_skill",
            )
        ]

    def __str__(self) -> str:
        active = " [active]" if self.is_active else ""
        return f"SkillVersion {self.version}{active}"
