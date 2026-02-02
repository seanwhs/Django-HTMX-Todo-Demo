# todo/models.py 
from django.db import models

class Todo(models.Model):
    title = models.CharField(max_length=255)
    is_done = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False) # for soft delete
    note = models.CharField(max_length=100, blank=True, db_index=True) # for bulk undelete
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title