document.addEventListener('DOMContentLoaded', function() {
    var messageForm = document.getElementById('messageForm');
    var scrollPosition = 0;

    // Store scroll position before form submission
    window.addEventListener('beforeunload', function() {
        scrollPosition = window.scrollY;
        localStorage.setItem('scrollPosition', scrollPosition);
    });

    // Restore scroll position after page reload
    window.addEventListener('load', function() {
        scrollPosition = localStorage.getItem('scrollPosition') || 0;
        window.scrollTo(0, scrollPosition);
    });

    messageForm.addEventListener('submit', function(event) {
        event.preventDefault(); // Prevent form submission
        
        // Submit the form via AJAX
        var xhr = new XMLHttpRequest();
        xhr.open('POST', messageForm.getAttribute('action'), true);
        xhr.onload = function() {
            if (xhr.status === 200) {
                // Clear input fields
                document.getElementById('sender').value = '';
                document.getElementById('content').value = '';

                // Scroll to the stored position
                window.scrollTo(0, scrollPosition);
            }
        };
        xhr.send(new FormData(messageForm));
    });
});
