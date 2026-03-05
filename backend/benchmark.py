import asyncio
import json
import time
import psutil
import websockets


async def single_user_test(user_id, url, message):
    results = {}
    start = time.perf_counter()
    tokens = 0

    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"message": message}))

        while True:
            response = await asyncio.wait_for(ws.recv(), timeout=60)
            try:
                data = json.loads(response)
                if data.get("type") == "end":
                    break
                if data.get("type") == "error":
                    results["error"] = data["message"]
                    break
            except json.JSONDecodeError:
                tokens += 1

    elapsed = time.perf_counter() - start
    results["user_id"] = user_id
    results["response_time_s"] = round(elapsed, 2)
    results["tokens"] = tokens
    results["tokens_per_second"] = round(tokens / elapsed, 2) if elapsed > 0 else 0
    return results


async def concurrent_test(num_users, url, message):
    tasks = [single_user_test(i + 1, url, message) for i in range(num_users)]
    return await asyncio.gather(*tasks)


def get_system_stats():
    process = psutil.Process()
    return {
        "ram_usage_mb": round(process.memory_info().rss / 1024 / 1024, 2),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "total_ram_mb": round(psutil.virtual_memory().total / 1024 / 1024, 2),
        "available_ram_mb": round(psutil.virtual_memory().available / 1024 / 1024, 2),
    }


async def main():
    url = "ws://localhost:8000/ws/chat"
    test_message = "I want to order a chocolate cake for a birthday party"

    print("=" * 60)
    print("PERFORMANCE BENCHMARK - Bakery Order Assistant")
    print("=" * 60)

    # System info
    stats = get_system_stats()
    print(f"\nSystem RAM: {stats['total_ram_mb']} MB")
    print(f"Available RAM: {stats['available_ram_mb']} MB")
    print(f"CPU Usage: {stats['cpu_percent']}%")

    # Single user test
    print("\n--- Single User Test ---")
    result = await single_user_test(1, url, test_message)
    print(f"Response Time: {result['response_time_s']}s")
    print(f"Tokens: {result['tokens']}")
    print(f"Tokens/sec: {result['tokens_per_second']}")

    # RAM after single request
    stats_after = get_system_stats()
    print(f"RAM Usage (process): {stats_after['ram_usage_mb']} MB")

    # Concurrent users test
    for num_users in [2, 3, 5]:
        print(f"\n--- {num_users} Concurrent Users Test ---")
        results = await concurrent_test(num_users, url, test_message)
        times = [r["response_time_s"] for r in results]
        tps = [r["tokens_per_second"] for r in results]
        print(f"Avg Response Time: {round(sum(times)/len(times), 2)}s")
        print(f"Max Response Time: {max(times)}s")
        print(f"Avg Tokens/sec: {round(sum(tps)/len(tps), 2)}")

    # Final RAM
    final_stats = get_system_stats()
    print(f"\nFinal RAM Usage (process): {final_stats['ram_usage_mb']} MB")
    print(f"Final Available RAM: {final_stats['available_ram_mb']} MB")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
