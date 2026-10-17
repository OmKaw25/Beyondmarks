from contextlib import redirect_stdout
from io import StringIO
import pytest
from app.content.practice_variants import support_variant, task_variant
from app.services.assessment_service import evaluate_task
from app.services.journey_rules import public_task


def output_of(code):
    output=StringIO()
    # Only trusted repository templates are executed, never learner/AI input.
    with redirect_stdout(output):
        exec(code, {'__builtins__': {'print':print, 'range':range}})
    return output.getvalue().strip()


@pytest.mark.parametrize('slug', ['variables','conditionals','loops'])
def test_fresh_practice_has_distinct_content_valid_answers_and_changing_positions(slug):
    seen=set(); positions=set()
    for index in range(20):
        variant=support_variant(slug,index)
        assert variant['worked_example'] not in seen
        seen.add(variant['worked_example'])
        assert output_of(variant['worked_example'])==variant['correct_choice']
        values=[c['value'] for c in variant['choices_json']]
        assert len(set(values))==len(values)
        positions.add(values.index(variant['correct_choice']))
    assert len(positions)>1


@pytest.mark.parametrize('slug', ['variables','conditionals','loops'])
def test_new_checks_retain_phase_difficulty_have_correct_keys_and_hide_answers(slug):
    for phase,difficulty in [('transfer','Apply'),('independent','Challenge'),('reflection','Stretch')]:
        seen=set(); positions=set()
        for index in range(20):
            variant=task_variant(slug,phase,index)
            config=variant['interaction_json']
            assert config['difficulty']==difficulty
            fingerprint=(variant['prompt'],variant['code'],str(config.get('choices')))
            assert fingerprint not in seen
            seen.add(fingerprint)
            answer=config.get('correct_answer',variant['expected_output'])
            code=variant['code'].replace('# YOUR CHANGE',answer).replace('CHOSEN_VALUE',answer)
            assert output_of(code)==variant['expected_output']
            response=dict(answer=answer,explanation='I traced each change.',reasoning_tag=variant['correct_tag'])
            assert evaluate_task(variant,response)['passed']
            assert not evaluate_task(variant,{**response,'reasoning_tag':'guess'})['passed']
            public=public_task(variant)
            assert 'correct_answer' not in public['interaction']
            assert 'expected_output' not in public and 'correct_tag' not in public
            if config.get('choices'):
                positions.add([c['value'] for c in config['choices']].index(answer))
        if phase!='independent':
            assert len(positions)>1
