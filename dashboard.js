let map;
const activityList = document.getElementById('activity-list');
const grabJobButton = document.getElementById('grab-job');
const submitBidButton = document.getElementById('submit-bid');

function initMap(lat = 40.7128, lon = -74.0060) {
    map = L.map('map').setView([lat, lon], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
}

function addActivity(activity) {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] ${activity.service} at (${activity.lat.toFixed(4)}, ${activity.lon.toFixed(4)})\n`;
    activityList.textContent += logEntry;
    activityList.scrollTop = activityList.scrollHeight;

    L.marker([activity.lat, activity.lon]).addTo(map)
        .bindPopup(activity.service)
        .openPopup();
}

function fetchActivities() {
    setTimeout(() => {
        const activities = [
            { service: 'Cleaning', lat: 40.7128, lon: -74.0060 },
            { service: 'Delivery', lat: 40.7300, lon: -73.9950 },
            { service: 'Security', lat: 40.7200, lon: -74.0100 }
        ];
        activities.forEach(addActivity);
    }, 1000);
}

function simulateGrabJob() {
    const services = ['Cleaning', 'Delivery', 'Security', 'Maintenance'];
    const activity = {
        service: services[Math.floor(Math.random() * services.length)],
        lat: map.getCenter().lat + (Math.random() - 0.5) * 0.1,
        lon: map.getCenter().lng + (Math.random() - 0.5) * 0.1
    };
    addActivity(activity);
}

function simulateSubmitBid() {
    const services = ['Lawn Mowing', 'Pet Sitting', 'Home Repair', 'Painting'];
    const activity = {
        service: services[Math.floor(Math.random() * services.length)],
        lat: map.getCenter().lat + (Math.random() - 0.5) * 0.1,
        lon: map.getCenter().lng + (Math.random() - 0.5) * 0.1
    };
    addActivity(activity);
}

function getUserLocation() {
    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(
            position => {
                const { latitude, longitude } = position.coords;
                map.setView([latitude, longitude], 13);
                addActivity({ service: "Your Location", lat: latitude, lon: longitude });
            },
            error => {
                console.error("Error getting user location:", error.message);
                initMap(); // Fall back to default location
            }
        );
    } else {
        console.log("Geolocation is not available in this browser.");
        initMap(); // Fall back to default location
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initMap(); // Initialize with default location
    getUserLocation(); // Try to get user's location
    fetchActivities();

    grabJobButton.addEventListener('click', simulateGrabJob);
    submitBidButton.addEventListener('click', simulateSubmitBid);
});