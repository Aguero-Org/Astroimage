from pathlib import Path

import pytest
from pytestarch import EvaluableArchitecture, Rule, get_evaluable_architecture

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PATH = BACKEND_ROOT / "src" / "astroimage"


@pytest.fixture(scope="session")
def evaluable() -> EvaluableArchitecture:
    package = str(PACKAGE_PATH)
    return get_evaluable_architecture(package, package)


def test_infrastructure_does_not_import_api(evaluable: EvaluableArchitecture) -> None:
    (
        Rule()
        .modules_that()
        .are_sub_modules_of("astroimage.infrastructure")
        .should_not()
        .import_modules_that()
        .are_sub_modules_of("astroimage.api")
    ).assert_applies(evaluable)


def test_infrastructure_does_not_import_services(evaluable: EvaluableArchitecture) -> None:
    (
        Rule()
        .modules_that()
        .are_sub_modules_of("astroimage.infrastructure")
        .should_not()
        .import_modules_that()
        .are_sub_modules_of("astroimage.services")
    ).assert_applies(evaluable)


def test_domain_does_not_import_api(evaluable: EvaluableArchitecture) -> None:
    (
        Rule()
        .modules_that()
        .are_sub_modules_of("astroimage.domain")
        .should_not()
        .import_modules_that()
        .are_sub_modules_of("astroimage.api")
    ).assert_applies(evaluable)


def test_domain_does_not_import_services(evaluable: EvaluableArchitecture) -> None:
    (
        Rule()
        .modules_that()
        .are_sub_modules_of("astroimage.domain")
        .should_not()
        .import_modules_that()
        .are_sub_modules_of("astroimage.services")
    ).assert_applies(evaluable)


def test_services_do_not_import_api(evaluable: EvaluableArchitecture) -> None:
    (
        Rule()
        .modules_that()
        .are_sub_modules_of("astroimage.services")
        .should_not()
        .import_modules_that()
        .are_sub_modules_of("astroimage.api")
    ).assert_applies(evaluable)
