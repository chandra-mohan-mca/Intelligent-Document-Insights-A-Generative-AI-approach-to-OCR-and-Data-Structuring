
document.addEventListener('DOMContentLoaded', () => {
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('fileInput');
    const previewContainer = document.getElementById('preview-container');
    const previewImage = document.getElementById('preview-image');
    const fileInfo = document.getElementById('file-info');
    const convertBtn = document.getElementById('convertBtn');
    const saveBtn = document.getElementById('saveBtn');
    const transcriptionText = document.getElementById('transcription');
    const loadingIcon = document.querySelector('.loading');

    // Drag and Drop Events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        dropArea.classList.add('dragover');
    }

    function unhighlight() {
        dropArea.classList.remove('dragover');
    }

    dropArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    // Click to upload
    dropArea.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', function () {
        handleFiles(this.files);
    });

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];

            // Validate file type
            if (!['image/jpeg', 'image/png', 'application/pdf'].includes(file.type)) {
                alert('Only JPG, PNG, and PDF files are allowed.');
                return;
            }

            fileInfo.textContent = `Selected: ${file.name}`;
            fileInfo.style.display = 'block';
            convertBtn.disabled = false;

            // Preview if image
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    previewImage.src = e.target.result;
                    previewContainer.style.display = 'block';
                }
                reader.readAsDataURL(file);
            } else {
                previewContainer.style.display = 'none';
            }
        }
    }

    // Convert Button Click
    convertBtn.addEventListener('click', async () => {
        const file = fileInput.files[0];
        if (!file) return;

        setLoading(true);
        transcriptionText.value = "Processing... This uses Gemini AI and may take a few seconds.";

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Upload failed');
            }

            const data = await response.json();
            transcriptionText.value = data.text;
        } catch (error) {
            console.error('Error:', error);
            transcriptionText.value = `Error: ${error.message}`;
            alert(`Error: ${error.message}`);
        } finally {
            setLoading(false);
        }
    });

    function setLoading(isLoading) {
        convertBtn.disabled = isLoading;
        if (isLoading) {
            loadingIcon.classList.add('active');
            convertBtn.querySelector('span').textContent = 'Converting...';
        } else {
            loadingIcon.classList.remove('active');
            convertBtn.querySelector('span').textContent = 'Convert to Text';
        }
    }

    // Save to Word Button Click
    saveBtn.addEventListener('click', async () => {
        const text = transcriptionText.value;
        if (!text) {
            alert('No text to save!');
            return;
        }

        const formData = new FormData();
        formData.append('text', text);

        try {
            const response = await fetch('/download-docx', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Download failed');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'transcription.docx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to save document.');
        }
    });
});
