import csv

from django.http import HttpResponse
from django.contrib import admin
from .models import MonolingualCorpus, UploadedFileIndex, UploadedFileInfo, TaggedWord, DropdownOption

admin.site.register(MonolingualCorpus)
admin.site.register(UploadedFileIndex)
admin.site.register(UploadedFileInfo)
admin.site.register(DropdownOption)


class TaggedWordAdmin(admin.ModelAdmin):
    list_display = ('proceed', 'word', 'tag', 'last_updated_time', 'sentence', 'user')
    actions = ['download_tags_csv_by_user']

    def download_tags_csv_by_user(self, request, queryset):
        users = queryset.values_list('user', flat=True).distinct()
        if len(users) != 1:
            self.message_user(request, "Please select tagged words from exactly one user.")
            return HttpResponse(status=400)  # Bad request

        user_id = users[0]
        tagged_words = TaggedWord.objects.filter(user_id=user_id).select_related('sentence')
        user = tagged_words.first().user

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{user.username}_tagged_words.csv"'
        writer = csv.writer(response)
        writer.writerow(['Words', 'Tags'])

        # Grouping words and tags by sentences
        sentence_dict = {}
        for tagged_word in tagged_words:
            sentence = tagged_word.sentence.content
            word = tagged_word.word
            tag = tagged_word.tag
            if sentence not in sentence_dict:
                sentence_dict[sentence] = {'words': [], 'tags': []}
            sentence_dict[sentence]['words'].append(word)
            sentence_dict[sentence]['tags'].append(tag)

        # Writing to CSV
        for sentence, data in sentence_dict.items():
            words = ', '.join(data['words'])
            tags = ', '.join(data['tags'])
            writer.writerow([words, tags])

        return response

    download_tags_csv_by_user.short_description = "Download tags by selected user"

admin.site.register(TaggedWord, TaggedWordAdmin)