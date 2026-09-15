TEST_QUESTIONS = [
    {
        "id": 1,
        "category": "direct",
        "question": "How many earned leaves are regular employees entitled to in a calendar year?",
    },
    {
        "id": 2,
        "category": "direct",
        "question": "What is the maximum number of casual leave days an employee can take in a calendar year?",
    },
    {
        "id": 3,
        "category": "hallucination_trap",
        "question": "How many days per week can an employee work from home?",
    },
    {
        "id": 4,
        "category": "table",
        "question": "For Slab-5, what is the eligible travel mode and what are the listed allowance amounts?",
    },
    {
        "id": 5,
        "category": "follow_up",
        "question": "How many of those earned leaves can be carried forward to the next year?",
        "depends_on": 1,
    },
    {
        "id": 6,
        "category": "multi_chunk",
        "question": "What are the leave credit rules for an employee who joins or is transferred during the month?",
    },
    {
        "id": 7,
        "category": "direct",
        "question": "What are the normal working days and working hours of the company?",
    },
    {
        "id": 8,
        "category": "direct",
        "question": "How long is the lunch break and between what times can employees take it?",
    },
    {
        "id": 9,
        "category": "direct",
        "question": "How many times in a month is flexi-entry allowed?",
    },
]
