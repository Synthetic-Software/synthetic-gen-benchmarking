from typing import List

from synthetic_benchmarking.helpers.classes import FilePair, ProblemGeneratorParameters, GeneratedProblemStatement, \
    ListOfGeneratedProblems, ValidatorModelStats
from synthetic_benchmarking.helpers.clients import OPENAI_CLIENT
from synthetic_benchmarking.helpers.helpers import calculate_price

from pathlib import Path

def generate_problem_statements(
    repo_path: Path,
    filepairs: List[FilePair],
    parameters: ProblemGeneratorParameters
) -> List[GeneratedProblemStatement]:
    selected_file_pair = parameters.filepair_selection_logic(filepairs)
    prompt_text = parameters.prompt_template.render(
        dict(
            files=selected_file_pair.files
        )
    )

    model_map = {
        "gpt4omini": "gpt-4o-mini",
        "gpt4o": "gpt-4o"
    }
    model = parameters.problem_gen_model if parameters.problem_gen_model not in model_map \
        else model_map[parameters.problem_gen_model]


    completion = OPENAI_CLIENT.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": prompt_text},
            {"role": "user", "content": f"Generate the list of problem statements. Generate exactly {parameters.num_problems_to_gen} statements, no more and no less"},
        ],
        response_format=ListOfGeneratedProblems,
    )

    parsed_response = completion.choices[0].message.parsed.generated_problem_statements
    prompt_tokens, completion_tokens = completion.usage.prompt_tokens, completion.usage.completion_tokens
    cost = calculate_price(model, prompt_tokens, completion_tokens)

    return [
        GeneratedProblemStatement(
            repo_path=repo_path,
            prompt=prompt_text,
            model=model,
            problem_statement=statement.problem_statement,
            dynamic_checklist=statement.dynamic_checklist,
            model_stats=ValidatorModelStats(
                input_tokens=prompt_tokens,
                output_tokens=completion_tokens,
                cost=cost,
            ),
        ) for statement in parsed_response
    ]
