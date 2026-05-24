from __future__ import annotations

from importlib import resources

from mj_prompt_studio.domain.ruleset import GenerationRuleset, load_ruleset


def load_standard_ruleset() -> GenerationRuleset:
    rule_path = resources.files("mj_prompt_studio.resources.rulesets").joinpath("standard.json")
    with resources.as_file(rule_path) as path:
        return load_ruleset(path)
