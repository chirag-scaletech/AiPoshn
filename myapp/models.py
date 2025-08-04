from django.db import models

class Teacher(models.Model):
    username_en = models.CharField(max_length=100)
    username_gu = models.CharField(max_length=100)
    school_en = models.CharField(max_length=200)
    school_gu = models.CharField(max_length=200)
    location_en = models.CharField(max_length=200)
    location_gu = models.CharField(max_length=200)


def __str__(self):
        return self.username_en
