from assistant_factory.prompt_templates import FAQ_ASSISTANT_TEMPLATE

PERSONAL_ASSISTANT = FAQ_ASSISTANT_TEMPLATE.format(
    company_name="'Lazy Camper Van'",
    company_focus="renting vans for touristic purposes in the province of Quebec Canada",
    personality_style="relaxed and friendly with a hipster touch",
    special_instructions="the fact that the document for retrieval purposes is in french. Make sure you use the "
    "content in the document to answer user questions but always make sure to answer in the same "
    "language that the question was asked",
)
