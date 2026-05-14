# model/azure_provider.py
import requests

class AzureProvider:
    @staticmethod
    def generate(api_key: str, endpoint: str, region: str, text: str) -> str:
        """Thực hiện lệnh gọi API dịch thuật văn bản qua Azure Translator (v3)."""
        if not api_key or not endpoint:
            raise ValueError("Thông tin xác thực Azure Key hoặc Endpoint đang bị thiếu")
        
        base = endpoint.rstrip('/')
        if "/translator/text/v3.0" not in base:
            url = f"{base}/translator/text/v3.0/translate"
        else:
            url = base
            
        headers = {
            'Ocp-Apim-Subscription-Key': api_key.strip(),
            'Content-type': 'application/json'
        }
        if region and region.strip():
            headers['Ocp-Apim-Subscription-Region'] = region.strip()

        params = {'api-version': '3.0', 'to': 'vi'}
        body = [{'text': text}]
        try:
            r = requests.post(url, params=params, headers=headers, json=body, timeout=25)
            r.raise_for_status()
            data = r.json()
            
            if isinstance(data, list) and len(data) > 0:
                translations = data[0].get('translations')
                if translations and len(translations) > 0:
                    return translations[0].get('text', '').strip()
            raise RuntimeError(f"Azure trả về dữ liệu cấu trúc không mong muốn: {data}")
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            raise RuntimeError(f"Azure API báo lỗi HTTP: {status}") from e
        except Exception as e:
            raise RuntimeError(f"Azure Translator Error: {e}") from e
