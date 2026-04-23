from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    # Вот этот текст мы будем менять в Гитхабе, чтобы проверить обновление
    return "<h1>Привет! Я работаю на отьебись, как и все здесь, а еще и автоматичесски.</h1>"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)

