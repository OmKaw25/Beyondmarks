from contextlib import redirect_stdout
from io import StringIO
import pytest
from app.content.catalog import catalog
from app.schemas import Correction, TaskResponse
from app.services.diagnostic_engine import assess


def test_diagnostic_probes_are_distinct_and_honest_about_shared_predictions():
    for exercise in catalog():
        hypotheses = {h['key']: h for h in exercise['hypotheses']}
        assert {'concept', 'reading', 'understood', 'time_pressure', 'incomplete'} <= hypotheses.keys()
        probes = exercise['followups']
        assert len(probes) >= 3
        assert len({p['code'] for p in probes}) == len(probes)
        for probe in probes:
            assert set(probe['predictions']) == {h['id'] for h in hypotheses.values()}
            assert set(probe['predictions'].values()) <= {c['value'] for c in probe['choices']}
            if probe['priority'] != 1:  # Reading probe asks about source text, not output.
                output = StringIO()
                with redirect_stdout(output):
                    exec(probe['code'], {'__builtins__': {'print': print, 'range': range}})
                assert output.getvalue().strip() == probe['correct_choice']
        # A correct answer alone cannot distinguish understanding from time pressure.
        assert probes[0]['predictions'][hypotheses['understood']['id']] == probes[0]['predictions'][hypotheses['time_pressure']['id']]


def test_self_report_is_optional_and_not_scored_as_a_diagnosis():
    exercise = catalog()[0]
    payload = Correction(segment_ids=[exercise['segments'][1]['id']], broad_category=exercise['broad'],
                         specific_reason=exercise['reason'], explanation='I tracked the assignment.',
                         confidence='unsure', context='time_pressure', context_note='The lesson was ending.')
    assert payload.context == 'time_pressure'
    assert assess(exercise['hypotheses'], ['caught_flaw']) == assess(exercise['hypotheses'], ['caught_flaw', 'learner_self_report'])
    assert TaskResponse(task_id=exercise['independent'][0]['id'], answer='2', explanation='My reasoning', reasoning_tag='trace').confidence is None


@pytest.mark.integration
def test_pause_resume_context_and_help_are_persisted_and_owned(live_client, integration_engine):
    from tests.test_integration import signup, send, begin
    from sqlalchemy import select
    from sqlalchemy.orm import Session
    from app import models as m
    client = live_client
    learner = signup(client)
    exercise = catalog()[0]
    attempt = begin(client, exercise)
    base = '/api/investigations/' + attempt['id']
    paused = send(client, base + '/agency', {'action': 'pause', 'reason': 'I need a break.'})
    assert paused['stage'] == 'investigate' and paused['agency']['paused']
    correction = dict(segment_ids=[exercise['segments'][1]['id']], broad_category=exercise['broad'],
                      specific_reason=exercise['reason'], explanation='I tracked the assignment.',
                      confidence='unsure', context='time_pressure', context_note='The lesson was ending.')
    assert client.post(base + '/correction', json=correction).status_code == 409
    assert client.get(base).json()['data']['agency']['paused']
    send(client, base + '/agency', {'action': 'help', 'reason': 'Please review the wording.'})
    resumed = send(client, base + '/agency', {'action': 'resume'})
    assert not resumed['agency']['paused'] and resumed['agency']['help_requested']
    result = send(client, base + '/correction', correction)
    assert result['self_report']['context'] == 'time_pressure'
    followup = send(client, base + '/select-follow-up')
    assert followup['followup']['id'] == exercise['followups'][2]['id']
    assert 'did not change the evidence scores' in followup['selection']['rationale']
    answered = send(client, base + '/follow-up', {'answer': exercise['followups'][2]['correct_choice']})
    assert answered['stage'] == 'support'
    with Session(integration_engine) as db:
        evidence = list(db.scalars(select(m.LearnerEvidence).where(m.LearnerEvidence.attempt_id == attempt['id'])))
        assert len([e for e in evidence if e.source == 'learner-agency']) == 3
        assert next(e for e in evidence if e.source == 'self-report').value_json['confidence'] == 'unsure'
    signup(client)
    assert client.post(base + '/agency', json={'action': 'resume'}).status_code == 404
