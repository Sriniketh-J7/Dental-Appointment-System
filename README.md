# Dental Appointment Management System

A conversational AI agent for managing dental clinic appointments, built with LangGraph and Grok-4 (xAI). I built this to explore multi-agent orchestration — instead of one LLM trying to handle every kind of request, a supervisor agent classifies user intent and routes the conversation to a specialized agent that only has the tools it actually needs.

## What it does

Patients or clinic staff can, through a normal chat interface:
- Check available appointment slots and doctor schedules
- Book a new appointment
- Cancel an existing appointment
- Reschedule an appointment to a different slot

## Architecture

A supervisor agent looks at each incoming message, classifies the intent, and hands off to the right specialist:

```
                    ┌──────────────┐
                    │   Supervisor │ ← Intent classification & routing
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
   ┌─────────────┐ ┌─────────────┐ ┌───────────────┐
   │ Info Agent  │ │   Booking   │ │  Cancellation │
   │             │ │    Agent    │ │    Agent      │
   └─────────────┘ └─────────────┘ └───────────────┘
          │
          ▼
   ┌───────────────┐
   │   Reschedule  │
   │    Agent      │
   └───────────────┘
```

**Supervisor** — reads the user's message, classifies intent (`get_info`, `book`, `cancel`, `reschedule`, `end`), and routes accordingly.
**Info Agent** — answers questions about slots, schedules, and a patient's existing appointments.
**Booking Agent** — collects the details needed for a booking and creates it.
**Cancellation Agent** — cancels an existing appointment.
**Rescheduling Agent** — moves an appointment to a new slot.

Each agent only gets the tools relevant to its job — the Info Agent can look things up but can't book anything, for example. That separation is the main design decision I wanted to get right: it keeps each agent's prompt focused and makes the whole system easier to reason about than one agent juggling every tool at once.

### Stack

- **LangGraph** — orchestrates the agent workflow and shared state
- **LangChain** — LLM integration and tool-calling framework
- **Grok-4 (xAI)** — the underlying model
- **Pandas** — CSV-based data storage for this demo
- **Pydantic** — structured output validation (used for the supervisor's routing decision)

## Project structure

```
dental_agent_project/
├── main.py                          # CLI entry point
├── doctor_availability.csv          # Sample data store for appointments
├── requirements.txt
├── dental_agent/
│   ├── agent.py                     # Agent definition & tool registration
│   ├── config/
│   │   └── settings.py              # Config & environment loading
│   ├── models/
│   │   └── state.py                 # Shared state schema
│   ├── tools/
│   │   ├── csv_reader.py            # Read-only query tools
│   │   └── csv_writer.py            # Mutation tools (book/cancel/reschedule)
│   ├── agents/
│   │   ├── supervisor.py
│   │   ├── info_agent.py
│   │   ├── booking_agent.py
│   │   ├── cancellation_agent.py
│   │   └── rescheduling_agent.py
│   └── workflows/
│       └── graph.py                 # LangGraph graph definition
```

## Setup

### Requirements

- Python 3.10+
- An xAI API key (for Grok-4)

### Steps

1. Clone the repo and move into the project directory:
   ```bash
   git clone <your-repo-url>
   cd dental_agent_project
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and add your key:
   ```
   XAI_API_KEY=your_api_key_here
   MODEL_NAME=grok-4
   TEMPERATURE=0
   ```
   Get a key from the [xAI Console](https://console.x.ai/).

## Usage

```bash
python main.py
```

### Example interactions

**Checking available slots:**
```
You: Show available slots for an orthodontist
Agent: Here are the available orthodontist appointments:
1. 5/10/2026 9:00 - Dr. Emily Johnson
2. 5/10/2026 10:00 - Dr. Emily Johnson
3. 5/12/2026 14:00 - Dr. Emily Johnson
...
```

**Booking:**
```
You: Book patient 1000082 with Emily Johnson on 5/10/2026 9:00
Agent: Let me check that slot first... The slot is available!
I've booked the appointment:
- Patient ID: 1000082
- Doctor: Emily Johnson
- Date/Time: 5/10/2026 9:00
- Specialization: orthodontist
```

**Checking a patient's appointments:**
```
You: What appointments does patient 1000048 have?
Agent: Patient 1000048 has the following appointments:
1. 5/8/2026 9:00 - Dr. John Doe (general_dentist)
```

**Cancelling:**
```
You: Cancel appointment for patient 1000082 at 5/10/2026 9:00
Agent: I've cancelled the appointment for patient 1000082 on 5/10/2026 at 9:00.
```

**Rescheduling:**
```
You: Reschedule patient 1000082 from 5/10/2026 9:00 to 5/12/2026 10:00
Agent: Let me verify the new slot is available... It's available!
I've rescheduled the appointment:
- Patient ID: 1000082
- New Date/Time: 5/12/2026 10:00
- Doctor: Emily Johnson
```

## Specializations supported

General Dentist, Oral Surgeon, Orthodontist, Cosmetic Dentist, Prosthodontist, Pediatric Dentist, Emergency Dentist.

## Data model

Appointment data lives in `doctor_availability.csv` (a stand-in for a real database in this demo):

| Field | Description |
|-------|-------------|
| date_slot | Appointment date and time (M/D/YYYY H:MM) |
| specialization | Type of dental specialist |
| doctor_name | Name of the dentist |
| is_available | Whether the slot is open |
| patient_to_attend | Patient ID if booked, blank if available |

## Notes on the design

A few things I paid attention to while building this:

- **Intent classification is structured, not free text.** The supervisor returns a JSON object (`intent`, `next_agent`, `reasoning`) via Pydantic, rather than parsing free-form text — this makes routing deterministic and easy to debug.
- **Tool access is scoped per agent** (principle of least privilege) — an agent can only call the tools it needs for its job.
- **State is shared across the graph** — message history, the current routing decision, and any parameters collected mid-conversation (patient ID, doctor, date) persist across agent handoffs.
- **The data layer is abstracted** behind `csv_reader` / `csv_writer` — swapping the CSV for a real database wouldn't require touching the agent logic.

## License

Educational / portfolio project.
