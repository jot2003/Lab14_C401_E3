import asyncio
import time
from typing import List, Dict, Any
# Import other components...

class BenchmarkRunner:
    def __init__(self, agent, evaluator, judge):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge

    async def run_single_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.perf_counter()
        # 1. Gọi Agent
        response = await self.agent.query(test_case["question"])
        answer_text = response.get("answer", "") if isinstance(response, dict) else str(response)
        latency = time.perf_counter() - start_time
        # Fallback lấy expected_ids
        # Chuẩn hóa lấy expected_ids từ metadata['expected_retrieval_ids'] nếu có
        expected_ids = []
        if isinstance(test_case.get('metadata'), dict) and 'expected_retrieval_ids' in test_case['metadata']:
            expected_ids = test_case['metadata']['expected_retrieval_ids']
        elif 'expected_retrieval_ids' in test_case:
            expected_ids = test_case['expected_retrieval_ids']
        elif 'expected_ids' in test_case:
            expected_ids = test_case['expected_ids']
        # Đảm bảo là list
        if not isinstance(expected_ids, list):
            expected_ids = [expected_ids] if expected_ids else []
        # Fallback lấy retrieved_ids
        retrieved_ids = response.get('retrieved_ids') or []
        if not retrieved_ids and isinstance(response.get('metadata'), dict):
            meta = response['metadata']
            retrieved_ids = meta.get('retrieved_ids') or meta.get('sources') or []
        if not isinstance(retrieved_ids, list):
            retrieved_ids = [retrieved_ids] if retrieved_ids else []
        # 2. Chạy RAGAS metrics
        ragas_scores = await self.evaluator.score(test_case, response)
        # 2b. Tính retrieval metrics thật nếu evaluator có hàm
        hit_rate = None
        mrr = None
        if hasattr(self.evaluator, 'calculate_hit_rate') and hasattr(self.evaluator, 'calculate_mrr'):
            hit_rate = self.evaluator.calculate_hit_rate(expected_ids, retrieved_ids)
            mrr = self.evaluator.calculate_mrr(expected_ids, retrieved_ids)
        # 3. Chạy Multi-Judge
        judge_result = await self.judge.evaluate_multi_judge(
            test_case["question"], 
            answer_text,
            test_case["expected_answer"]
        )

        if judge_result.get("requires_manual_review"):
            status = "review"
        else:
            status = "fail" if judge_result["final_score"] < 3 else "pass"

        # Trả về đầy đủ trace
        return {
            "test_case": test_case["question"],
            "agent_response": answer_text,
            "latency": latency,
            "expected_ids": expected_ids,
            "retrieved_ids": retrieved_ids,
            "hit_rate": hit_rate,
            "mrr": mrr,
            "ragas": ragas_scores,
            "judge": judge_result,
            "status": status,
        }

    async def run_all(self, dataset: List[Dict], batch_size: int = 5) -> List[Dict]:
        """
        Chạy song song bằng asyncio.gather với giới hạn batch_size để không bị Rate Limit.
        """
        results = []
        for i in range(0, len(dataset), batch_size):
            batch = dataset[i:i + batch_size]
            tasks = [self.run_single_test(case) for case in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
        return results
