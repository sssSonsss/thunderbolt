import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import PyPDF2
import os
import json
from google import genai


def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        messagebox.showerror("PDF Error", f"Lỗi khi đọc PDF: {e}")
        return None


def analyze_resume(resume_text):
    if not resume_text:
        return {"error": "Không có văn bản để xử lý từ CV."}

    prompt = f"""
    Bạn là một trợ lý phân tích CV chuyên nghiệp. Hãy trích xuất các thông tin sau từ CV được cung cấp:
    - Tên đầy đủ của ứng viên
    - Thông tin liên hệ: email, số điện thoại
    - Các mục học vấn: bằng cấp, tên trường/tổ chức, thời gian học
    - Danh sách các kỹ năng
    - Các mục kinh nghiệm làm việc: tên công ty, vị trí/vai trò, thời gian làm việc

    Vui lòng trả về kết quả dưới định dạng JSON sau:

    ```json
    {{
      "candidate_name": "Tên ứng viên",
      "contact_details": {{
        "email": "email@example.com",
        "phone": "+84 123 456 789"
      }},
      "education": [
        {{
          "degree": "Bằng cấp",
          "institution": "Tên trường",
          "dates": "Thời gian học"
        }}
      ],
      "skills": [
        "Kỹ năng 1",
        "Kỹ năng 2"
      ],
      "work_experience": [
        {{
          "company": "Tên công ty",
          "role": "Vị trí",
          "dates": "Thời gian làm việc"
        }}
      ]
    }}
    ```

    Đây là văn bản CV:
    ---
    {resume_text}
    ---
    """

    try:
        client = genai.Client(api_key="AIzaSyDTzn0avrKlIf8ch3B6ICc83wmaHJ66xu4")
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt
        )

        json_start = response.text.find('{')
        json_text = response.text[json_start:].strip("`")
        return json.loads(json_text)
    except Exception as e:
        return {"error": f"Lỗi khi gọi Gemini API: {e}"}


def choose_file():
    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if file_path:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, file_path)


def run_analysis():
    file_path = entry_path.get()
    if not file_path.endswith(".pdf"):
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn một file PDF hợp lệ.")
        return

    result_textbox.delete(1.0, tk.END)
    text = extract_text_from_pdf(file_path)
    if not text:
        return

    result_textbox.insert(tk.END, "Đang phân tích CV...\n")
    root.update()

    result = analyze_resume(text)
    if "error" in result:
        result_textbox.insert(tk.END, f"Lỗi: {result['error']}")
    else:
        result_textbox.insert(tk.END, json.dumps(result, indent=2, ensure_ascii=False))


# GUI Setup
root = tk.Tk()
root.title("CV Analyzer - Gemini AI")
root.geometry("700x600")

frame = tk.Frame(root)
frame.pack(pady=10)

entry_path = tk.Entry(frame, width=50)
entry_path.pack(side=tk.LEFT, padx=5)

btn_browse = tk.Button(frame, text="Chọn File", command=choose_file)
btn_browse.pack(side=tk.LEFT)

btn_run = tk.Button(root, text="Phân Tích CV", command=run_analysis)
btn_run.pack(pady=10)

result_textbox = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=30)
result_textbox.pack(padx=10, pady=10)

root.mainloop()
