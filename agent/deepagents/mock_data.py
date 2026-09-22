"""
Mock data for the patient call analysis demo.

Contains a realistic multi-turn call transcript between a patient and
a pharmaceutical support agent, along with pre-computed analysis data
for the sandbox sentiment computation.
"""

MOCK_TRANSCRIPT = """
[00:00:05] AGENT: Thank you for calling Patient Support Services, my name is Sarah. How can I help you today?

[00:00:12] PATIENT: Hi Sarah, my name is Margaret Chen. I'm calling about the medication I was enrolled in through the patient assistance program. My date of birth is March 15, 1958, and my member ID is PAT-20241087.

[00:00:28] AGENT: Thank you, Margaret. Let me pull up your account. Can you confirm the phone number we have on file?

[00:00:35] PATIENT: Yes, it's 555-867-5309.

[00:00:40] AGENT: Perfect, I've verified your identity. I can see you're enrolled in the CardioAssist program for Vasculin 40mg. How can I help you today?

[00:00:52] PATIENT: Well, I've been taking Vasculin for about three weeks now, and I've been having some problems. I'm getting really bad headaches, almost every day. And sometimes I feel dizzy when I stand up, like the room is spinning.

[00:01:10] AGENT: I'm sorry to hear that, Margaret. I want to make sure I understand — you're experiencing daily headaches and dizziness upon standing. When did these symptoms first start?

[00:01:22] PATIENT: About a week after I started taking the medication. At first I thought it was just stress, but it's been getting worse. Yesterday I almost fell in the kitchen because the dizziness was so bad.

[00:01:38] AGENT: That sounds concerning. I need to document this as a potential adverse event. Can you tell me — are you taking any other medications alongside Vasculin?

[00:01:50] PATIENT: Yes, I take lisinopril for my blood pressure, and I also take a baby aspirin every day. My doctor, Dr. Raymond Park at Cedar Valley Medical, prescribed the Vasculin.

[00:02:05] AGENT: Thank you for that information. I want to make sure you're safe. Have you contacted Dr. Park about these symptoms?

[00:02:14] PATIENT: No, I wasn't sure if I should. I thought maybe this was normal when starting a new medication.

[00:02:22] AGENT: I understand, and I appreciate you calling us. I would strongly recommend contacting Dr. Park as soon as possible about the dizziness, especially since you mentioned nearly falling. In the meantime, I'm going to file an adverse event report for the headaches and dizziness. This is standard procedure to ensure patient safety.

[00:02:45] PATIENT: Oh, that sounds serious. Is there something wrong with the medication?

[00:02:52] AGENT: I want to reassure you — filing an adverse event report is a standard safety procedure. It doesn't necessarily mean there's something wrong with the medication. It helps us track and monitor any symptoms patients experience. Your safety is our top priority.

[00:03:10] PATIENT: Okay, I understand. Thank you for explaining that.

[00:03:15] AGENT: Of course. Now, I also want to ask about your enrollment. Your records show your next shipment is scheduled for next week. Would you like to continue with the shipment, or would you prefer to wait until you've spoken with Dr. Park?

[00:03:32] PATIENT: I think I'd like to wait until I talk to my doctor. Can you hold the shipment?

[00:03:38] AGENT: Absolutely, I'll place a hold on the next shipment. You can call us back anytime to resume. Is there anything else I can help you with?

[00:03:48] PATIENT: Actually, yes. I had a question about the copay assistance. I got a bill from the pharmacy for $45, but I thought the program covered the full cost?

[00:04:00] AGENT: Let me check that for you. Looking at your enrollment, you're approved for full copay coverage. That $45 charge shouldn't have gone through. I'll escalate this to our billing team and they'll process a refund within 5-7 business days. You should also receive a corrected explanation of benefits.

[00:04:22] PATIENT: Oh good, thank you so much. I was worried about that.

[00:04:28] AGENT: No problem at all. Is there anything else I can help with today?

[00:04:33] PATIENT: No, I think that covers everything. You've been very helpful, Sarah.

[00:04:38] AGENT: Thank you, Margaret. Please remember to contact Dr. Park about those symptoms as soon as you can. And don't hesitate to call us back if you need anything. Have a good day.

[00:04:48] PATIENT: Thank you, goodbye.

[00:04:50] AGENT: Goodbye, Margaret. Take care.
"""

MOCK_SEGMENT_SENTIMENTS = [
    {"segment": "00:00:00-00:00:50", "speaker": "agent", "label": "greeting_verification", "score": 0.85, "emotion": "professional, warm"},
    {"segment": "00:00:00-00:00:50", "speaker": "patient", "label": "greeting_verification", "score": 0.70, "emotion": "neutral, cooperative"},
    {"segment": "00:00:52-00:01:38", "speaker": "patient", "label": "symptom_report", "score": 0.25, "emotion": "concerned, anxious"},
    {"segment": "00:00:52-00:01:38", "speaker": "agent", "label": "symptom_report", "score": 0.75, "emotion": "empathetic, attentive"},
    {"segment": "00:01:38-00:02:05", "speaker": "agent", "label": "ae_documentation", "score": 0.80, "emotion": "professional, thorough"},
    {"segment": "00:01:38-00:02:05", "speaker": "patient", "label": "ae_documentation", "score": 0.45, "emotion": "cooperative, slightly worried"},
    {"segment": "00:02:05-00:02:45", "speaker": "agent", "label": "safety_guidance", "score": 0.90, "emotion": "reassuring, directive"},
    {"segment": "00:02:05-00:02:45", "speaker": "patient", "label": "safety_guidance", "score": 0.30, "emotion": "anxious, uncertain"},
    {"segment": "00:02:45-00:03:15", "speaker": "agent", "label": "ae_reassurance", "score": 0.88, "emotion": "calming, informative"},
    {"segment": "00:02:45-00:03:15", "speaker": "patient", "label": "ae_reassurance", "score": 0.55, "emotion": "relieved, accepting"},
    {"segment": "00:03:15-00:03:48", "speaker": "agent", "label": "enrollment_management", "score": 0.82, "emotion": "helpful, accommodating"},
    {"segment": "00:03:15-00:03:48", "speaker": "patient", "label": "enrollment_management", "score": 0.60, "emotion": "decisive, calmer"},
    {"segment": "00:03:48-00:04:22", "speaker": "agent", "label": "billing_resolution", "score": 0.85, "emotion": "efficient, proactive"},
    {"segment": "00:03:48-00:04:22", "speaker": "patient", "label": "billing_resolution", "score": 0.75, "emotion": "relieved, grateful"},
    {"segment": "00:04:22-00:04:50", "speaker": "agent", "label": "closing", "score": 0.90, "emotion": "warm, professional"},
    {"segment": "00:04:22-00:04:50", "speaker": "patient", "label": "closing", "score": 0.85, "emotion": "satisfied, appreciative"},
]

MOCK_TOPICS = [
    {
        "topic": "Patient Identity Verification",
        "category": "SOP",
        "segments": ["00:00:05-00:00:40"],
        "details": "Agent verified patient identity through name, DOB, member ID, and phone number confirmation.",
    },
    {
        "topic": "Adverse Event Report — Headaches and Dizziness",
        "category": "adverse_event",
        "segments": ["00:00:52-00:02:45"],
        "details": "Patient reported daily headaches and dizziness upon standing after 3 weeks on Vasculin 40mg. Near-fall incident reported. Agent initiated AE documentation.",
    },
    {
        "topic": "Concomitant Medication Review",
        "category": "safety_signal",
        "segments": ["00:01:50-00:02:05"],
        "details": "Patient disclosed concomitant use of lisinopril and aspirin alongside Vasculin. Potential drug interaction flag for BP medications.",
    },
    {
        "topic": "Physician Referral for Symptom Follow-up",
        "category": "safety_signal",
        "segments": ["00:02:05-00:02:22"],
        "details": "Agent recommended patient contact prescribing physician Dr. Raymond Park regarding dizziness symptoms.",
    },
    {
        "topic": "Patient Enrollment — Shipment Hold",
        "category": "enrollment",
        "segments": ["00:03:15-00:03:48"],
        "details": "Patient requested hold on next Vasculin shipment pending physician consultation. Agent processed the hold.",
    },
    {
        "topic": "Copay Assistance — Billing Discrepancy",
        "category": "enrollment",
        "segments": ["00:03:48-00:04:22"],
        "details": "Patient reported unexpected $45 copay charge despite full coverage enrollment. Agent identified error and escalated refund.",
    },
]

MOCK_ADVERSE_EVENTS = [
    {
        "event": "Persistent Headaches",
        "severity": "moderate",
        "confidence": 0.92,
        "onset": "approximately 1 week after starting Vasculin 40mg",
        "frequency": "daily",
        "rationale": "Patient explicitly reported 'really bad headaches, almost every day' temporally associated with Vasculin initiation. Clear causal language and consistent daily pattern indicate high confidence.",
        "verbatim": "I've been having some problems. I'm getting really bad headaches, almost every day.",
    },
    {
        "event": "Orthostatic Dizziness",
        "severity": "moderate-to-severe",
        "confidence": 0.89,
        "onset": "approximately 1 week after starting Vasculin 40mg",
        "frequency": "recurrent, worsening",
        "rationale": "Patient described positional dizziness ('dizzy when I stand up, like the room is spinning') with functional impact (near-fall in kitchen). Worsening trajectory reported. Concomitant lisinopril use may compound hypotensive effects.",
        "verbatim": "sometimes I feel dizzy when I stand up, like the room is spinning. Yesterday I almost fell in the kitchen.",
    },
]

MOCK_TECHNICAL_COMPLAINTS = [
    {
        "complaint": "Billing System Error — Incorrect Copay Charge",
        "confidence": 0.78,
        "category": "billing",
        "rationale": "Patient reported a $45 copay charge that contradicts their full copay coverage enrollment. Agent confirmed this was a system error, indicating a technical issue in the billing/claims processing pipeline.",
        "verbatim": "I got a bill from the pharmacy for $45, but I thought the program covered the full cost?",
    },
]

INTERNAL_ONLY_TERMS = [
    "Project Titan",
    "VoiceIQ",
    "internal-ref",
    "NOVA-2024",
    "pre-launch",
    "Phase IIb",
    "compound NVS-4892",
    "internal audit score",
    "Salesforce case ID",
    "CRM ticket",
]
