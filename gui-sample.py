import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import PyPDF2
import google.generativeai as genai
import json
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER

# --- 1. Cấu hình GenAI API ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    messagebox.showerror("Lỗi Cấu hình",
                         "Biến môi trường GEMINI_API_KEY chưa được thiết lập. Vui lòng thiết lập trước khi chạy ứng dụng.")
    exit()  # Thoát nếu API key không có

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')


# --- 2. Hàm trích xuất văn bản từ PDF (giữ nguyên) ---
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() or ""
    except FileNotFoundError:
        return None, f"Lỗi: Không tìm thấy file PDF tại đường dẫn: {pdf_path}"
    except PyPDF2.errors.PdfReadError:
        return None, f"Lỗi: Không thể đọc file PDF này. File có thể bị hỏng hoặc không phải là PDF hợp lệ: {pdf_path}"
    except Exception as e:
        return None, f"Lỗi không xác định khi đọc PDF: {e}"
    return text, None


# --- 3. Hàm phân tích CV với GenAI (giữ nguyên) ---
def parse_resume_with_genai(resume_text):
    if not resume_text:
        return {"error": "Không có văn bản để xử lý từ CV."}, "Không có văn bản để xử lý từ CV."

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
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        start_idx = response_text.find("```json")
        end_idx = response_text.rfind("```")

        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            json_str = response_text[start_idx + len("```json"):end_idx].strip()
        else:
            json_str = response_text

        parsed_data = json.loads(json_str)
        return parsed_data, None  # Trả về dữ liệu và không có lỗi
    except json.JSONDecodeError as e:
        return {
            "error": "Không thể phân tích phản hồi GenAI thành JSON."}, f"Lỗi JSON: {e}\nPhản hồi thô: {response_text}"
    except Exception as e:
        return {"error": f"Lỗi GenAI API: {e}"}, f"Lỗi GenAI API: {e}"


# --- 4. Hàm xuất JSON ra PDF (sử dụng reportlab, giữ nguyên logic) ---
def export_json_to_pdf(data, output_pdf_path="extracted_cv_report.pdf"):
    doc = SimpleDocTemplate(output_pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Tiêu đề
    title_style = styles['h1']
    title_style.alignment = TA_CENTER
    story.append(Paragraph("Báo Cáo Trích Xuất Thông Tin CV", title_style))
    story.append(Spacer(1, 0.2 * 10 * 2))

    # Tên ứng viên
    story.append(Paragraph(f"<b>Tên ứng viên:</b> {data.get('candidate_name', 'N/A')}", styles['Normal']))
    story.append(Spacer(1, 0.2 * 10))

    # Thông tin liên hệ
    story.append(Paragraph("<b>Thông tin liên hệ:</b>", styles['Normal']))
    contact = data.get('contact_details', {})
    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;Email: {contact.get('email', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;Điện thoại: {contact.get('phone', 'N/A')}", styles['Normal']))
    story.append(Spacer(1, 0.2 * 10))

    # Học vấn
    story.append(Paragraph("<b>Học vấn:</b>", styles['Normal']))
    for edu in data.get('education', []):
        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;- <b>{edu.get('degree', 'N/A')}</b>", styles['Normal']))
        story.append(
            Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Tại: {edu.get('institution', 'N/A')}", styles['Normal']))
        story.append(
            Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Thời gian: {edu.get('dates', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 0.1 * 10))
    if not data.get('education'):
        story.append(Paragraph("&nbsp;&nbsp;&nbsp;N/A", styles['Normal']))
    story.append(Spacer(1, 0.2 * 10))

    # Kinh nghiệm làm việc
    story.append(Paragraph("<b>Kinh nghiệm làm việc:</b>", styles['Normal']))
    for exp in data.get('work_experience', []):
        story.append(
            Paragraph(f"&nbsp;&nbsp;&nbsp;- <b>{exp.get('role', 'N/A')}</b> tại <b>{exp.get('company', 'N/A')}</b>",
                      styles['Normal']))
        story.append(
            Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Thời gian: {exp.get('dates', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 0.1 * 10))
    if not data.get('work_experience'):
        story.append(Paragraph("&nbsp;&nbsp;&nbsp;N/A", styles['Normal']))
    story.append(Spacer(1, 0.2 * 10))

    # Kỹ năng
    story.append(Paragraph("<b>Kỹ năng:</b>", styles['Normal']))
    skills = data.get('skills', [])
    if skills:
        skill_text = ", ".join(skills)
        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;{skill_text}", styles['Normal']))
    else:
        story.append(Paragraph("&nbsp;&nbsp;&nbsp;N/A", styles['Normal']))
    story.append(Spacer(1, 0.2 * 10))

    try:
        doc.build(story)
        return True, None
    except Exception as e:
        return False, f"Lỗi khi tạo PDF: {e}"


# --- Lớp ứng dụng GUI ---
class ResumeParserApp:
    def __init__(self, master):
        self.master = master
        master.title("Ứng dụng Phân tích CV")
        master.geometry("800x600")  # Kích thước cửa sổ mặc định

        # Biến lưu trữ đường dẫn file PDF
        self.pdf_file_path = tk.StringVar()

        # Khung chọn file
        self.file_frame = tk.Frame(master)
        self.file_frame.pack(pady=10)

        self.label_file = tk.Label(self.file_frame, text="Chọn file PDF CV:")
        self.label_file.pack(side=tk.LEFT, padx=5)

        self.entry_file = tk.Entry(self.file_frame, textvariable=self.pdf_file_path, width=50)
        self.entry_file.pack(side=tk.LEFT, padx=5)
        # Thêm sự kiện cho phép dán đường dẫn
        self.entry_file.bind("<Button-3>", self.show_context_menu)  # Right-click to paste

        self.button_browse = tk.Button(self.file_frame, text="Duyệt...", command=self.browse_pdf_file)
        self.button_browse.pack(side=tk.LEFT, padx=5)

        # Nút Export
        self.button_export = tk.Button(master, text="Phân tích & Xuất Báo cáo", command=self.process_and_export,
                                       height=2, bg="lightblue", fg="darkblue")
        self.button_export.pack(pady=10)

        # Khung hiển thị kết quả
        self.result_frame = tk.LabelFrame(master, text="Kết quả trích xuất (JSON)")
        self.result_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

        self.result_text = scrolledtext.ScrolledText(self.result_frame, wrap=tk.WORD, width=70, height=20,
                                                     font=("Courier New", 10))
        self.result_text.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        self.result_text.insert(tk.END, "Kết quả sẽ hiển thị ở đây...")
        self.result_text.config(state=tk.DISABLED)  # Chỉ đọc

    def browse_pdf_file(self):
        """Mở hộp thoại chọn file PDF."""
        file_selected = filedialog.askopenfilename(
            title="Chọn file PDF CV",
            filetypes=[("PDF files", "*.pdf")]
        )
        if file_selected:
            self.pdf_file_path.set(file_selected)

    def show_context_menu(self, event):
        """Hiển thị menu ngữ cảnh (paste) cho Entry."""
        context_menu = tk.Menu(self.master, tearoff=0)
        context_menu.add_command(label="Dán", command=lambda: self.entry_file.event_generate("<<Paste>>"))
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def update_result_display(self, message, is_error=False):
        """Cập nhật vùng hiển thị kết quả."""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, message)
        if is_error:
            self.result_text.config(fg="red")
        else:
            self.result_text.config(fg="black")
        self.result_text.config(state=tk.DISABLED)

    def process_and_export(self):
        """Xử lý toàn bộ quá trình: đọc PDF, phân tích, xuất PDF."""
        pdf_path = self.pdf_file_path.get()
        if not pdf_path:
            messagebox.showwarning("Thiếu file", "Vui lòng chọn hoặc nhập đường dẫn đến file PDF CV.")
            return

        self.update_result_display("Đang xử lý... Vui lòng đợi.")
        self.master.update_idletasks()  # Cập nhật giao diện ngay lập tức

        # 1. Trích xuất văn bản từ PDF
        cv_text, pdf_error = extract_text_from_pdf(pdf_path)
        if pdf_error:
            messagebox.showerror("Lỗi đọc PDF", pdf_error)
            self.update_result_display(f"Lỗi đọc PDF: {pdf_error}", is_error=True)
            return

        # 2. Phân tích với GenAI
        extracted_data, genai_error = parse_resume_with_genai(cv_text)
        if genai_error:
            messagebox.showerror("Lỗi phân tích AI", genai_error)
            self.update_result_display(f"Lỗi phân tích AI: {genai_error}", is_error=True)
            return

        if "error" in extracted_data:
            messagebox.showerror("Lỗi Phân tích", f"Lỗi từ GenAI: {extracted_data['error']}")
            self.update_result_display(f"Lỗi từ GenAI: {extracted_data['error']}", is_error=True)
            return

        # Hiển thị JSON lên GUI
        json_output = json.dumps(extracted_data, indent=2, ensure_ascii=False)
        self.update_result_display(json_output)

        # 3. Xuất ra PDF báo cáo
        # Lấy tên file gốc để đặt tên file báo cáo
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_report_pdf_name = f"{base_name}_extracted_report.pdf"

        # Hỏi người dùng nơi lưu file báo cáo
        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=output_report_pdf_name,
            title="Lưu báo cáo trích xuất CV"
        )

        if not save_path:  # Người dùng hủy
            messagebox.showinfo("Thông báo", "Người dùng đã hủy lưu file báo cáo.")
            self.update_result_display(json_output + "\n\nNgười dùng đã hủy lưu file báo cáo.")
            return

        export_success, export_error = export_json_to_pdf(extracted_data, save_path)

        if export_success:
            messagebox.showinfo("Thành công", f"Đã trích xuất và xuất báo cáo PDF thành công tới:\n{save_path}")
            self.update_result_display(json_output + f"\n\nĐã xuất báo cáo PDF thành công tới:\n{save_path}")
        else:
            messagebox.showerror("Lỗi xuất PDF", export_error)
            self.update_result_display(json_output + f"\n\nLỗi khi xuất báo cáo PDF: {export_error}", is_error=True)


# --- Khởi tạo và chạy ứng dụng ---
if __name__ == "__main__":
    root = tk.Tk()
    app = ResumeParserApp(root)
    root.mainloop()
