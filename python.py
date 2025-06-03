import PyPDF2
import google.generativeai as genai
import json
import os

# --- Cấu hình GenAI API ---
# Thay thế "YOUR_GEMINI_API_KEY" bằng API Key thực của bạn
# Tốt nhất nên lưu API key trong biến môi trường
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set.")
genai.configure(api_key=GEMINI_API_KEY)

# Chọn model phù hợp (ví dụ: gemini-pro cho văn bản)
model = genai.GenerativeModel('gemini-pro')

def extract_text_from_pdf(pdf_path):
    """
    Trích xuất toàn bộ văn bản từ một file PDF.
    """
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() or "" # extract_text có thể trả về None
    except Exception as e:
        print(f"Lỗi khi đọc PDF: {e}")
        return None
    return text

def parse_resume_with_genai(resume_text):
    """
    Gửi văn bản CV đến GenAI API để trích xuất thông tin.
    """
    if not resume_text:
        return {"error": "Không có văn bản để xử lý từ CV."}

    # Prompt Engineering: Hướng dẫn model trích xuất thông tin và định dạng JSON
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
        # Gemini thường trả về markdown code block, cần trích xuất phần JSON
        response_text = response.text.strip()
        
        # Tìm và trích xuất chuỗi JSON giữa các dấu ```json và ```
        start_idx = response_text.find("```json")
        end_idx = response_text.rfind("```")
        
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            json_str = response_text[start_idx + len("```json"):end_idx].strip()
        else:
            # Nếu không tìm thấy markdown, thử phân tích trực tiếp
            json_str = response_text

        # Chuyển chuỗi JSON thành dictionary
        parsed_data = json.loads(json_str)
        return parsed_data
    except json.JSONDecodeError as e:
        print(f"Lỗi khi phân tích JSON từ phản hồi GenAI: {e}")
        print(f"Phản hồi thô: \n{response.text}")
        return {"error": "Không thể phân tích phản hồi GenAI thành JSON."}
    except Exception as e:
        print(f"Lỗi khi gọi GenAI API: {e}")
        return {"error": f"Lỗi GenAI API: {e}"}

# --- Hàm chính ---
if __name__ == "__main__":
    pdf_file_path = "example_cv.pdf" # Đặt tên file CV của bạn ở đây

    # Bước 1: Trích xuất văn bản từ PDF
    cv_text = extract_text_from_pdf(pdf_file_path)

    if cv_text:
        print("Đã trích xuất văn bản từ CV. Đang gửi đến GenAI để phân tích...")
        # Bước 2: Gọi GenAI API để phân tích
        extracted_data = parse_resume_with_genai(cv_text)

        # Bước 3: In kết quả
        if "error" in extracted_data:
            print(f"Có lỗi xảy ra: {extracted_data['error']}")
        else:
            print("\n--- Kết quả Trích xuất CV ---")
            print(json.dumps(extracted_data, indent=2, ensure_ascii=False)) # ensure_ascii=False để hiển thị tiếng Việt
            print("\n--- Kết quả này sẵn sàng cho xử lý tiếp theo ---")
    else:
        print(f"Không thể đọc hoặc trích xuất văn bản từ file PDF: {pdf_file_path}")
