"""
Benchmark script for Financial AI Agent
Measures real latency, throughput, and costs
"""
import asyncio
import time
import statistics
from decimal import Decimal
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.hf_inference import HFInferenceService
from app.config import get_settings

settings = get_settings()


async def benchmark_classification(service: HFInferenceService, iterations: int = 10):
    """Benchmark transaction classification latency."""
    print(f"\n🔍 Benchmarking Classification ({iterations} iterations)...")
    
    test_transactions = [
        ("TRANSFERENCIA RECIBIDA NOMINA", 2500.0),
        ("COMPRA AMAZON", -45.99),
        ("RECIBO LUZ IBERDROLA", -89.50),
        ("PAGO SEGURO ZURICH", -120.0),
        ("FACTURA CLIENTE ABC SL", 1500.0),
    ]
    
    latencies = []
    
    for i in range(iterations):
        concepto, importe = test_transactions[i % len(test_transactions)]
        start = time.perf_counter()
        
        try:
            result = await service.classify_transaction(concepto, importe)
            elapsed = time.perf_counter() - start
            latencies.append(elapsed)
            print(f"  ✓ Iteration {i+1}/{iterations}: {elapsed:.3f}s - {result.get('categoria_pgc', 'N/A')}")
        except Exception as e:
            print(f"  ✗ Iteration {i+1}/{iterations} failed: {e}")
    
    if latencies:
        return {
            "mean": statistics.mean(latencies),
            "median": statistics.median(latencies),
            "p50": statistics.median(latencies),
            "p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies),
            "p99": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies),
            "min": min(latencies),
            "max": max(latencies),
            "samples": len(latencies),
        }
    return None


async def benchmark_embeddings(service: HFInferenceService, iterations: int = 10):
    """Benchmark embedding generation latency."""
    print(f"\n🔍 Benchmarking Embeddings ({iterations} iterations)...")
    
    test_texts = [
        "Transferencia bancaria por nómina mensual",
        "Pago de seguro médico anual",
        "Compra de material de oficina",
        "Factura de servicios profesionales",
        "Ingreso por venta de productos",
    ]
    
    latencies = []
    
    for i in range(iterations):
        texts = [test_texts[i % len(test_texts)]]
        start = time.perf_counter()
        
        try:
            result = await service.generate_embeddings(texts)
            elapsed = time.perf_counter() - start
            latencies.append(elapsed)
            dim = len(result[0]) if result and result[0] else 0
            print(f"  ✓ Iteration {i+1}/{iterations}: {elapsed:.3f}s - dim={dim}")
        except Exception as e:
            print(f"  ✗ Iteration {i+1}/{iterations} failed: {e}")
    
    if latencies:
        return {
            "mean": statistics.mean(latencies),
            "median": statistics.median(latencies),
            "p50": statistics.median(latencies),
            "p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies),
            "p99": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies),
            "min": min(latencies),
            "max": max(latencies),
            "samples": len(latencies),
        }
    return None


def estimate_cost(classification_calls: int, embedding_calls: int):
    """Estimate API costs based on HuggingFace pricing."""
    # Rough estimates (HF pricing varies)
    # Mixtral-8x7B: ~$0.0007 per 1K tokens
    # BGE-M3 embeddings: ~$0.0001 per 1K tokens
    
    # Average tokens per classification: ~200 input + 50 output = 250 tokens
    classification_cost = (classification_calls * 250 / 1000) * 0.0007
    
    # Average tokens per embedding: ~20 tokens
    embedding_cost = (embedding_calls * 20 / 1000) * 0.0001
    
    return {
        "classification_total": classification_cost,
        "embedding_total": embedding_cost,
        "total": classification_cost + embedding_cost,
        "per_classification": classification_cost / classification_calls if classification_calls > 0 else 0,
        "per_embedding": embedding_cost / embedding_calls if embedding_calls > 0 else 0,
    }


async def main():
    """Run all benchmarks."""
    print("=" * 60)
    print("🚀 Financial AI Agent - Benchmark Suite")
    print("=" * 60)
    print(f"Model LLM: {settings.hf_model_llm}")
    print(f"Model Embeddings: {settings.hf_model_embeddings}")
    print(f"HF Token configured: {'✓' if settings.hf_token else '✗ (will fail)'}")
    
    if not settings.hf_token:
        print("\n⚠️  ERROR: HF_TOKEN not configured in .env")
        print("Please set your HuggingFace token to run benchmarks.")
        return
    
    service = HFInferenceService()
    
    # Run benchmarks
    classification_results = await benchmark_classification(service, iterations=10)
    embedding_results = await benchmark_embeddings(service, iterations=10)
    
    # Calculate costs
    costs = estimate_cost(
        classification_calls=classification_results["samples"] if classification_results else 0,
        embedding_calls=embedding_results["samples"] if embedding_results else 0,
    )
    
    # Print results
    print("\n" + "=" * 60)
    print("📊 BENCHMARK RESULTS")
    print("=" * 60)
    
    if classification_results:
        print("\n📈 Classification (PGC):")
        print(f"  Mean:   {classification_results['mean']:.3f}s")
        print(f"  Median: {classification_results['median']:.3f}s")
        print(f"  p95:    {classification_results['p95']:.3f}s")
        print(f"  p99:    {classification_results['p99']:.3f}s")
        print(f"  Min:    {classification_results['min']:.3f}s")
        print(f"  Max:    {classification_results['max']:.3f}s")
    
    if embedding_results:
        print("\n📈 Embeddings:")
        print(f"  Mean:   {embedding_results['mean']:.3f}s")
        print(f"  Median: {embedding_results['median']:.3f}s")
        print(f"  p95:    {embedding_results['p95']:.3f}s")
        print(f"  p99:    {embedding_results['p99']:.3f}s")
        print(f"  Min:    {embedding_results['min']:.3f}s")
        print(f"  Max:    {embedding_results['max']:.3f}s")
    
    print("\n💰 Cost Estimates:")
    print(f"  Per classification: ${costs['per_classification']:.6f}")
    print(f"  Per embedding:      ${costs['per_embedding']:.6f}")
    print(f"  Total benchmark:    ${costs['total']:.6f}")
    
    print("\n✅ Benchmark complete!")
    print("=" * 60)
    
    # Save results to file
    results_file = Path(__file__).parent.parent / "docs" / "benchmark_results.json"
    import json
    with open(results_file, "w") as f:
        json.dump({
            "classification": classification_results,
            "embeddings": embedding_results,
            "costs": costs,
            "config": {
                "llm_model": settings.hf_model_llm,
                "embedding_model": settings.hf_model_embeddings,
            }
        }, f, indent=2)
    print(f"\n📁 Results saved to: {results_file}")
    
    await service.close()


if __name__ == "__main__":
    asyncio.run(main())

