import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    email = models.EmailField(
        error_messages={"unique": "A user with that email already exists"},
        db_index=True
    )
    mobile_number = models.CharField(
        max_length=50, null=True, blank=True,
        help_text="Unique mobile number with country code",
        error_messages={"unique": "A user with that mobile number already exists"},
    )

    def __str__(self):
        return self.email

    class Meta:
        ordering = ('first_name',)
        verbose_name_plural = 'Users'
        verbose_name = 'User'
