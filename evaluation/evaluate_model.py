import json

from src.inference.qwen_inference import predict_risk


with open("evaluation/benchmark_cases.json", "r") as f:
    cases = json.load(f)


correct = 0

for case in cases:
    print("=" * 60)
    print("CASE:", case["name"])

    prediction = predict_risk(case["scenario"])

    print("\nMODEL OUTPUT:")
    print(prediction)

    if case["expected_risk"] in prediction:
        correct += 1
        print("\nRESULT: PASS")
    else:
        print("\nRESULT: FAIL")


print("\n" + "=" * 60)
print(f"TOTAL: {correct}/{len(cases)} correct")
