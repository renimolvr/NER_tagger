import pandas as pd
import nltk

from nltk.tokenize import word_tokenize
from django.db import transaction
from django.utils import timezone
from django.conf import settings


from .models import MonolingualCorpus, UploadedFileInfo

nltk.download('punkt')

def process_csv(file: str, user, lang: str = 'ml', chunk_size: int = 1000):
    uploaded_file_info = UploadedFileInfo.objects.create(user = user, 
                                        uploaded_file_name = file.name, 
                                        last_updated = timezone.now())
    monolingual_corpus_list = []
    reader = pd.read_csv(file, chunksize=chunk_size)

    for chunk in reader:
        for index, row in chunk.iterrows():
            content = ','.join(map(str, row.tolist()))
            monolingual_corpus_list.append(
                MonolingualCorpus(
                    username = user.username,
                    uploaded_file_index = uploaded_file_info,
                    language = lang,
                    content = content.strip(),
                    last_updated = timezone.now()
                )
            )

    with transaction.atomic():
        MonolingualCorpus.objects.bulk_create(monolingual_corpus_list)


def process_text(file, user, lang: str = 'ml') -> None:
    uploaded_file_info = UploadedFileInfo.objects.create(user = user, 
                                        uploaded_file_name = file.name, 
                                        last_updated = timezone.now())
    content = file.read().decode('utf-8')
    lines = content.split('\n')
    monolingual_corpus_list = []

    for line in lines:
        monolingual_corpus_list.append(
            MonolingualCorpus(
                username=user.username,
                uploaded_file_index = uploaded_file_info,
                language=lang,
                content=content.strip(),
                last_updated=timezone.now()
            )
        )
        
    with transaction.atomic():
        MonolingualCorpus.objects.bulk_create(monolingual_corpus_list)
        