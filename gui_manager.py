# gui_manager.py
import customtkinter as ctk
import os
import json
from dotenv import set_key, load_dotenv
from tkinter import messagebox

# Đọc cấu trúc danh sách model lưu trong thư mục model/
from model.config import get_models_by_provider

class ApiManagerWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Quản lý API & Trạng thái Pool Keys")
        self.geometry("1100x750")  # Mở rộng kích thước để chứa bảng trạng thái keys
        self.attributes("-topmost", True)
        
        load_dotenv(override=True)
        
        # Cấu trúc lưu danh sách Azure Keys định dạng: [{"key": "abc...", "status": "LIVE"}, ...]
        self.azure_pool_data = []
        self.load_azure_pool_config()
            
        self.prev_groq_model = os.getenv("GROQ_MODEL") or "llama-3.3-70b-versatile"
        self.setup_ui()

    def load_azure_pool_config(self):
        """Nạp cấu hình Pool Keys Azure từ tệp cấu hình hệ thống"""
        try:
            keys_raw = os.getenv("AZURE_KEYS_LIST")
            if keys_raw:
                parsed = json.loads(keys_raw)
                # Chuẩn hóa cấu trúc cũ nếu chỉ chứa chuỗi ký tự thô
                if parsed and isinstance(parsed[0], str):
                    self.azure_pool_data = [{"key": k, "status": "LIVE"} for k in parsed]
                else:
                    self.azure_pool_data = parsed
            else:
                self.azure_pool_data = []
        except:
            self.azure_pool_data = []

    def save_azure_pool_config(self):
        """Lưu cấu hình Pool Keys Azure vào tệp .env"""
        set_key(".env", "AZURE_KEYS_LIST", json.dumps(self.azure_pool_data))
        # Đồng bộ danh sách hiển thị trên OptionMenu giao diện
        dropdown_vals = [x["key"] for x in self.azure_pool_data] if self.azure_pool_data else ["(Trống)"]
        self.key_dropdown.configure(values=dropdown_vals)
        self.key_dropdown.set(dropdown_vals[0])
        self.refresh_key_status_table()

    def setup_ui(self):
        # --- KHỐI CẤU HÌNH AZURE ---
        azure_group = ctk.CTkLabel(self, text="◆ PHÂN HỆ CẤU HÌNH MICROSOFT AZURE TRANSLATOR", font=("Arial", 13, "bold"), text_color="#3498DB")
        azure_group.pack(anchor="w", padx=20, pady=5)

        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row1, text="Azure Endpoint:").pack(side="left")
        self.ent_endpoint = ctk.CTkEntry(row1, width=400)
        self.ent_endpoint.insert(0, os.getenv("AZURE_ENDPOINT") or "")
        self.ent_endpoint.pack(side="left", padx=10)
        
        ctk.CTkLabel(row1, text="Region:").pack(side="left")
        self.combo_region = ctk.CTkComboBox(row1, values=["southeastasia", "eastus", "westus"], width=150)
        self.combo_region.set(os.getenv("AZURE_REGION") or "southeastasia")
        self.combo_region.pack(side="left", padx=10)

        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row2, text="Azure Key Chính:").pack(side="left")
        self.ent_main_key = ctk.CTkEntry(row2, width=435, show="*")
        self.ent_main_key.insert(0, os.getenv("AZURE_MAIN_KEY") or "")
        self.ent_main_key.pack(side="left", padx=10)
        ctk.CTkButton(row2, text="Validate Azure", width=150, 
                      command=lambda: self.master.validate_azure(self.ent_main_key, self.ent_endpoint, self.combo_region)).pack(side="left", padx=5)

        # --- BẢNG ĐIỀU KHIỂN & THEO DÕI POOL KEYS ĐA LUỒNG ---
        row3 = ctk.CTkFrame(self, fg_color="transparent")
        row3.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row3, text="Quản lý Pool Keys:").pack(side="left")
        vals = [x["key"] for x in self.azure_pool_data] if self.azure_pool_data else ["(Trống)"]
        self.key_dropdown = ctk.CTkOptionMenu(row3, values=vals, width=400)
        self.key_dropdown.pack(side="left", padx=10)
        ctk.CTkButton(row3, text="Thêm Vào Pool", width=110, fg_color="#2980B9", command=self.add_key_logic).pack(side="left", padx=5)

        row4 = ctk.CTkFrame(self, fg_color="transparent")
        row4.pack(fill="x", padx=20, pady=5)
        self.ent_new_key = ctk.CTkEntry(row4, placeholder_text="Dán chuỗi ký tự Key mới vào đây để thêm...", width=440)
        self.ent_new_key.pack(side="left", padx=125)
        ctk.CTkButton(row4, text="Xóa Khỏi Pool", width=110, fg_color="#C0392B", command=self.delete_key_logic).pack(side="left", padx=5)
        ctk.CTkButton(row4, text="Kích Hoạt Key", width=110, fg_color="#27AE60", command=self.use_key_logic).pack(side="left", padx=5)

        # --- BẢNG THEO DÕI TRẠNG THÁI SỐNG / CHẾT CỦA CÁC LUỒNG ---
        table_frame = ctk.CTkFrame(self, fg_color="#1A1A1A", height=150)
        table_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(table_frame, text="DANH SÁCH GIÁM SÁT TRẠNG THÁI KEY ROTATION POOL", font=("Arial", 11, "bold"), text_color="#E74C3C").pack(pady=2)
        
        self.table_textbox = ctk.CTkTextbox(table_frame, height=120, fg_color="black", text_color="#00FF00", font=("Consolas", 12))
        self.table_textbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.refresh_key_status_table()

        # --- KHỐI CẤU HÌNH ONLINE PROVIDERS VÀ ĐỌC FILE NỘI BỘ ---
        online_group = ctk.CTkLabel(self, text="◆ PHÂN HỆ CẤU HÌNH ONLINE PROVIDERS", font=("Arial", 13, "bold"), text_color="#E67E22")
        online_group.pack(anchor="w", padx=20, pady=10)

        # Cấu hình OpenAI Key
        row_openai = ctk.CTkFrame(self, fg_color="transparent")
        row_openai.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row_openai, text="OpenAI Key:   ", width=100, anchor="w").pack(side="left")
        self.ent_openai_key = ctk.CTkEntry(row_openai, width=440, show="*")
        self.ent_openai_key.insert(0, os.getenv("OPENAI_KEY") or "")
        self.ent_openai_key.pack(side="left", padx=10)
        ctk.CTkButton(row_openai, text="Validate OpenAI", width=150,
                      command=lambda: self.master.validate_ai("OpenAI", "OPENAI_KEY", self.ent_openai_key)).pack(side="left", padx=5)

        # Cấu hình Groq Key
        row_groq = ctk.CTkFrame(self, fg_color="transparent")
        row_groq.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row_groq, text="Groq Key:     ", width=100, anchor="w").pack(side="left")
        self.ent_groq_key = ctk.CTkEntry(row_groq, width=440, show="*")
        self.ent_groq_key.insert(0, os.getenv("GROQ_KEY") or "")
        self.ent_groq_key.pack(side="left", padx=10)
        ctk.CTkButton(row_groq, text="Validate Groq", width=150,
                      command=lambda: self.master.validate_ai("Groq Cloud", "GROQ_KEY", self.ent_groq_key)).pack(side="left", padx=5)

        # Lựa chọn Model của hệ thống Groq (Đọc trực tiếp tệp cấu hình hệ thống)
        row_groq_model = ctk.CTkFrame(self, fg_color="transparent")
        row_groq_model.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row_groq_model, text="Groq Model Selector:", width=130, anchor="w").pack(side="left")
        
        # Đọc cấu trúc danh sách model lưu trong thư mục model/config.py
        groq_models_list = get_models_by_provider("groq") [1]
        if not groq_models_list:
            groq_models_list = [self.prev_groq_model]

        saved_model = os.getenv("GROQ_MODEL") or self.prev_groq_model
        if saved_model not in groq_models_list:
            saved_model = groq_models_list[0]

        self.groq_model_selector = ctk.CTkOptionMenu(
            row_groq_model, 
            values=groq_models_list, 
            width=410,
            command=self.confirm_model_change
        )
        self.groq_model_selector.set(saved_model)
        self.groq_model_selector.pack(side="left", padx=10)

    # ================= LOGIC XÁC NHẬN MODEL =================

    def confirm_model_change(self, new_model):
        msg = f"Bạn có chắc chắn muốn chuyển sang Model:\n▶ {new_model} không?"
        if messagebox.askyesno("Xác nhận thay đổi", msg):
            set_key(".env", "GROQ_MODEL", new_model)
            os.environ["GROQ_MODEL"] = new_model
            self.prev_groq_model = new_model
            self.master.log(f"✅ Đã xác nhận đổi model Groq: {new_model}")
        else:
            self.groq_model_selector.set(self.prev_groq_model)
            self.master.log("⚠️ Đã hủy thay đổi model.")

    def update_groq_dropdown(self, models):
        """Hàm đồng bộ danh sách khi bốc tách thành công qua mạng API"""
        if hasattr(self, 'groq_model_selector'):
            self.groq_model_selector.configure(command=None)
            self.groq_model_selector.configure(values=models)
            current = os.getenv("GROQ_MODEL")
            if current in models:
                self.groq_model_selector.set(current)
            else:
                self.groq_model_selector.set(models[0])
            self.groq_model_selector.configure(command=self.confirm_model_change)

    # ================= LOGIC THEO DÕI POOL VÀ BIẾN MÔI TRƯỜNG TRANSLATE =================

    def refresh_key_status_table(self):
        """Vẽ lại bảng giám sát trạng thái LIVE/DEAD của hệ thống đa luồng"""
        self.table_textbox.configure(state="normal")
        self.table_textbox.delete("1.0", "end")
        if not self.azure_pool_data:
            self.table_textbox.insert("end", "[Hệ thống] Hiện tại chưa có khóa Key nào được nạp vào Pool lưu trữ.")
        else:
            for idx, item in enumerate(self.azure_pool_data, start=1):
                k_masked = f"{item['key'][:15]}...{item['key'][-8:]}"
                status = item.get("status", "LIVE")
                color_tag = "● STT"
                self.table_textbox.insert("end", f"[{idx:02d}] Key: {k_masked} | Trạng thái: {status}\n")
        self.table_textbox.configure(state="disabled")

    def add_key_logic(self):
        nk = self.ent_new_key.get().strip()
        if nk:
            existing_keys = [x["key"] for x in self.azure_pool_data]
            if nk not in existing_keys:
                self.azure_pool_data.append({"key": nk, "status": "LIVE"})
                self.save_azure_pool_config()
                self.ent_new_key.delete(0, 'end')
                self.master.log("✅ Đã lưu và thêm Key Azure mới dạng LIVE vào Pool.")
            else:
                messagebox.showwarning("Trùng lặp", "Key này đã tồn tại trong Pool quản lý!")
        else:
            messagebox.showwarning("Trống", "Vui lòng dán chuỗi ký tự khóa cần nạp!")

    def delete_key_logic(self):
        sel = self.key_dropdown.get()
        target = [x for x in self.azure_pool_data if x["key"] == sel]
        if target:
            self.azure_pool_data.remove(target[0])
            self.save_azure_pool_config()
            self.master.log("🗑️ Đã xóa bỏ Key Azure khỏi danh sách Pool.")
        else:
            messagebox.showwarning("Lỗi", "Không tìm thấy dữ liệu khóa cần cấu hình xóa!")

    def use_key_logic(self):
        sel = self.key_dropdown.get()
        if sel and sel != "(Trống)":
            self.ent_main_key.delete(0, 'end')
            self.ent_main_key.insert(0, sel)
            set_key(".env", "AZURE_MAIN_KEY", sel)
            os.environ["AZURE_MAIN_KEY"] = sel
            self.master.log(f"🔑 Đã kích hoạt nạp Key mục tiêu lên cổng chính: {sel[:12]}...")
            messagebox.showinfo("Thành công", "Đã đặt khóa được chọn làm Azure Key hoạt động chính!")
