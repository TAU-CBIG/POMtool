import pytest
import run_job_utility


def pytest_addoption(parser):
    parser.addoption("--skip-lead", action="store_true", help="A custom option for pytest")
    parser.addoption("--make-gold", action="store_true", help="A custom option for pytest")


@pytest.fixture(scope='session')
def job_session_fixture(request):
    run_job_utility.skip = (request.config.getoption("--skip-lead"))
    yield

    make_gold = (request.config.getoption("--make-gold"))
    if make_gold:
        for f in set(run_job_utility.gold_files):
            run_job_utility.make_gold_file(f)
