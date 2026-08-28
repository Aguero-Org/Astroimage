"""Global architecture rules for the feature-based backend layout.

Package layout under ``astroimage``:

* one package per feature (e.g. ``health``), containing role modules
  (``controller``, ``service``, ``dao``/``repository``, ``model``, ``schema``);
* ``shared`` for cross-cutting infrastructure only;
* ``main`` / ``config`` as composition root (not features).

Rules are derived from the packages on disk so new features inherit the same
constraints automatically. Explicit allow-lists exist only for documented
exceptions.

Feature-specific architecture tests (if ever needed) live under
``tests/architecture/<feature>/``.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pytest
from pytestarch import (
    EvaluableArchitecture,
    LayeredArchitecture,
    LayerRule,
    Rule,
    get_evaluable_architecture,
)

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PATH = BACKEND_ROOT / "src" / "astroimage"
TESTS_PATH = BACKEND_ROOT / "tests"
PACKAGE_NAME = "astroimage"

# Top-level packages that are not features.
NON_FEATURE_PACKAGES = frozenset({"shared"})

# Composition-root modules at package root (files, not feature packages).
COMPOSITION_ROOT_MODULES = frozenset({"main", "config"})

# Allowed non-feature packages under tests/{unit,integration,architecture}/.
ALLOWED_NON_FEATURE_TEST_PACKAGES = frozenset({"shared", "config", "main"})

# Historical / global technical layer package names that must not reappear.
FORBIDDEN_GLOBAL_LAYER_PACKAGES = frozenset(
    {
        "api",
        "controllers",
        "daos",
        "domain",
        "infrastructure",
        "models",
        "repositories",
        "schemas",
        "services",
    }
)

# Intra-feature role module stems (Python module file names without .py).
CONTROLLER_MODULES = frozenset({"controller"})
SERVICE_MODULES = frozenset({"service"})
DAO_MODULES = frozenset({"dao", "repository"})
MODEL_MODULES = frozenset({"model"})
SCHEMA_MODULES = frozenset({"schema"})

# Cross-feature imports that are explicitly allowed (none today).
# Prefer depending on another feature's public service, never on dao/model.
ALLOWED_FEATURE_DEPENDENCIES: frozenset[tuple[str, str]] = frozenset()

TEST_TYPE_DIRS = ("architecture", "unit", "integration")


def _discover_feature_names() -> list[str]:
    """Return top-level feature package names under ``astroimage``."""
    features: list[str] = []
    for path in sorted(PACKAGE_PATH.iterdir()):
        if not path.is_dir() or path.name.startswith(("_", ".")):
            continue
        if path.name in NON_FEATURE_PACKAGES:
            continue
        if path.name in FORBIDDEN_GLOBAL_LAYER_PACKAGES:
            continue
        if not (path / "__init__.py").exists():
            continue
        features.append(path.name)
    return features


def _feature_module(feature: str) -> str:
    return f"{PACKAGE_NAME}.{feature}"


def _role_module(feature: str, role: str) -> str:
    return f"{PACKAGE_NAME}.{feature}.{role}"


@pytest.fixture(scope="session")
def evaluable() -> EvaluableArchitecture:
    package = str(PACKAGE_PATH)
    return get_evaluable_architecture(package, package)


@pytest.fixture(scope="session")
def features() -> list[str]:
    discovered = _discover_feature_names()
    assert discovered, "expected at least one feature package under astroimage/"
    return discovered


def test_no_global_technical_layer_packages() -> None:
    """Features must not be reorganized into global layer folders."""
    present = sorted(
        path.name
        for path in PACKAGE_PATH.iterdir()
        if path.is_dir() and path.name in FORBIDDEN_GLOBAL_LAYER_PACKAGES
    )
    assert present == [], f"forbidden global layer packages present: {present}"


def test_features_are_top_level_packages(features: list[str]) -> None:
    for feature in features:
        feature_dir = PACKAGE_PATH / feature
        assert feature_dir.is_dir()
        assert (feature_dir / "__init__.py").exists()


def test_test_tree_is_typed_then_modular(features: list[str]) -> None:
    """tests/<type>/<feature|shared|config>/… — never global component folders."""
    allowed_packages = frozenset(features) | ALLOWED_NON_FEATURE_TEST_PACKAGES

    top_level = {path.name for path in TESTS_PATH.iterdir() if path.is_dir()}
    stray_feature_dirs = sorted(
        name for name in top_level if name in features or name in ALLOWED_NON_FEATURE_TEST_PACKAGES
    )
    assert stray_feature_dirs == [], (
        "feature/shared packages must not sit at tests/ root; "
        f"nest them under unit|integration|architecture: {stray_feature_dirs}"
    )

    for test_type in TEST_TYPE_DIRS:
        type_root = TESTS_PATH / test_type
        if not type_root.is_dir():
            continue
        for path in sorted(type_root.iterdir()):
            if path.name.startswith(("_", ".")) or path.name == "__pycache__":
                continue
            if path.is_file():
                # Cross-cutting suites (e.g. openapi contract, global arch rules).
                assert path.suffix == ".py", f"unexpected file in tests/{test_type}: {path.name}"
                continue
            assert path.is_dir(), f"unexpected entry in tests/{test_type}: {path.name}"
            assert path.name in allowed_packages, (
                f"tests/{test_type}/{path.name} is not a known feature/shared/composition package"
            )
            assert path.name not in FORBIDDEN_GLOBAL_LAYER_PACKAGES, (
                f"global layer test package is forbidden: tests/{test_type}/{path.name}"
            )


def test_shared_does_not_import_features(
    evaluable: EvaluableArchitecture,
    features: list[str],
) -> None:
    for feature in features:
        (
            Rule()
            .modules_that()
            .are_sub_modules_of(f"{PACKAGE_NAME}.shared")
            .should_not()
            .import_modules_that()
            .are_sub_modules_of(_feature_module(feature))
        ).assert_applies(evaluable)


def test_features_do_not_import_composition_root(
    evaluable: EvaluableArchitecture,
    features: list[str],
) -> None:
    """Features stay free of the app entrypoint; main may import features."""
    for feature in features:
        for root_module in COMPOSITION_ROOT_MODULES:
            (
                Rule()
                .modules_that()
                .are_sub_modules_of(_feature_module(feature))
                .should_not()
                .import_modules_that()
                .are_named(f"{PACKAGE_NAME}.{root_module}")
            ).assert_applies(evaluable)


def test_features_do_not_depend_on_other_features_unless_allowed(
    evaluable: EvaluableArchitecture,
    features: list[str],
) -> None:
    """Default: no cross-feature imports. Exceptions live in ALLOWED_FEATURE_DEPENDENCIES."""
    for source in features:
        for target in features:
            if source == target:
                continue
            if (source, target) in ALLOWED_FEATURE_DEPENDENCIES:
                continue
            (
                Rule()
                .modules_that()
                .are_sub_modules_of(_feature_module(source))
                .should_not()
                .import_modules_that()
                .are_sub_modules_of(_feature_module(target))
            ).assert_applies(evaluable)


def test_features_do_not_import_other_features_internals(
    evaluable: EvaluableArchitecture,
    features: list[str],
) -> None:
    """Even allowed collaborators must not touch another feature's dao/model."""
    internal_roles = sorted(DAO_MODULES | MODEL_MODULES)
    for source in features:
        for target in features:
            if source == target:
                continue
            for role in internal_roles:
                (
                    Rule()
                    .modules_that()
                    .are_sub_modules_of(_feature_module(source))
                    .should_not()
                    .import_modules_that()
                    .are_named(_role_module(target, role))
                ).assert_applies(evaluable)


def test_no_circular_dependencies_between_features(
    evaluable: EvaluableArchitecture,
    features: list[str],
) -> None:
    """Detect direct or transitive cycles among feature packages."""
    adjacency: dict[str, set[str]] = defaultdict(set)

    for source in features:
        for target in features:
            if source == target:
                continue
            rule = (
                Rule()
                .modules_that()
                .are_sub_modules_of(_feature_module(source))
                .should_not()
                .import_modules_that()
                .are_sub_modules_of(_feature_module(target))
            )
            try:
                rule.assert_applies(evaluable)
            except AssertionError:
                adjacency[source].add(target)

    white, gray, black = 0, 1, 2
    color = dict.fromkeys(features, white)

    def _visit(node: str, path: list[str]) -> list[str] | None:
        color[node] = gray
        path.append(node)
        for nxt in adjacency[node]:
            if color[nxt] == gray:
                return [*path, nxt]
            if color[nxt] == white:
                found = _visit(nxt, path[:])
                if found is not None:
                    return found
        color[node] = black
        return None

    for feature in features:
        if color[feature] != white:
            continue
        cycle = _visit(feature, [])
        assert cycle is None, f"circular feature dependency detected: {' -> '.join(cycle)}"


def _existing_role_modules(features: list[str], roles: frozenset[str]) -> list[str]:
    modules: list[str] = []
    for feature in features:
        for role in sorted(roles):
            path = PACKAGE_PATH / feature / f"{role}.py"
            if path.is_file():
                modules.append(_role_module(feature, role))
    return modules


def test_intra_feature_layer_dependencies(
    evaluable: EvaluableArchitecture,
    features: list[str],
) -> None:
    """controller → service → dao → model (and schema stays passive).

    Layers are collected across features by role module name. Missing roles are
    skipped so small features (controller + schema only) still type-check.
    """
    controllers = _existing_role_modules(features, CONTROLLER_MODULES)
    services = _existing_role_modules(features, SERVICE_MODULES)
    daos = _existing_role_modules(features, DAO_MODULES)
    models = _existing_role_modules(features, MODEL_MODULES)
    schemas = _existing_role_modules(features, SCHEMA_MODULES)

    layers: list[tuple[str, list[str]]] = [
        ("controller", controllers),
        ("service", services),
        ("dao", daos),
        ("model", models),
        ("schema", schemas),
    ]
    present = [(name, modules) for name, modules in layers if modules]
    if len(present) < 2:
        pytest.skip("not enough role modules present to assert layer rules")

    architecture: LayeredArchitecture = LayeredArchitecture()
    for name, modules in present:
        # containing_modules is typed as BaseLayeredArchitecture; cast back.
        architecture = architecture.layer(name).containing_modules(modules)  # type: ignore[assignment]

    def forbid(source_layer: str, *target_layers: str) -> None:
        existing_targets = [layer for layer in target_layers if layer in dict(present)]
        if source_layer not in dict(present) or not existing_targets:
            return
        (
            LayerRule()
            .based_on(architecture)
            .layers_that()
            .are_named(source_layer)
            .should_not()
            .access_layers_that()
            .are_named(existing_targets if len(existing_targets) > 1 else existing_targets[0])
        ).assert_applies(evaluable)

    # model is the innermost layer
    forbid("model", "controller", "service", "dao", "schema")
    # dao must not climb toward application/HTTP
    forbid("dao", "controller", "service", "schema")
    # service must not depend on HTTP controllers
    forbid("service", "controller")
    # controllers must not skip the service layer and hit persistence directly
    forbid("controller", "dao", "model")
    # schemas are DTOs: no outbound deps into other role layers
    forbid("schema", "controller", "service", "dao", "model")


def test_controllers_do_not_import_dao_or_model_modules(
    evaluable: EvaluableArchitecture,
    features: list[str],
) -> None:
    """Belt-and-suspenders Rule form of controller ↛ dao/model."""
    for feature in features:
        controller = PACKAGE_PATH / feature / "controller.py"
        if not controller.is_file():
            continue
        for role in sorted(DAO_MODULES | MODEL_MODULES):
            for target_feature in features:
                target_path = PACKAGE_PATH / target_feature / f"{role}.py"
                if not target_path.is_file():
                    continue
                (
                    Rule()
                    .modules_that()
                    .are_named(_role_module(feature, "controller"))
                    .should_not()
                    .import_modules_that()
                    .are_named(_role_module(target_feature, role))
                ).assert_applies(evaluable)


def test_models_do_not_import_upper_layers(
    evaluable: EvaluableArchitecture,
    features: list[str],
) -> None:
    upper = sorted(CONTROLLER_MODULES | SERVICE_MODULES | DAO_MODULES | SCHEMA_MODULES)
    for feature in features:
        model_path = PACKAGE_PATH / feature / "model.py"
        if not model_path.is_file():
            continue
        for role in upper:
            for target_feature in features:
                target_path = PACKAGE_PATH / target_feature / f"{role}.py"
                if not target_path.is_file():
                    continue
                (
                    Rule()
                    .modules_that()
                    .are_named(_role_module(feature, "model"))
                    .should_not()
                    .import_modules_that()
                    .are_named(_role_module(target_feature, role))
                ).assert_applies(evaluable)


def test_daos_do_not_import_service_or_controller(
    evaluable: EvaluableArchitecture,
    features: list[str],
) -> None:
    upper = sorted(CONTROLLER_MODULES | SERVICE_MODULES)
    for feature in features:
        for dao_role in sorted(DAO_MODULES):
            dao_path = PACKAGE_PATH / feature / f"{dao_role}.py"
            if not dao_path.is_file():
                continue
            for role in upper:
                for target_feature in features:
                    target_path = PACKAGE_PATH / target_feature / f"{role}.py"
                    if not target_path.is_file():
                        continue
                    (
                        Rule()
                        .modules_that()
                        .are_named(_role_module(feature, dao_role))
                        .should_not()
                        .import_modules_that()
                        .are_named(_role_module(target_feature, role))
                    ).assert_applies(evaluable)
