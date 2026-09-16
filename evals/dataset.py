"""
Evaluation dataset for the patient call analysis agent.

Creates and uploads a dataset to LangSmith with the mock transcript input
and expected reference outputs for evaluators to compare against.
"""

import json
import os

from langsmith import Client

_EXAMPLES_PATH = os.path.join(os.path.dirname(__file__), "eval_examples.json")


def _load_examples() -> list:
    """Load the evaluation examples from the JSON sidecar."""
    with open(_EXAMPLES_PATH) as f:
        return json.load(f)


EVAL_EXAMPLES = _load_examples()


def create_dataset(dataset_name: str = "Patient Call Analysis Eval") -> str:
    """Create and upload the evaluation dataset to LangSmith.

    Returns the dataset ID.
    """
    client = Client()

    existing = None
    for ds in client.list_datasets(dataset_name=dataset_name):
        if ds.name == dataset_name:
            existing = ds
            break

    if existing is not None:
        # Reuse the dataset (keeps experiment history linked to the same id) and
        # clear its examples, rather than deleting the dataset — DELETE /datasets
        # fails once experiments reference it.
        old_ids = [e.id for e in client.list_examples(dataset_id=existing.id)]
        if old_ids:
            client.delete_examples(example_ids=old_ids)
        dataset = existing
        print(f"Reusing dataset '{dataset_name}' (id={existing.id}); cleared {len(old_ids)} old example(s).")
    else:
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description="Evaluation dataset for patient call analysis agent with expected outputs for trajectory, PII, leakage, and correctness checks.",
        )
        print(f"Created dataset '{dataset_name}'.")

    for example in EVAL_EXAMPLES:
        client.create_example(
            inputs=example["inputs"],
            outputs=example["outputs"],
            dataset_id=dataset.id,
        )

    print(f"Uploaded {len(EVAL_EXAMPLES)} example(s) to '{dataset_name}'.")
    return str(dataset.id)


if __name__ == "__main__":
    create_dataset()
