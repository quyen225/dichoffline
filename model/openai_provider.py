# model/openai_provider.py
import requests

class OpenAIProvider:
    @staticmethod
    def generate(api_key: str, model: str, text: str) -> str:
        if not api_key:
            raise ValueError("Hệ thống chưa nhận diện được OpenAI API Key")
        if not model:
            model = "gpt-4o-mini"

        # ENDPOINT CHÍNH XÁC: Đã sửa từ openai.com thành api.openai.com
        url = "https://" + "api.openai.com" + "/v1/chat/completions"
        
        headers = {
            "Authorization": "Bearer " + str(api_key).strip(),
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Bạn là dịch giả chuyên nghiệp. Hãy dịch đoạn văn bản sau sang tiếng Việt thuần việt, lưu loát, chuẩn văn phong truyện."},
                {"role": "user", "content": text}
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=40)
            r.raise_for_status()
            data = r.json()
            
            choices = data.get("choices")
            if choices and isinstance(choices, list) and len(choices) > 0:
                first_choice = choices[0]
                content = first_choice.get("message", {}).get("content")
                if content:
                    return str(content).strip()
            raise RuntimeError("Không thể bóc tách cấu trúc dữ liệu OpenAI")
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            raise RuntimeError(f"OpenAI API trả về mã lỗi HTTP: {status}") from e
        except Exception as e:
            raise RuntimeError(f"Lỗi kết nối OpenAI: {e}") from e
