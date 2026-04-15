
## Known Environment Limitations

### Appointments Module (test3.openmrs.org)
- **UI:** `esm-appointments` microfrontend not installed on test3 environment — page loads blank
- **API:** `appointmentscheduling` REST module not deployed on this server
- **Decision:** Appointment scheduling tests deferred pending environment with module installed (e.g., demo.openmrs.org or local Docker instance)
- **Logged:** 2026-04-15
