from django.db import models
from django.contrib.auth.models import BaseUserManager, User


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        if not username:
            raise ValueError("Users must have a username")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password):
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            password=password,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user  

class UploadedFileInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    uploaded_file_name = models.CharField(max_length=255, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.uploaded_file_name}"

class MonolingualCorpus(models.Model):
    username = models.CharField(max_length=150, null=True)
    uploaded_file_index = models.ForeignKey(UploadedFileInfo, on_delete=models.CASCADE, null=True)
    language = models.CharField(max_length=50, null=True)
    content = models.TextField(null=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.uploaded_file_index} - {self.id}"
    
class UploadedFileIndex(models.Model):
    uploaded_file_name = models.CharField(max_length=255)
    starting_id = models.IntegerField()
    ending_id = models.IntegerField()

    def __str__(self):
        return f"{self.uploaded_file_name}, {self.starting_id}, {self.ending_id}"

class TaggedWord(models.Model):
    proceed = models.BooleanField(default=False)
    word = models.CharField(max_length=100)
    tag = models.CharField(max_length=50)
    last_updated_time = models.DateTimeField(auto_now=True)
    sentence = models.ForeignKey(MonolingualCorpus, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True)

    def __str__(self):
        return f"{self.word} - {self.tag}"
    
class DropdownOption(models.Model):
    option_name = models.CharField(max_length=100)

    def __str__(self):
        return self.option_name
