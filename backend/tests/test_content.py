from contextlib import redirect_stdout
from io import StringIO
from app.content.catalog import catalog


def test_authored_code_matches_expected_outputs_and_verification_is_unseen():
    for exercise in catalog():
        snippets = [exercise, *exercise['transfer'], *exercise['independent'], *exercise['reflection']]
        assert len({task['code'] for task in snippets}) == len(snippets)
        for task in snippets:
            output = StringIO()
            # Execute only this repository's trusted, fixed curriculum in a unit test.
            code = task['code']
            config = task.get('interaction_json', {})
            if config.get('format') == 'repair':
                code = code.replace('# YOUR CHANGE', config['correct_answer'])
            elif config.get('format') == 'counterexample':
                code = code.replace('CHOSEN_VALUE', config['correct_answer'])
            with redirect_stdout(output):
                exec(code, {'__builtins__': {'print': print, 'range': range}})
            assert output.getvalue().strip() == task['expected_output'], task['code']
        assert any(s['is_flawed'] for s in exercise['segments'])
        assert len(exercise['hypotheses']) >= 2
        assert len(exercise['independent']) >= 3


def test_all_followups_and_support_have_valid_answer_keys():
    for exercise in catalog():
        for task in exercise['followups'] + exercise['support']:
            assert task['correct_choice'] in [choice['value'] for choice in task['choices']]
        for task in exercise['transfer'] + exercise['independent']:
            assert task['correct_tag'] in [choice['value'] for choice in task['reasoning_options']]
