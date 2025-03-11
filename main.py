from flask import Flask, render_template_string, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import threading
import time
import os

app = Flask(__name__)

# HTML + CSS للموقع
HTML = """
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>أتمتة تعليقات فيسبوك</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background: #f4f4f4; }
        .container { width: 60%; margin: 50px auto; padding: 20px; background: white; box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1); border-radius: 10px; }
        h1 { color: #333; }
        textarea, input, button { width: 100%; margin: 10px 0; padding: 10px; border: 1px solid #ccc; border-radius: 5px; }
        button { background: #007bff; color: white; border: none; cursor: pointer; }
        button:disabled { background: #ccc; cursor: not-allowed; }
    </style>
</head>
<body>
    <div class="container">
        <h1>أتمتة التعليقات في مجموعات فيسبوك</h1>
        <form id="form">
            <label>روابط الجروبات:</label>
            <textarea id="group_links"></textarea>
            
            <label>التعليقات:</label>
            <textarea id="comments"></textarea>

            <label>الفاصل الزمني (بالثواني):</label>
            <input type="number" id="delay" value="10">

            <button type="submit">بدء النشر</button>
            <button id="stop" type="button" disabled>إيقاف العملية</button>
        </form>
        <p id="status"></p>
    </div>

    <script>
        document.getElementById("form").addEventListener("submit", async function(event) {
            event.preventDefault();
            document.getElementById("stop").disabled = false;
            document.getElementById("status").innerText = "جاري النشر...";
            
            const groupLinks = document.getElementById("group_links").value.split("\\n");
            const comments = document.getElementById("comments").value.split("\\n");
            const delay = document.getElementById("delay").value;

            const response = await fetch("/submit", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ group_links: groupLinks, comments: comments, delay: delay })
            });

            const result = await response.json();
            document.getElementById("status").innerText = result.status;
        });

        document.getElementById("stop").addEventListener("click", async function() {
            await fetch("/stop", { method: "POST" });
            alert("تم إيقاف التنفيذ.");
            document.getElementById("status").innerText = "تم الإيقاف.";
        });
    </script>
</body>
</html>
"""

# خيارات تشغيل Selenium على Render
options = webdriver.ChromeOptions()
options.add_argument("--headless")  
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

stop_flag = False  # للتحكم في الإيقاف

def post_comment(group_url, comments, delay):
    global stop_flag
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.facebook.com/")

    input("سجل الدخول يدويًا واضغط Enter...")  

    driver.get(group_url)
    time.sleep(5)

    posts = driver.find_elements(By.XPATH, '//div[@role="article"]')[:10]  

    for i, post in enumerate(posts):
        if stop_flag:
            break  

        try:
            comment_box = post.find_element(By.XPATH, './/div[@aria-label="اكتب تعليقًا"]')
            comment_box.click()
            time.sleep(2)
            comment_box.send_keys(comments[i % len(comments)])  
            comment_box.send_keys(Keys.RETURN)
            print(f"تم نشر التعليق رقم {i + 1}")
            time.sleep(delay)  
        except Exception as e:
            print("تعذر نشر تعليق:", e)

    print("تم التنفيذ بالكامل.")
    driver.quit()

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/submit', methods=['POST'])
def submit():
    global stop_flag
    stop_flag = False  
    data = request.json
    group_links = data['group_links']
    comments = data['comments']
    delay = int(data['delay'])

    def run_task():
        for group in group_links:
            if stop_flag:
                break
            post_comment(group, comments, delay)

    thread = threading.Thread(target=run_task)
    thread.start()

    return jsonify({"status": "تم بدء النشر..."})

@app.route('/stop', methods=['POST'])
def stop():
    global stop_flag
    stop_flag = True
    return jsonify({"status": "تم الإيقاف"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)