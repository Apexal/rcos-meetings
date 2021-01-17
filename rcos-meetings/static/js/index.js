const meetingColors = {
  'large_group': '#da291c',
  'small_group': 'green',
  'presentations': 'orange',
  'bonus_session': 'gold',
  'grading': 'red',
  // 'mentors': ''
  'coordinators': 'purple'
  // 'other'
};

function meetingToEvent(meeting, index) {
  return {
    title: (meeting.title || 'Meeting'),
    start: meeting.start_date_time + 'Z',
    end: meeting.end_date_time + 'Z',
    backgroundColor: meetingColors[meeting.meeting_type],
    url: '/meetings/' + meeting.meeting_id,
    meeting
  }
}

const API_BASE = 'http://198.211.105.73:3000'

document.addEventListener('DOMContentLoaded', function () {
  const calendarEl = document.getElementById('calendar');
  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    timeZone: 'America/New_York',
    weekends: false,
    events: function (info, successCallback, failureCallback) {
      fetch(API_BASE + '/public_meetings')
        .then(res => res.json())
        .then(meetings => successCallback(meetings.map(meetingToEvent)))
        .catch(failureCallback)
    }
  });
  calendar.render();
});