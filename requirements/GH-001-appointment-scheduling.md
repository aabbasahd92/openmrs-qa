# Requirement: Appointment Scheduling — Patient-Facing Flow

## Source
Linked to project backlog item OMQ-014 (OpenMRS O3 Appointments module).

## Acceptance Criteria
1. A logged-in clinician can select a patient from search results.
2. The clinician can open the "Appointments" tab on the patient chart.
3. The clinician can create a new appointment by selecting a service, date, and time.
4. The system displays a confirmation after the appointment is saved.
5. The appointment appears in the patient's appointment list after creation.

## Out of Scope (explicitly not required)
- Payment collection for appointments
- SMS/email reminder configuration
- Multi-provider scheduling conflicts

## Known Environment Notes
- `esm-appointments` microfrontend is not installed on test3.openmrs.org (see this repo's
  README, "Known Environment Limitations"). This requirement targets an environment where the
  module IS installed — the planner must verify this via live exploration, not assume.
