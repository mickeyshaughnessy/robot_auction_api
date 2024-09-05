let map;
const activityList = document.getElementById('activity-list');

function initMap(lat, lon) {
    map = L.map('map').setView([lat, lon], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
}

function addActivity(activity) {
    const li = document.createElement('li');
    li.textContent = `${activity.service} at (${activity.lat.toFixed(4)}, ${activity.lon.toFixed(4)})`;
    activityList.prepend(li);
    L.marker([activity.lat, activity.lon]).addTo(map)
        .bindPopup(activity.service)
        .openPopup();
}

async function fetchActivities(lat, lon) {
    try {
        const response = await fetch('http://localhost:5001/nearby', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + localStorage.getItem('access_token')
            },
            body: JSON.stringify({ lat, lon })
        });
        if (!response.ok) throw new Error('Failed to fetch activities');
        const activities = await response.json();
        activities.forEach(addActivity);
    } catch (error) {
        console.error('Error fetching activities:', error);
    }
}

function getRandomLocation() {
    return [
        40.7128 + (Math.random() - 0.5) * 0.1,
        -74.0060 + (Math.random() - 0.5) * 0.1
    ];
}

document.addEventListener('DOMContentLoaded', () => {
    if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(
            position => {
                const { latitude, longitude } = position.coords;
                initMap(latitude, longitude);
                fetchActivities(latitude, longitude);
            },
            error => {
                console.warn('Geolocation error:', error);
                const [lat, lon] = getRandomLocation();
                initMap(lat, lon);
                fetchActivities(lat, lon);
            }
        );
    } else {
        const [lat, lon] = getRandomLocation();
        initMap(lat, lon);
        fetchActivities(lat, lon);
    }
});