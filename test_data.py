#!/usr/bin/env python3
"""
Test script to generate sample data for LLM-Lens dashboard.
This script creates realistic test requests to populate the dashboard with data.
"""


from dotenv import load_dotenv
load_dotenv()
import asyncio
import httpx
import json
import random
from datetime import datetime, timedelta

# Sample test data
SAMPLE_MODELS = ["llama-3.2-1b", "qwen2.5-coder-7b", "mistral-7b-instruct"]

SAMPLE_PROMPTS = [
    "Write a Python function to calculate the factorial of a number.",
    "Explain the concept of machine learning in simple terms.",
    "Create a REST API endpoint for user authentication.",
    "What are the benefits of using containerization in software development?",
    "Write a SQL query to find the top 10 customers by revenue.",
    "Explain the difference between supervised and unsupervised learning.",
    "Create a React component for a todo list.",
    "What is the time complexity of quicksort algorithm?",
    "Write a function to reverse a linked list.",
    "Explain how blockchain technology works."
]

SAMPLE_RESPONSES = [
    "Here's a Python function that calculates the factorial using recursion:\n\ndef factorial(n):\n    if n == 0 or n == 1:\n        return 1\n    return n * factorial(n - 1)",
    "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed for every scenario.",
    "Here's a basic REST API endpoint for authentication:\n\n@app.post('/api/auth/login')\ndef login(credentials: UserCredentials):\n    user = authenticate_user(credentials)\n    if user:\n        token = generate_jwt_token(user)\n        return {'token': token}\n    raise HTTPException(401, 'Invalid credentials')",
    "Containerization provides several key benefits: 1) Consistency across environments, 2) Improved scalability, 3) Resource efficiency, 4) Simplified deployment, 5) Better isolation and security.",
    "SELECT customer_id, customer_name, SUM(order_total) as total_revenue\nFROM orders o\nJOIN customers c ON o.customer_id = c.id\nGROUP BY customer_id, customer_name\nORDER BY total_revenue DESC\nLIMIT 10;",
    "Supervised learning uses labeled training data to learn patterns and make predictions, while unsupervised learning finds hidden patterns in unlabeled data without predetermined outcomes.",
    "Here's a React todo list component:\n\nfunction TodoList() {\n  const [todos, setTodos] = useState([]);\n  const [input, setInput] = useState('');\n  \n  const addTodo = () => {\n    setTodos([...todos, { id: Date.now(), text: input, completed: false }]);\n    setInput('');\n  };\n  \n  return (\n    <div>\n      <input value={input} onChange={(e) => setInput(e.target.value)} />\n      <button onClick={addTodo}>Add</button>\n      {todos.map(todo => <div key={todo.id}>{todo.text}</div>)}\n    </div>\n  );\n}",
    "Quicksort has an average time complexity of O(n log n) and worst-case complexity of O(n²). The average case occurs when the pivot divides the array roughly in half at each step.",
    "Here's a function to reverse a linked list iteratively:\n\ndef reverse_linked_list(head):\n    prev = None\n    current = head\n    \n    while current:\n        next_temp = current.next\n        current.next = prev\n        prev = current\n        current = next_temp\n    \n    return prev",
    "Blockchain is a distributed ledger technology that maintains a continuously growing list of records (blocks) linked using cryptography. Each block contains a hash of the previous block, timestamp, and transaction data."
]

async def create_test_request(session: httpx.AsyncClient, model: str, prompt: str, response: str, streaming: bool = False):
    """Create a test request to the LLM-Lens proxy."""
    
    # Simulate request data
    request_data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": round(random.uniform(0.1, 1.0), 2),
        "max_tokens": random.randint(100, 1000),
        "stream": streaming
    }
    
    try:
        response_obj = await session.post(
            "http://localhost:5000/proxy/v1/chat/completions",
            json=request_data,
            timeout=30.0
        )
        print(f"✓ Created test request: {model} ({'streaming' if streaming else 'non-streaming'})")
        return True
    except Exception as e:
        print(f"✗ Failed to create test request: {e}")
        return False

async def generate_test_data():
    """Generate multiple test requests with various patterns."""
    
    async with httpx.AsyncClient() as session:
        print("🚀 Generating test data for LLM-Lens dashboard...")
        
        # Create a mix of requests
        tasks = []
        
        for i in range(20):  # Create 20 test requests
            model = random.choice(SAMPLE_MODELS)
            prompt = random.choice(SAMPLE_PROMPTS)
            response = random.choice(SAMPLE_RESPONSES)
            streaming = random.choice([True, False])
            
            # Add some delay between requests
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            task = create_test_request(session, model, prompt, response, streaming)
            tasks.append(task)
        
        # Execute all requests
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for result in results if result is True)
        print(f"\n📊 Generated {successful} test requests successfully!")
        print("🎯 You can now view the enhanced dashboard with sample data.")
        print("🌐 Visit: http://localhost:5000")

if __name__ == "__main__":
    asyncio.run(generate_test_data())