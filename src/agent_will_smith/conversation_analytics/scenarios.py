"""Predefined conversation scenarios for testing.

Contains 5 predefined scenarios representing different user personas
for testing the intent chat system.
"""

from agent_will_smith.conversation_analytics.models import Scenario


CXO_WEALTH = Scenario(
    scenario_id="cxo_wealth",
    name="High-Level Executive Wealth Planning",
    icon="briefcase",
    short_desc="52-year-old CFO planning for retirement and wealth transfer",
    persona_description=(
        "You are a 52-year-old CFO of a medium-sized tech company. "
        "You have accumulated significant wealth over your career and are now thinking about "
        "retirement planning, wealth preservation, and legacy planning for your family. "
        "You are sophisticated in financial matters, have a moderate risk tolerance, "
        "and are interested in tax-efficient investment strategies. "
        "You have about NT$50 million in investable assets and want to retire by 60."
    ),
    expected_intents=["retirement", "wealth_management", "tax_planning", "estate_planning"],
    expected_life_stage="pre_retirement",
    expected_risk_preference="moderate",
)

YOUNG_STARTER = Scenario(
    scenario_id="young_starter",
    name="Young Professional Getting Started",
    icon="graduation-cap",
    short_desc="28-year-old software engineer starting to invest",
    persona_description=(
        "You are a 28-year-old software engineer at a startup. "
        "You have been working for 5 years and have saved about NT$1 million. "
        "You want to start investing but are not sure where to begin. "
        "You have a long time horizon and can tolerate higher risk for better returns. "
        "You are interested in learning about different investment options and building wealth."
    ),
    expected_intents=["investment", "savings", "wealth_growth"],
    expected_life_stage="early_career",
    expected_risk_preference="aggressive",
)

RETIREE_STABLE = Scenario(
    scenario_id="retiree_stable",
    name="Retiree Seeking Stable Income",
    icon="umbrella-beach",
    short_desc="62-year-old retired teacher seeking stable income",
    persona_description=(
        "You are a 62-year-old retired high school teacher. "
        "You have a pension but want to supplement your income with safe investments. "
        "You have about NT$10 million in savings and want to preserve capital while generating "
        "steady income. You are risk-averse and prefer predictable returns over high growth. "
        "You are also concerned about healthcare costs in the future."
    ),
    expected_intents=["income_generation", "capital_preservation", "healthcare"],
    expected_life_stage="retired",
    expected_risk_preference="conservative",
)

FAMILY_EDUCATION = Scenario(
    scenario_id="family_education",
    name="Family Planning for Children's Education",
    icon="users",
    short_desc="38-year-old couple planning for children's education",
    persona_description=(
        "You are a 38-year-old dual-income couple with two children (ages 8 and 5). "
        "You are planning for your children's education, including potential overseas university. "
        "You have a combined household income of NT$3 million per year and have saved about "
        "NT$8 million. You want to balance education savings with your own retirement planning. "
        "You have moderate risk tolerance and a 10-15 year investment horizon for education goals."
    ),
    expected_intents=["education_planning", "retirement", "family_protection"],
    expected_life_stage="mid_career",
    expected_risk_preference="moderate",
)

FREE_FORM = Scenario(
    scenario_id="free_form",
    name="Free Conversation",
    icon="comments",
    short_desc="Open-ended conversation without predefined persona",
    persona_description=None,
    expected_intents=[],
    expected_life_stage=None,
    expected_risk_preference=None,
)


SCENARIOS: dict[str, Scenario] = {
    "cxo_wealth": CXO_WEALTH,
    "young_starter": YOUNG_STARTER,
    "retiree_stable": RETIREE_STABLE,
    "family_education": FAMILY_EDUCATION,
    "free_form": FREE_FORM,
}


def get_scenario(scenario_id: str) -> Scenario | None:
    """Get a scenario by its ID.

    Args:
        scenario_id: The ID of the scenario to retrieve.

    Returns:
        The Scenario if found, None otherwise.
    """
    return SCENARIOS.get(scenario_id)


def list_scenarios() -> list[Scenario]:
    """Get all available scenarios.

    Returns:
        List of all predefined scenarios.
    """
    return list(SCENARIOS.values())
