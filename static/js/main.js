// Initialize tooltips and popovers
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Face recognition camera script
function initCamera() {
    const video = document.getElementById('video-element');
    const startButton = document.getElementById('start-camera');
    const stopButton = document.getElementById('stop-camera');
    const captureButton = document.getElementById('capture-image');
    const statusElement = document.getElementById('camera-status');
    
    if (!video || !startButton || !stopButton) return;
    
    let stream = null;
    
    // Start camera
    startButton.addEventListener('click', async () => {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: "user" }, 
                audio: false 
            });
            video.srcObject = stream;
            startButton.classList.add('d-none');
            stopButton.classList.remove('d-none');
            if (statusElement) {
                statusElement.textContent = 'Camera active. Face detection running...';
                statusElement.classList.remove('text-danger');
                statusElement.classList.add('text-success');
            }
        } catch (err) {
            console.error('Error accessing camera:', err);
            if (statusElement) {
                statusElement.textContent = 'Error accessing camera. Please check permissions.';
                statusElement.classList.add('text-danger');
            }
        }
    });
    
    // Stop camera
    stopButton.addEventListener('click', () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            video.srcObject = null;
            startButton.classList.remove('d-none');
            stopButton.classList.add('d-none');
            if (statusElement) {
                statusElement.textContent = 'Camera stopped';
                statusElement.classList.remove('text-success');
            }
        }
    });
    
    // Capture image (if capture button exists)
    if (captureButton) {
        captureButton.addEventListener('click', () => {
            if (stream) {
                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                canvas.getContext('2d').drawImage(video, 0, 0);
                
                // Convert to data URL
                const imageData = canvas.toDataURL('image/png');
                
                // Create hidden input and set value
                let input = document.getElementById('captured-image');
                if (!input) {
                    input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = 'captured_image';
                    input.id = 'captured-image';
                    document.getElementById('camera-form').appendChild(input);
                }
                input.value = imageData;
                
                if (statusElement) {
                    statusElement.textContent = 'Image captured! You can now submit.';
                }
            }
        });
    }
}

// Initialize chart.js for attendance analytics
function initCharts() {
    // Status distribution chart
    const statusChartElement = document.getElementById('status-chart');
    if (statusChartElement && typeof statusData !== 'undefined') {
        new Chart(statusChartElement, {
            type: 'pie',
            data: {
                labels: statusData.map(item => item.status),
                datasets: [{
                    data: statusData.map(item => item.count),
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.7)',  // Present - green
                        'rgba(255, 193, 7, 0.7)',  // Late - yellow
                        'rgba(220, 53, 69, 0.7)'   // Absent - red
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    // Course attendance rate chart
    const courseChartElement = document.getElementById('course-chart');
    if (courseChartElement && typeof courseData !== 'undefined') {
        new Chart(courseChartElement, {
            type: 'bar',
            data: {
                labels: courseData.map(item => item.course),
                datasets: [{
                    label: 'Attendance Rate (%)',
                    data: courseData.map(item => item.rate),
                    backgroundColor: 'rgba(13, 110, 253, 0.7)',
                    borderColor: 'rgba(13, 110, 253, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }
    
    // Monthly attendance trend chart
    const monthChartElement = document.getElementById('month-chart');
    if (monthChartElement && typeof monthData !== 'undefined') {
        new Chart(monthChartElement, {
            type: 'line',
            data: {
                labels: monthData.map(item => item.month),
                datasets: [{
                    label: 'Attendance Rate (%)',
                    data: monthData.map(item => item.rate),
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    borderColor: 'rgba(13, 110, 253, 1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }
}

// Call initialization functions
document.addEventListener('DOMContentLoaded', function() {
    initCamera();
    initCharts();
});