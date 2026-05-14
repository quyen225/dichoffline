# model/groq_provider.py
import requests
from typing import List

class GroqProvider:
    @staticmethod
    def fetch_models(api_key: str) -> List[str]:
        from model.config import get_models_by_provider
        return get_models_by_provider("groq")

    @staticmethod
    def generate(api_key: str, model: str, text: str) -> str:
        if not api_key:
            raise ValueError("Hệ thống chưa nhận diện được Groq API Key")
        
        if not model or "/" in model:
            model = "llama-3.3-70b-versatile"

        # ENDPOINT CHÍNH XÁC: Đã sửa từ groq.com thành api.groq.com
        url = "https://" + "api.groq.com" + "/openai/v1/chat/completions"
        
        headers = {
            "Authorization": "Bearer " + str(api_key).strip(),
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Bạn là dịch giả chuyên nghiệp. Chỉ trả về bản dịch tiếng Việt văn phong tiểu thuyết mượt mà, không giải thích gì thêm."},
                {"role": "user", "content": text}
            ],
            "temperature": 0.2,
            "max_tokens": 2000
        }
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            r.raise_for_status()
            data = r.json()
            
            choices = data.get("choices")
            if not choices or not isinstance(choices, list) or len(choices) == 0:
                raise RuntimeError("Cấu trúc phản hồi từ Groq không hợp lệ")
            
            first_choice = choices[0]
            content = first_choice.get("message", {}).get("content") or first_choice.get("text")
            if not content:
                raise RuntimeError("Dữ liệu phản hồi từ Groq Cloud bị trống")
            return str(content).strip()
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            try:
                server_msg = e.response.json().get("error", {}).get("message", "")
                err_detail = f" - {server_msg}" if server_msg else ""
            except:
                err_detail = ""
            raise RuntimeError(f"Groq API lỗi HTTP {status}{err_detail}") from e
        except Exception as e:
            raise RuntimeError(f"Lỗi kết nối Groq: {e}") from e
