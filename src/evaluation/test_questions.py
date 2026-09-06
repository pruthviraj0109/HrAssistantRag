TEST_QUESTIONS = [
    {
        "id": 1,
        "category": "direct",
        "question": "How many casual leaves can I take in a year?",
    },
    {"id": 2, "category": "direct", "question": "What is the work-from-home policy?"},
    {
        "id": 3,
        "category": "follow_up",
        "question": "How many days per week can I work remotely?",
        "depends_on": 2,
    },
    {
        "id": 4,
        "category": "multi_document",
        "question": "Can I claim hotel expenses during a business trip, and how many leaves can I combine with it?",
    },
    {
        "id": 5,
        "category": "multi_chunk",
        "question": "What is the full process for onboarding a new employee, from offer letter to first day?",
    },
    {
        "id": 6,
        "category": "no_answer",
        "question": "What is the company's policy on pet insurance?",
    },
    {
        "id": 7,
        "category": "hallucination_trap",
        "question": "How many sick leaves are carried forward if I resign mid-year?",
    },
    {
        "id": 8,
        "category": "direct",
        "question": "How many days can I carry forward my unused leave?",
    },
    {
        "id": 9,
        "category": "direct",
        "question": "What is the notice period mentioned in the exit policy?",
    },
    {
        "id": 10,
        "category": "follow_up",
        "question": "And what happens if I don't serve the full notice period?",
        "depends_on": 9,
    },
    {
        "id": 11,
        "category": "hallucination_trap",
        "question": "Does the company provide a signing bonus for referrals?",
    },
    {
        "id": 12,
        "category": "no_answer",
        "question": "What is the maternity leave policy for adopted children?",
    },
]
