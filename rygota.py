import os
from flask import Flask, request
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
import time

app = Flask(__name__)

# 1. Настройка подключения к базе данных
# Мы берем данные из тех переменных, что указали в docker-compose.yml
# Обрати внимание на 'db' в адресе — это имя сервиса из compose
DB_URL = "mysql+mysqlconnector://user:user_password@db/visits_db"

# Создаем "движок" и сессию для работы с БД
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# 2. Описываем структуру нашей таблицы (Модель)
class Visit(Base):
    __tablename__ = 'visits'
    
    # Столбец для IP адреса (будет нашим главным ключом)
    ip_address = Column(String(50), primary_key=True)
    # Столбец для количества заходов
    count = Column(Integer, default=1)

# 3. Функция для автоматического создания таблицы при старте
def init_db():
    # Цикл нужен, чтобы подождать, пока MySQL окончательно "протрезвеет"
    for i in range(10):
        try:
            Base.metadata.create_all(engine)
            print("Таблица успешно создана или уже существует")
            break
        except OperationalError:
            print(f"База еще не готова, ждем... попытка {i+1}")
            time.sleep(3)

init_db()

@app.route('/')
def index():
    # Получаем реальный IP пользователя (который нам передал Nginx)
    user_ip = request.headers.get('X-Real-IP', request.remote_addr)
    
    session = Session()
    try:
        # Ищем запись с таким IP в базе
        visit = session.query(Visit).filter_by(ip_address=user_ip).first()
        
        if visit:
            # Если нашли — увеличиваем счетчик
            visit.count += 1
        else:
            # Если нет — создаем новую запись
            new_visit = Visit(ip_address=user_ip, count=1)
            session.add(new_visit)
        
        session.commit()
        
        # Получаем все записи из базы для отображения
        all_visits = session.query(Visit).all()
        
        # Формируем простую HTML-таблицу
        rows = "".join([f"<tr><td>{v.ip_address}</td><td>{v.count}</td></tr>" for v in all_visits])
        return f"""
            <h1>Журнал посещений</h1>
            <table border='1'>
                <tr><th>IP адрес</th><th>Количество заходов</th></tr>
                {rows}
            </table>
        """
    except Exception as e:
        return f"Ошибка при работе с базой: {e}"
    finally:
        session.close()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)

