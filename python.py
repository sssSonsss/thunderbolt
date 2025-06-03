from google import genai

client = genai.Client(api_key="AIzaSyDTzn0avrKlIf8ch3B6ICc83wmaHJ66xu4")

response = client.models.generate_content(
    model="gemini-2.0-flash", contents="Who is Post Malone"
)
print(response.text)
