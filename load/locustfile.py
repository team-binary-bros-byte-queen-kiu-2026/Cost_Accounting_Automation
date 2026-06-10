"""
Load test for ConstructAI — targets the live Vercel deployment.
Run: locust -f load/locustfile.py --host https://cost-accounting-automation.vercel.app
     --users 50 --spawn-rate 5 --run-time 2m --headless
"""
import json
import random
from locust import HttpUser, task, between

# Sample session IDs to simulate returning users hitting the chat endpoint
SAMPLE_SESSION_IDS = [f"load-test-session-{i:03d}" for i in range(20)]

CHAT_QUESTIONS = [
    "What is the total material cost?",
    "How much does concrete cost per m3?",
    "What is the labor estimate?",
    "Can you break down the roofing cost?",
    "How accurate is this estimate?",
    "What is the cost per square meter?",
]


class ConstructAIUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def health_check(self):
        """Lightweight probe — does not call LLM."""
        self.client.get("/api/health", name="/api/health")

    @task(5)
    def chat_stream(self):
        """POST /api/chat/stream — primary load target."""
        session_id = random.choice(SAMPLE_SESSION_IDS)
        message = random.choice(CHAT_QUESTIONS)
        payload = {
            "session_id": session_id,
            "message": message,
        }
        with self.client.post(
            "/api/chat/stream",
            json=payload,
            name="/api/chat/stream",
            stream=True,
            catch_response=True,
        ) as resp:
            if resp.status_code == 429:
                resp.success()  # expected under load — fallback handles it
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.success()
