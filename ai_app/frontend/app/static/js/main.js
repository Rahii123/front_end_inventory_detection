// Dropdown toggle functionality
function toggleDropdown(dropdownId) {
    const content = document.getElementById(dropdownId);
    const button = event.currentTarget;
    
    if (content.classList.contains('active')) {
        content.classList.remove('active');
        button.innerHTML = button.innerHTML.replace('▲', '▼');
    } else {
        content.classList.add('active');
        button.innerHTML = button.innerHTML.replace('▼', '▲');
    }
}

// Clear prediction result
function clearPredictionResult() {
    // Hide result container
    const resultContainer = document.querySelector('.result-container');
    if (resultContainer) {
        resultContainer.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => {
            resultContainer.remove();
        }, 300);
    }
    
    // Reset file input
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
        fileInput.value = '';
    }
    
    // Reset preview
    const preview = document.getElementById('preview');
    const uploadContent = document.getElementById('upload-content');
    if (preview && uploadContent) {
        preview.style.display = 'none';
        preview.src = '';
        uploadContent.style.display = 'block';
    }
    
    // Scroll to top of form
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Add fadeOut animation
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from {
            opacity: 1;
            transform: translateY(0);
        }
        to {
            opacity: 0;
            transform: translateY(-20px);
        }
    }
`;
document.head.appendChild(style);

// Image preview function (for predict page)
function previewImage(input) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.onload = function (e) {
            document.getElementById('upload-content').style.display = 'none';
            var preview = document.getElementById('preview');
            preview.src = e.target.result;
            preview.style.display = 'block';
        }
        reader.readAsDataURL(input.files[0]);
    }
}

// Smooth scroll for navigation
document.addEventListener('DOMContentLoaded', function() {
    // Add smooth transitions to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animation = `fadeIn 0.5s ease ${index * 0.1}s both`;
    });
});
