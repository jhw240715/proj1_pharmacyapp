from django.db import models
from django.contrib.auth.models import User

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    pword = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user'


class Pharmacy(models.Model):
    pname = models.CharField(max_length=100, blank=True, null=True)
    p_id = models.AutoField(primary_key=True)
    paddr = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pharmacy'

    def __str__(self):
        return self.pname


class Board(models.Model):
    board_id = models.AutoField(primary_key=True)
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='boards', to_field='p_id')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=20, blank=True, null=True)
    content = models.CharField(max_length=100, blank=True, null=True)
    uptime = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'board'

    def __str__(self):
        return f"{self.board_id}: {self.title}"

    @property
    def pname(self):
        return self.pharmacy.pname if self.pharmacy else None



class Score(models.Model):
    p = models.ForeignKey(Pharmacy, on_delete=models.CASCADE)
    q1_score = models.IntegerField(blank=True, null=True)
    q2_score = models.IntegerField(blank=True, null=True)
    q3_score = models.IntegerField(blank=True, null=True)
    q4_score = models.IntegerField(blank=True, null=True)
    q5_score = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'score'