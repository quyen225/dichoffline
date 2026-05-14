# model/ollama_provider.py
import requests
from typing import List

class OllamaProvider:
    @staticmethod
    def get_models() -> List[str]:
        """Quét danh sách các model Ollama hiện đang được cài đặt local."""
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            if r.status_code == 200:
                return [x['name'] for x in r.json().get('models', [])]
        except Exception:
            pass
        return []

    @staticmethod
    def generate(model: str, text: str) -> str:
        """Gửi văn bản tới Ollama local phục vụ dịch thuật truyện."""
        if not model or "chưa chạy" in model.lower():
            raise ValueError("Chưa cấu hình Model Ollama hợp lệ trên ứng dụng")

        url = "http://localhost:11434/api/generate"
        refined_prompt = (
            "Act as a professional Chinese-to-Vietnamese translator. "
            "Translate the following text into emotional Vietnamese novel style. "
            "Result must be Vietnamese only. No notes. No original text.\n\n"
            f"Text: {text}\n\nVietnamese:"
        )
        payload = {
            "model": model,
            "prompt": refined_prompt,
            "stream": False,
            "options": {"temperature": 0.3, "top_p": 0.9}
        }
        try:
            r = requests.post(url, json=payload, timeout=90)
            r.raise_for_status()
            data = r.json()
            
            result = ""
            if isinstance(data, dict):
                result = data.get("response") or data.get("output") or data.get("results")
                if isinstance(result, list):
                    result = " ".join([str(x) for x in result])
                if isinstance(result, dict):
                    result = result.get("text") or str(result)
            if not result:
                result = data.get("text", "") if isinstance(data, dict) else ""
            
            result = str(result).strip()
            if "Vietnamese:" in result:
                result = result.split("Vietnamese:")[-1].strip()
            return result
        except requests.RequestException as e:
            raise requests.RequestException(f"Lỗi mạng kết nối Ollama: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Lỗi xử lý Ollama: {e}") from e
