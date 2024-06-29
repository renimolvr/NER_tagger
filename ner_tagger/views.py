import matplotlib.pyplot as plt

from django.conf import settings
from django.db.models import Max
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from collections import defaultdict

from .models import DropdownOption, MonolingualCorpus, UploadedFileIndex, UploadedFileInfo, TaggedWord
from .forms import CustomAuthenticationForm
from .helper import process_csv, process_text

plt.rcParams['font.family'] = 'Meera'

def user_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if user.is_staff:
                    return redirect('upload_csv')  
                else:
                    return redirect('view_uploaded_files')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    return redirect('user_login')

@login_required
def upload_csv(request):
    starting_id = None
    ending_id = None
    
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        file_type = file.name.split('.')[-1].lower()
        
        existing_upload = UploadedFileIndex.objects.filter(uploaded_file_name=file.name).first()
        if existing_upload:
            MonolingualCorpus.objects.filter(id__range=(existing_upload.starting_id, existing_upload.ending_id)).delete()
            UploadedFileIndex.objects.filter(uploaded_file_name=file.name).delete()
     
        if file_type == 'csv':
            starting_id = (MonolingualCorpus.objects.aggregate(Max('id'))['id__max'] or 0) + 1
            process_csv(file, request.user)
            ending_id = (MonolingualCorpus.objects.aggregate(Max('id'))['id__max'] or 0)
            uploaded_file_index = UploadedFileIndex.objects.create(uploaded_file_name = file.name, 
                                                                   starting_id = starting_id, 
                                                                   ending_id = ending_id)
            
        elif file_type == 'txt':
            starting_id = (MonolingualCorpus.objects.aggregate(Max('id'))['id__max'] or 0) + 1
            process_text(file, request.user)
            ending_id = (MonolingualCorpus.objects.aggregate(Max('id'))['id__max'] or 0)
            uploaded_file_index = UploadedFileIndex.objects.create(uploaded_file_name = file.name, 
                                                                   starting_id = starting_id,
                                                                   ending_id = ending_id)
            
        else:
            print("Unsupported file type")
            
        return render(request, 'success.html', {'uploaded_file_info': uploaded_file_index})

    return render(request, 'upload.html')

@login_required
def view_uploaded_files(request):
    uploaded_files = UploadedFileIndex.objects.all()
    return render(request, 'view_uploaded_files.html', {'uploaded_files': uploaded_files})

@login_required
def view_sentences(request, file_id):
    uploaded_file = get_object_or_404(UploadedFileInfo, id=file_id)
    corpus_entries = MonolingualCorpus.objects.filter(uploaded_file_index=uploaded_file)
    
    sentences = []
    for entry in corpus_entries:
        sentences.extend(entry.content.split('. '))

    sentence_index = int(request.GET.get('index', 0))
    
    dropdown_options = DropdownOption.objects.all()

    previous_tags = request.session.get(f'sentence_{sentence_index}_tags', {})

    if sentence_index < len(sentences):
        sentence = sentences[sentence_index]
        tokens = sentence.split()
        next_index = sentence_index + 1
    else:
        sentence = "No more sentences."
        tokens = []
        next_index = sentence_index

    if request.method == 'POST':
        if 'save' in request.POST:
            tags = {}
            for token in tokens:
                tag = request.POST.get(f'tag_{token}', 'Others')
                tags[token] = tag

                tagged_word, created = TaggedWord.objects.update_or_create(
                    word=token,
                    sentence=MonolingualCorpus.objects.filter(content__icontains=sentence).first(),
                    defaults={'tag': tag, 'user': request.user}
                )
            request.session[f'sentence_{sentence_index}_tags'] = tags
            return redirect(f"{request.path}?index={next_index}")

        elif 'next' in request.POST:
            return redirect(f"{request.path}?index={next_index}")

    context = {
        'file_name': uploaded_file.uploaded_file_name,
        'sentence': sentence,
        'tokens': tokens,
        'next_index': next_index,
        'file_id': file_id,
        'dropdown_options': dropdown_options,
        'previous_tags': previous_tags
    }
    return render(request, 'view_sentences.html', context)

def user_names_action(request):
    # Fetch all user names from the database
    user_names = User.objects.values_list('username', flat=True)
    
    # Render a template with the user names
    return render(request, 'user_names.html', {'user_names': user_names})

@login_required
def view_tags(request):
    dropdown_options = DropdownOption.objects.all()

    if request.method == 'POST':
        username = request.POST.get('username')
        user_tags = TaggedWord.objects.filter(user__username=username).order_by('sentence__id')
        
        # Group tags by sentence
        grouped_tags = defaultdict(list)
        for tag in user_tags:
            grouped_tags[tag.sentence.content].append(tag)
        
        # Handle tag updates
        for sentence, tags in grouped_tags.items():
            for tag in tags:
                new_tag = request.POST.get(f'tag_{tag.word}')
                if new_tag and new_tag != tag.tag:
                    tag.tag = new_tag
                    tag.save()
        
        context = {
            'username': username,
            'grouped_tags': dict(grouped_tags),
            'dropdown_options': dropdown_options,
        }
        
        return render(request, 'user_tags.html', context)
    
    elif request.method == 'GET':
        username = request.GET.get('username')
        user_tags = TaggedWord.objects.filter(user__username=username).order_by('sentence__id')
        
        # Group tags by sentence
        grouped_tags = defaultdict(list)
        for tag in user_tags:
            grouped_tags[tag.sentence.content].append(tag)
        
        context = {
            'username': username,
            'grouped_tags': dict(grouped_tags),
            'dropdown_options': dropdown_options,
        }
        
        return render(request, 'user_tags.html', context)
    
    return render(request, 'home.html')