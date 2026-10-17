import pytest
from app.errors import AppError
from app.services.journey_rules import require_stage, public_task, adaptation_choice


def test_stage_cannot_be_skipped():
    with pytest.raises(AppError) as error:
        require_stage('investigate', ['independent'])
    assert error.value.status == 409
    require_stage('support', ['support'])


def test_independent_payload_never_leaks_answer_or_rule_keys():
    task = dict(id='x', prompt='Solve', code='print(2)', explanation_prompt='Why?', reasoning_options=[],
                expected_output='2', correct_tag='trace', rules={'trace': 1})
    assert 'expected_output' not in public_task(task)
    assert 'correct_tag' not in public_task(task)
    assert 'rules' not in public_task(task)


def test_adaptation_does_not_reuse_support_or_verification():
    modules = [dict(id='old', hypothesis_id='h', priority=0), dict(id='new', hypothesis_id='h', priority=1)]
    tasks = [dict(id='seen', priority=0), dict(id='fresh', priority=1)]
    result = adaptation_choice('h', modules, tasks, ['old'], ['seen'])
    assert result['support']['id'] == 'new'
    assert result['task']['id'] == 'fresh'
    assert adaptation_choice('h', modules, tasks, ['old', 'new'], ['seen', 'fresh']) is None
