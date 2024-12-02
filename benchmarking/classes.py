from dataclasses import dataclass
from pathlib import Path
from typing import List, Callable
from jinja2 import Template
from pydantic import BaseModel

@dataclass 
class IngestionHeuristics:
    min_files_to_consider_dir_for_problems: int
    min_file_content_len: int

@dataclass
class File:
    path: Path
    contents: str

@dataclass
class EmbeddedFile:
    path: str
    contents: str
    embedding: list

    def __str__(self):
        return f"File: {self.path}, Length: {len(self.contents)}"
    
    def __repr__(self) -> str:
        return f"File: {self.path}, Length: {len(self.contents)}"

@dataclass
class FilePair:
    cosine_similarity: float
    files: List[EmbeddedFile]

@dataclass
class ProblemGeneratorParameters:
    filepair_selection_logic: Callable[[List[FilePair]], FilePair]
    prompt_template: Template
    num_problems_to_gen: int
    problem_gen_model: str = "gpt-4o-2024-08-06"

@dataclass
class GeneratedProblemStatement:
    prompt: str
    model: str
    problem_statement: str

# We use pydantic for some classes because OpenAI json output can structure based on that
class ListOfGeneratedProblems(BaseModel):
    generated_problem_statements: list[str]

class MinerOutputScore(BaseModel):
    addresses_problem_in_statement: float
    logical_solution: float
    brevity_and_cleanliness_of_code: float
    potential_bugs_generated: float

class FullyScoredProblem:
    generated_problem_statement: GeneratedProblemStatement
    miner_solution_patch: str
    miner_output_score: MinerOutputScore