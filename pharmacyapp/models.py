from django.db import models
from django.contrib.auth.models import User

class Pharmacy(models.Model):
    name = models.CharField(max_length=100, null=False)
    address = models.CharField(max_length=100, null=False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'pharmacy'

    def __str__(self):
        return self.name

class Board(models.Model):
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='boards')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, null=False)
    content = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'board'
        unique_together = (('pharmacy', 'user'),)

    def __str__(self):
        return self.title

class Score(models.Model):
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, related_name='scores')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    q1_score = models.IntegerField(null=False)
    q2_score = models.IntegerField(null=False)
    q3_score = models.IntegerField(null=False)
    q4_score = models.IntegerField(null=False)
    q5_score = models.IntegerField(null=False)

    class Meta:
        db_table = 'score'
        unique_together = (('pharmacy', 'user'),)

    def __str__(self):
        return f"Score for {self.pharmacy.name} by {self.user.username}"

    @property
    def average_score(self):
        return (self.q1_score + self.q2_score + self.q3_score + self.q4_score + self.q5_score) / 5