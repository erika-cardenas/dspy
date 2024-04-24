import random

import typing as t
from datasets import load_dataset
from dspy.primitives.example import Example

from .dataset import Dataset
from pydantic import Field


class HotPotQA(Dataset):
    keep_details: t.Literal["true", "dev_titles", "false"] = Field(default="dev_titles")
    unofficial_dev: bool = Field(default=True)

    def load(self) -> None:
        train_ds, dev_ds = load_dataset("hotpot_qa", "fullwiki", split=["train", "validation"])

        if self.keep_details == "true":
            keys = ["id", "question", "answer", "type", "supporting_facts"]
        elif self.keep_details == "dev_titles":
            keys = ["question", "answer", "supporting_facts"]
        else:
            keys = ["question", "answer"]

        def process_sample(sample, keys) -> Example:
            example = Example(**{k: sample[k] for k in keys})

            if "supporting_facts" in example:
                example["gold_titles"] = set(example["supporting_facts"]["title"])
                del example["supporting_facts"]

            return example

        train_examples = [process_sample(sample, keys) for sample in train_ds if sample["level"] == "hard"]
        test_examples = [process_sample(sample, keys) for sample in dev_ds if sample["level"] == "hard"]

        random.shuffle(train_examples)

        sep_idx = len(train_examples) * 75 // 100
        self.train_examples = train_examples[:sep_idx]

        if self.unofficial_dev:
            self.dev_examples = train_examples[sep_idx:]
        else:
            self.dev_examples = None

        self.test_examples = test_examples
