from django.db import models

class Teacher(models.Model):
    username_en = models.CharField(max_length=100)
    username_gu = models.CharField(max_length=100)

    def __str__(self):
        return self.username_en
