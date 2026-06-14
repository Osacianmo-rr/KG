import json
from collections import defaultdict
from app import answer

with open("testset.json", "r", encoding="utf-8") as f:
    testset = json.load(f)

correct = 0
total = len(testset)
correct_by_type = defaultdict(int)
total_by_type = defaultdict(int)

for i, item in enumerate(testset, 1):
    question = item["question"]
    gold = set(item["answer"])
    qtype = item["type"]
    total_by_type[qtype] += 1

    pred = set(answer(question))

    # 宽松匹配：预测包含 Gold 即正确
    if gold.issubset(pred):
        correct += 1
        correct_by_type[qtype] += 1
        print(f"✓ {i}. {question}")
    else:
        print(f"✗ {i}. {question}")
        print(f"   Pred: {sorted(pred)}")
        print(f"   Gold: {sorted(gold)}")

print("\n" + "=" * 50)
print(f"Total: {total}")
print(f"Correct: {correct}")
print(f"Overall Accuracy: {correct/total*100:.2f}%")
print("=" * 50)

print("\nAccuracy by type:")
for t in sorted(total_by_type.keys()):
    acc = correct_by_type[t] / total_by_type[t] * 100
    print(f"  {t}: {acc:.2f}% ({correct_by_type[t]}/{total_by_type[t]})")