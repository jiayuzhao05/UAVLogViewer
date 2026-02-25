"""Chatbot usage example"""
import requests
import json


BASE_URL = "http://localhost:8000"
TIMEOUT = 15


def upload_file(file_path: str) -> str:
    """Upload a .bin file"""
    print(f"Uploading file: {file_path}")
    
    with open(file_path, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/api/upload",
            files={"file": f},
            timeout=TIMEOUT,
        )
    
    if response.status_code == 200:
        result = response.json()
        file_id = result["file_id"]
        print(f"✓ Uploaded")
        print(f"  file_id: {file_id}")
        print(f"  message: {result['message']}")
        if "parsed_messages" in result:
            print(f"  parsed_messages: {result['parsed_messages']}")
        return file_id
    else:
        print(f"✗ Upload failed: {response.text}")
        return None


def get_summary(file_id: str):
    """Fetch telemetry + anomaly summary."""
    res = requests.get(f"{BASE_URL}/api/telemetry/summary/{file_id}", timeout=TIMEOUT)
    if res.status_code != 200:
        print("✗ Failed to fetch summary")
        return
    data = res.json()
    print("Telemetry summary:", json.dumps(data.get("summary", {}), indent=2))
    print("Anomaly summary:", json.dumps(data.get("anomaly_summary", {}), indent=2))


def ask_question(question: str, file_id: str = None, conversation_id: str = None) -> dict:
    """Send a question"""
    payload = {
        "question": question,
    }
    
    if file_id:
        payload["file_id"] = file_id
    
    if conversation_id:
        payload["conversation_id"] = conversation_id
    
    print(f"\nQ: {question}")
    
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json=payload,
        timeout=TIMEOUT,
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"A: {result['answer']}")
        print(f"confidence: {result['confidence']}")
        
        if result.get("requires_clarification"):
            print(f"clarification: {result.get('clarification_question')}")
        
        return result
    else:
        print(f"✗ Request failed: {response.text}")
        return None


def main():
    """Demo for chatbot"""
    print("=" * 60)
    print("UAV Logger Chatbot Demo")
    print("=" * 60)
    
    example_questions = [
        "What was the highest altitude reached during the flight?",
        "When did the GPS signal first get lost?",
        "What was the maximum battery temperature?",
        "How long was the total flight time?",
        "List all critical errors that happened mid-flight.",
        "When was the first instance of RC signal loss?",
        "Are there any anomalies in this flight?",
    ]
    
    # Replace with your .bin path
    # file_path = "path/to/your/flight_log.bin"
    # file_id = upload_file(file_path)
    # get_summary(file_id)
    
    # If you don't have a file, you can still test chat (without file_id)
    file_id = None
    conversation_id = None
    
    print("\n" + "=" * 60)
    print("Chatting")
    print("=" * 60)
    
    for i, question in enumerate(example_questions, 1):
        print(f"\n[{i}/{len(example_questions)}]")
        result = ask_question(question, file_id=file_id, conversation_id=conversation_id)
        
        if result:
            conversation_id = result["conversation_id"]
        
        print("-" * 60)
    
    print("\n" + "=" * 60)
    print("Done")
    print("=" * 60)


if __name__ == "__main__":
    # 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=TIMEOUT)
        if response.status_code == 200:
            print("✓ Service is up")
            main()
        else:
            print("✗ Service not healthy")
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect; make sure service is running:")
        print("  uvicorn backend.presentation.api.main:app --reload")

