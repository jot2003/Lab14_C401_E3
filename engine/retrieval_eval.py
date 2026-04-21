from typing import List, Dict

class RetrievalEvaluator:
    def __init__(self):
        pass

    def calculate_hit_rate(self, expected_ids: List[str], retrieved_ids: List[str], top_k: int = 3) -> float:
        """
        TODO: Tính toán xem ít nhất 1 trong expected_ids có nằm trong top_k của retrieved_ids không.
        """
        top_retrieved = retrieved_ids[:top_k]
        hit = any(doc_id in top_retrieved for doc_id in expected_ids)
        return 1.0 if hit else 0.0

    def calculate_mrr(self, expected_ids: List[str], retrieved_ids: List[str]) -> float:
        """
        TODO: Tính Mean Reciprocal Rank.
        Tìm vị trí đầu tiên của một expected_id trong retrieved_ids.
        MRR = 1 / position (vị trí 1-indexed). Nếu không thấy thì là 0.
        """
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in expected_ids:
                return 1.0 / (i + 1)
        return 0.0

    async def evaluate_batch(self, dataset: List[Dict], top_k: int = 3) -> Dict:
        """
        Chạy eval cho toàn bộ bộ dữ liệu.
        Dataset cần có trường 'expected_retrieval_ids' và Agent trả về 'retrieved_ids'.
        Trả về cả by_case để debug.
        """
        hit_rates = []
        mrrs = []
        by_case = []
        for idx, case in enumerate(dataset):
            # Fallback: lấy expected ids
            expected_ids = []
            if isinstance(case.get('metadata'), dict) and 'expected_retrieval_ids' in case['metadata']:
                expected_ids = case['metadata']['expected_retrieval_ids']
            elif 'expected_retrieval_ids' in case:
                expected_ids = case['expected_retrieval_ids']
            elif 'expected_ids' in case:
                expected_ids = case['expected_ids']
            if not isinstance(expected_ids, list):
                expected_ids = [expected_ids] if expected_ids else []
            # Fallback: lấy retrieved ids từ agent response
            retrieved_ids = case.get('retrieved_ids') or []
            # Nếu agent trả về metadata dạng dict
            if not retrieved_ids and isinstance(case.get('agent_response'), dict):
                meta = case['agent_response'].get('metadata', {})
                retrieved_ids = meta.get('retrieved_ids') or meta.get('sources') or []
            # Đảm bảo là list
            if not isinstance(expected_ids, list):
                expected_ids = [expected_ids] if expected_ids else []
            if not isinstance(retrieved_ids, list):
                retrieved_ids = [retrieved_ids] if retrieved_ids else []
            # Tính toán
            hit = self.calculate_hit_rate(expected_ids, retrieved_ids, top_k=top_k)
            mrr = self.calculate_mrr(expected_ids, retrieved_ids)
            hit_rates.append(hit)
            mrrs.append(mrr)
            by_case.append({
                "case_idx": idx,
                "expected_ids": expected_ids,
                "retrieved_ids": retrieved_ids,
                "hit_rate": hit,
                "mrr": mrr
            })
        avg_hit_rate = sum(hit_rates) / len(hit_rates) if hit_rates else 0.0
        avg_mrr = sum(mrrs) / len(mrrs) if mrrs else 0.0
        return {
            "avg_hit_rate": avg_hit_rate,
            "avg_mrr": avg_mrr,
            "by_case": by_case
        }
