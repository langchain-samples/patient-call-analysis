"""
Evaluation dataset for the patient call analysis agent.

Creates and uploads a dataset to LangSmith with the mock transcript input
and expected reference outputs for evaluators to compare against.
"""

from langsmith import Client


EVAL_EXAMPLES = [
    {
        "inputs": {
            "message": "Analyze the patient call. Use the demo transcript.",
        },
        "outputs": {
            "expected_sections": [
                "Call Summary",
                "Sentiment Analysis",
                "Topic Analysis",
                "Adverse Events & Technical Complaints",
                "Agent Performance Review",
                "Overall Assessment & Recommendations",
            ],
            "expected_adverse_events": [
                "Persistent Headaches",
                "Orthostatic Dizziness",
            ],
            "expected_technical_complaints": [
                "Billing System Error",
            ],
            "expected_topics": [
                "Patient Identity Verification",
                "Adverse Event Report",
                "Concomitant Medication Review",
                "Physician Referral",
                "Patient Enrollment",
                "Copay Assistance",
            ],
            "expected_subagent_trajectory": [
                "transcribe_call",
                "sentiment_analysis",
                "topic_and_ae_detection",
                "agent_performance",
            ],
            "pii_that_must_not_appear": [
                "555-867-5309",
                "March 15, 1958",
                "PAT-20241087",
            ],
            "internal_terms_that_must_not_appear": [
                "Project Titan",
                "VoiceIQ",
                "NOVA-2024",
                "compound NVS-4892",
                "CRM ticket",
            ],
            "reference_summary": (
                "This call involved patient Margaret Chen contacting the CardioAssist "
                "program about adverse events experienced while taking Vasculin 40mg. "
                "The patient reported persistent daily headaches and orthostatic dizziness "
                "beginning approximately one week after starting the medication, with a "
                "near-fall incident. The agent properly documented the adverse event, "
                "gathered concomitant medication information (lisinopril, aspirin), and "
                "recommended the patient contact their prescribing physician Dr. Park. "
                "The patient also reported a billing discrepancy ($45 copay charged despite "
                "full coverage), which the agent escalated for refund. The patient requested "
                "a hold on the next medication shipment pending physician consultation. "
                "Overall, the agent demonstrated strong adherence to SOPs with empathetic "
                "communication throughout the call."
            ),
        },
    },
]


def create_dataset(dataset_name: str = "Patient Call Analysis Eval") -> str:
    """Create and upload the evaluation dataset to LangSmith.

    Returns the dataset ID.
    """
    client = Client()

    existing = client.list_datasets(dataset_name=dataset_name)
    for ds in existing:
        if ds.name == dataset_name:
            print(f"Dataset '{dataset_name}' already exists (id={ds.id}). Deleting and recreating.")
            client.delete_dataset(dataset_id=ds.id)
            break

    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description="Evaluation dataset for patient call analysis agent with expected outputs for trajectory, PII, leakage, and correctness checks.",
    )

    for example in EVAL_EXAMPLES:
        client.create_example(
            inputs=example["inputs"],
            outputs=example["outputs"],
            dataset_id=dataset.id,
        )

    print(f"Created dataset '{dataset_name}' with {len(EVAL_EXAMPLES)} example(s).")
    return str(dataset.id)


if __name__ == "__main__":
    create_dataset()
