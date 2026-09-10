TEST_QUESTIONS = [
    {
        "id": 1,
        "category": "direct",
        "question": "How many casual leaves can an employee take in a calendar year?",
    },
    {
        "id": 2,
        "category": "direct",
        "question": "How many earned leaves are regular employees entitled to in a calendar year?",
    },
    {
        "id": 3,
        "category": "follow_up",
        "question": "How many of those leaves can be carried forward to the next year?",
        "depends_on": 2,
    },
    {
        "id": 4,
        "category": "multi_chunk",
        "question": "What are the rules for leave credit when an employee joins during the month?",
    },
    {
        "id": 5,
        "category": "multi_chunk",
        "question": "What are the working days and normal working hours of the company?",
    },
    # {
    #     "id": 6,
    #     "category": "direct",
    #     "question": "How long is the lunch break and during what time can employees take it?",
    # },
    # {
    #     "id": 7,
    #     "category": "hallucination_trap",
    #     "question": "How many sick leaves can an employee carry forward after resigning?",
    # },
    # {
    #     "id": 8,
    #     "category": "direct",
    #     "question": "How many times in a month can an employee use flexi-entry?",
    # },
    # {
    #     "id": 9,
    #     "category": "multi_chunk",
    #     "question": "What are the rules for maternity leave and combining other leave with maternity leave?",
    # },
    # {
    #     "id": 10,
    #     "category": "follow_up",
    #     "question": "What is the maximum total leave allowed when combining other leave with it?",
    #     "depends_on": 9,
    # },
    # {
    #     "id": 11,
    #     "category": "direct",
    #     "question": "What is the probation period mentioned in the HR policy?",
    # },
    # {
    #     "id": 12,
    #     "category": "no_answer",
    #     "question": "What is the company's policy on pet insurance?",
    # },
]
