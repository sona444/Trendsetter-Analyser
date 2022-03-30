import app

def upload(request):
    if request.method == 'GET':
        f = FileUpload()

    elif request.method == 'POST':
        import ipdb;
        ipdb.set_trace()
        f = FileUpload(request.POST, request.FILES)
        if f.is_valid():
            uploaded_file = f.cleaned_data['file_object']
            # manipulate file here.

    return render(request, 'upload.html', {'form': f})