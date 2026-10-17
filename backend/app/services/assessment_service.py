def evaluate_task(task: dict, response: dict) -> dict:
    interaction = task.get('interaction_json') or {}
    expected = interaction.get('correct_answer', task['expected_output'])
    if interaction.get('format') == 'multi-output':
        correct = [line.strip() for line in response['answer'].strip().splitlines()] == expected.splitlines()
    else:
        correct = response['answer'].strip() == expected.strip()
    explanation_present = bool(response['explanation'].strip())
    reasoning_supported = response['reasoning_tag'] == task['correct_tag']
    return dict(correct=correct, explanation_present=explanation_present,
                reasoning_supported=reasoning_supported,
                passed=correct and explanation_present and reasoning_supported,
                explanation_evidence_tags=[response['reasoning_tag']],
                note='Reasoning is evaluated from your structured choice; your written explanation is retained for teacher review.')
