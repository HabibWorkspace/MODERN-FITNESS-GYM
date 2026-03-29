# Requirements Document

## Introduction

This document specifies the requirements for integrating a biometric attendance system into an existing Flask-based Gym Management System. The system will connect to a ZKTeco iFace900 biometric device to automatically track member and trainer check-ins and check-outs, provide real-time notifications to administrators, and generate attendance analytics.

## Glossary

- **Biometric_Device**: The ZKTeco iFace900 hardware device connected to the local network that captures attendance scans
- **Attendance_Service**: The backend service module that communicates with the Biometric_Device using the pyzk library
- **Attendance_Record**: A database entry representing a single check-in or check-out event
- **Device_User_ID**: The unique identifier assigned to a person in the Biometric_Device
- **Person**: Either a Member or Trainer in the gym system
- **Check_In**: The first scan event that marks entry into the gym
- **Check_Out**: The second scan event that marks exit from the gym
- **Stay_Duration**: The calculated time difference between Check_Out and Check_In
- **Admin_Dashboard**: The web interface used by administrators to view attendance data
- **Notification_System**: The real-time communication mechanism (WebSocket or SSE) for instant updates
- **Sync_Operation**: The periodic process of fetching new attendance logs from the Biometric_Device

## Requirements

### Requirement 1: Device Connection and Communication

**User Story:** As a system administrator, I want the system to connect to the biometric device, so that attendance data can be retrieved automatically.

#### Acceptance Criteria

1. THE Attendance_Service SHALL connect to the Biometric_Device at IP address 192.168.0.201 on port 4370
2. THE Attendance_Service SHALL use the pyzk library for device communication
3. WHEN the connection fails, THE Attendance_Service SHALL log the error with timestamp and device details
4. THE Attendance_Service SHALL verify device connectivity before attempting to fetch attendance logs
5. WHEN the device is unreachable, THE Attendance_Service SHALL retry connection after 60 seconds

### Requirement 2: Attendance Log Synchronization

**User Story:** As a system administrator, I want attendance logs to be automatically synchronized from the device, so that attendance data is always current.

#### Acceptance Criteria

1. THE Attendance_Service SHALL fetch attendance logs from the Biometric_Device every 30 to 60 seconds
2. WHEN new attendance logs are retrieved, THE Attendance_Service SHALL process each log entry sequentially
3. THE Attendance_Service SHALL extract Device_User_ID, timestamp, and device serial number from each log entry
4. WHEN a Sync_Operation completes successfully, THE Attendance_Service SHALL log the number of records processed
5. WHEN a Sync_Operation fails, THE Attendance_Service SHALL log the error and continue with the next scheduled sync

### Requirement 3: Person Identification and Mapping

**User Story:** As a system administrator, I want device user IDs to be mapped to members or trainers, so that attendance records are linked to the correct people.

#### Acceptance Criteria

1. WHEN processing an attendance log, THE Attendance_Service SHALL map the Device_User_ID to either a Member or Trainer
2. THE Attendance_Service SHALL store the person type (member or trainer) in the Attendance_Record
3. THE Attendance_Service SHALL store the person ID (member_id or trainer_id) in the Attendance_Record
4. WHEN a Device_User_ID cannot be mapped to any Person, THE Attendance_Service SHALL log an unmapped entry warning with the Device_User_ID
5. THE Attendance_Service SHALL support a mapping configuration that associates Device_User_ID with Person records

### Requirement 4: Check-In and Check-Out Logic

**User Story:** As a gym member or trainer, I want my first scan to check me in and my second scan to check me out, so that my gym visit is tracked accurately.

#### Acceptance Criteria

1. WHEN a Person scans the Biometric_Device for the first time on a given day, THE Attendance_Service SHALL create a new Attendance_Record with Check_In time
2. WHEN a Person scans the Biometric_Device a second time on the same day, THE Attendance_Service SHALL update the existing Attendance_Record with Check_Out time
3. THE Attendance_Service SHALL calculate Stay_Duration as the difference between Check_Out time and Check_In time
4. THE Attendance_Service SHALL store Stay_Duration in minutes in the Attendance_Record
5. WHEN a Person scans more than twice in a day, THE Attendance_Service SHALL treat the third scan as a new Check_In for a separate visit

### Requirement 5: Duplicate Entry Prevention

**User Story:** As a system administrator, I want duplicate attendance entries to be prevented, so that attendance data remains accurate.

#### Acceptance Criteria

1. WHEN processing an attendance log entry, THE Attendance_Service SHALL check if an identical record already exists
2. THE Attendance_Service SHALL consider records identical when Device_User_ID, timestamp, and device serial match
3. WHEN a duplicate entry is detected, THE Attendance_Service SHALL skip insertion and log a duplicate warning
4. THE Attendance_Service SHALL allow multiple check-ins for the same Person on different days
5. THE Attendance_Service SHALL allow multiple check-ins for the same Person on the same day if separated by a Check_Out

### Requirement 6: Attendance Database Schema

**User Story:** As a developer, I want a well-structured attendance table, so that attendance data can be stored and queried efficiently.

#### Acceptance Criteria

1. THE Attendance_Record SHALL include fields: id, device_user_id, person_type, person_id, check_in_time, check_out_time, stay_duration, device_serial, created_at
2. THE Attendance_Record SHALL use a UUID for the id field
3. THE Attendance_Record SHALL store person_type as either "member" or "trainer"
4. THE Attendance_Record SHALL allow check_out_time to be null when only Check_In has occurred
5. THE Attendance_Record SHALL store timestamps in UTC format
6. THE Attendance_Record SHALL index device_user_id, person_id, and check_in_time for query performance

### Requirement 7: Real-Time Admin Notifications

**User Story:** As an administrator, I want to receive instant notifications when someone checks in or out, so that I can monitor gym activity in real-time.

#### Acceptance Criteria

1. WHEN a Person completes a Check_In, THE Notification_System SHALL send a notification to connected administrators
2. WHEN a Person completes a Check_Out, THE Notification_System SHALL send a notification to connected administrators
3. THE Notification_System SHALL include the Person's name, person type, and Check_In time in Check_In notifications
4. THE Notification_System SHALL include the Person's name, person type, Check_In time, and Stay_Duration in Check_Out notifications
5. THE Notification_System SHALL use WebSocket or Server-Sent Events for real-time delivery
6. THE Notification_System SHALL deliver notifications within 2 seconds of the attendance event

### Requirement 8: Attendance Dashboard Summary Cards

**User Story:** As an administrator, I want to see summary statistics on the dashboard, so that I can quickly understand current gym activity.

#### Acceptance Criteria

1. THE Admin_Dashboard SHALL display the total number of check-ins for the current day
2. THE Admin_Dashboard SHALL display the count of Members currently inside the gym
3. THE Admin_Dashboard SHALL display the count of Trainers currently inside the gym
4. THE Admin_Dashboard SHALL display the average Stay_Duration for the current day
5. THE Admin_Dashboard SHALL update summary cards automatically when new attendance events occur
6. WHEN calculating "currently inside", THE Admin_Dashboard SHALL count Attendance_Records with Check_In but no Check_Out

### Requirement 9: Live Activity Feed

**User Story:** As an administrator, I want to see a live feed of recent attendance activity, so that I can monitor who is entering and leaving the gym.

#### Acceptance Criteria

1. THE Admin_Dashboard SHALL display a live activity feed showing recent attendance events
2. THE Admin_Dashboard SHALL show Person name, person type, Check_In time, and status (Inside or Checked Out) for each entry
3. THE Admin_Dashboard SHALL display the most recent 20 attendance events in the feed
4. THE Admin_Dashboard SHALL automatically add new events to the top of the feed when they occur
5. THE Admin_Dashboard SHALL update the status from "Inside" to "Checked Out" when a Check_Out occurs

### Requirement 10: Attendance History Table

**User Story:** As an administrator, I want to view detailed attendance history with search and filters, so that I can analyze attendance patterns.

#### Acceptance Criteria

1. THE Admin_Dashboard SHALL display an attendance table with columns: Name, Role, Check_In, Check_Out, Total Time Stayed, Device
2. THE Admin_Dashboard SHALL support searching by Person name
3. THE Admin_Dashboard SHALL support filtering by person type (Member or Trainer)
4. THE Admin_Dashboard SHALL support filtering by date range
5. THE Admin_Dashboard SHALL support pagination with configurable page size
6. THE Admin_Dashboard SHALL sort attendance records by Check_In time in descending order by default
7. THE Admin_Dashboard SHALL display Stay_Duration in hours and minutes format

### Requirement 11: Currently Inside Gym Widget

**User Story:** As an administrator, I want to see who is currently inside the gym, so that I can monitor current occupancy.

#### Acceptance Criteria

1. THE Admin_Dashboard SHALL display a widget listing all Persons currently inside the gym
2. THE Admin_Dashboard SHALL show Person name, Check_In time, and time spent so far for each entry
3. THE Admin_Dashboard SHALL update the time spent automatically every minute
4. THE Admin_Dashboard SHALL remove a Person from the widget when they Check_Out
5. THE Admin_Dashboard SHALL group the widget by person type (Members and Trainers)

### Requirement 12: Weekly Attendance Analytics

**User Story:** As an administrator, I want to see weekly attendance trends, so that I can identify busy and slow periods.

#### Acceptance Criteria

1. THE Admin_Dashboard SHALL display a chart showing total check-ins for each day of the current week
2. THE Admin_Dashboard SHALL group check-ins by day (Monday through Sunday)
3. THE Admin_Dashboard SHALL use a bar chart or line chart visualization
4. THE Admin_Dashboard SHALL allow navigation to previous and next weeks
5. THE Admin_Dashboard SHALL display the week date range in the chart title

### Requirement 13: Monthly Attendance Analytics

**User Story:** As an administrator, I want to see monthly attendance trends, so that I can analyze long-term patterns.

#### Acceptance Criteria

1. THE Admin_Dashboard SHALL display a chart showing total check-ins for each day of the current month
2. THE Admin_Dashboard SHALL group check-ins by date
3. THE Admin_Dashboard SHALL use a line chart or area chart visualization
4. THE Admin_Dashboard SHALL allow navigation to previous and next months
5. THE Admin_Dashboard SHALL display the month and year in the chart title

### Requirement 14: Member Visit Frequency Analytics

**User Story:** As an administrator, I want to see which members visit most frequently, so that I can identify engaged members.

#### Acceptance Criteria

1. THE Admin_Dashboard SHALL display a list of the top 10 Members by visit count
2. THE Admin_Dashboard SHALL show Member name and total visit count for the current month
3. THE Admin_Dashboard SHALL sort Members by visit count in descending order
4. THE Admin_Dashboard SHALL count each Check_In as one visit
5. THE Admin_Dashboard SHALL exclude Trainers from this analytics view

### Requirement 15: Average Stay Time Analytics

**User Story:** As an administrator, I want to see average gym stay times, so that I can understand usage patterns.

#### Acceptance Criteria

1. THE Admin_Dashboard SHALL display the average Stay_Duration for the current day
2. THE Admin_Dashboard SHALL display the average Stay_Duration for the current week
3. THE Admin_Dashboard SHALL display the average Stay_Duration for the current month
4. THE Admin_Dashboard SHALL calculate averages only from completed visits (with Check_Out)
5. THE Admin_Dashboard SHALL display Stay_Duration in hours and minutes format

### Requirement 16: Attendance API Endpoints

**User Story:** As a frontend developer, I want RESTful API endpoints for attendance data, so that I can build the dashboard interface.

#### Acceptance Criteria

1. THE Attendance_Service SHALL provide a GET /api/attendance/sync endpoint to trigger manual synchronization
2. THE Attendance_Service SHALL provide a GET /api/attendance/today endpoint returning today's attendance records
3. THE Attendance_Service SHALL provide a GET /api/attendance/weekly endpoint returning current week's attendance summary
4. THE Attendance_Service SHALL provide a GET /api/attendance/monthly endpoint returning current month's attendance summary
5. THE Attendance_Service SHALL provide a GET /api/attendance/live endpoint returning currently checked-in Persons
6. THE Attendance_Service SHALL return JSON responses with appropriate HTTP status codes
7. THE Attendance_Service SHALL require authentication for all attendance endpoints

### Requirement 17: Dashboard UI Design and Responsiveness

**User Story:** As an administrator, I want a modern and responsive dashboard, so that I can access attendance data from any device.

#### Acceptance Criteria

1. THE Admin_Dashboard SHALL use a card-based layout for summary metrics
2. THE Admin_Dashboard SHALL be responsive and functional on desktop, tablet, and mobile devices
3. THE Admin_Dashboard SHALL use a modern fitness/gym SaaS design aesthetic
4. THE Admin_Dashboard SHALL display smooth animations for real-time updates
5. THE Admin_Dashboard SHALL use a consistent color scheme matching the existing gym management system
6. THE Admin_Dashboard SHALL load all initial data within 2 seconds on a standard broadband connection

### Requirement 18: Notification Popup Display

**User Story:** As an administrator, I want notification popups to be visually clear and non-intrusive, so that I stay informed without disruption.

#### Acceptance Criteria

1. WHEN a notification is received, THE Admin_Dashboard SHALL display a popup in the top-right corner
2. THE Admin_Dashboard SHALL show Person name, person type, and event type (Check-In or Check-Out) in the popup
3. THE Admin_Dashboard SHALL automatically dismiss the popup after 5 seconds
4. THE Admin_Dashboard SHALL allow manual dismissal of the popup by clicking a close button
5. THE Admin_Dashboard SHALL stack multiple popups vertically when multiple notifications arrive
6. THE Admin_Dashboard SHALL limit the maximum number of visible popups to 3

### Requirement 19: Background Service Execution

**User Story:** As a system administrator, I want the attendance sync service to run continuously in the background, so that attendance data is always up-to-date.

#### Acceptance Criteria

1. THE Attendance_Service SHALL run as a background process independent of web requests
2. THE Attendance_Service SHALL continue running even when no administrators are logged in
3. THE Attendance_Service SHALL restart automatically if it crashes or stops unexpectedly
4. THE Attendance_Service SHALL log its start time and status on initialization
5. THE Attendance_Service SHALL gracefully handle application shutdown and cleanup resources

### Requirement 20: Error Handling and Logging

**User Story:** As a system administrator, I want comprehensive error logging, so that I can troubleshoot issues quickly.

#### Acceptance Criteria

1. WHEN any error occurs in the Attendance_Service, THE system SHALL log the error with timestamp, error type, and stack trace
2. THE Attendance_Service SHALL log successful Sync_Operations with record counts
3. THE Attendance_Service SHALL log device connection status changes
4. THE Attendance_Service SHALL log unmapped Device_User_IDs with details
5. THE Attendance_Service SHALL write logs to a dedicated attendance log file
6. THE Attendance_Service SHALL rotate log files when they exceed 10MB in size
