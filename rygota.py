import os
from flask import Flask, request
from sqlalchemy import create_engine, Column, String, Integer, DateTime, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from datetime import datetime
import time

app = Flask(__name__)

# Настройки базы те же
DB_URL = "mysql+mysqlconnector://user:user_password@db/visits_db"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# ОБНОВЛЕННАЯ МОДЕЛЬ: Добавили столбец last_visit
class Visit(Base):
    __tablename__ = 'visits'
    ip_address = Column(String(50), primary_key=True)
    count = Column(Integer, default=1)
    # Тот самый новый столбец
    last_visit = Column(DateTime, default=datetime.now, onupdate=datetime.now)

def init_db():
    for i in range(10):
        try:
            # 1. Сначала создаем то, чего еще нет (базовую структуру)
            Base.metadata.create_all(engine)
            
            # 2. Магия миграции: Проверяем, нужно ли добавить новый столбец
            with engine.connect() as conn:
                # Ищем, есть ли в таблице visits колонка last_visit
                check_column = conn.execute(text("SHOW COLUMNS FROM visits LIKE 'last_visit'")).fetchone()
                
                if not check_column:
                    print("Внимание! Обнаружена старая база. Добавляю столбец last_visit...")
                    conn.execute(text("ALTER TABLE visits ADD COLUMN last_visit DATETIME"))
                    conn.commit()
                    print("Столбец успешно добавлен!")
            break
        except OperationalError:
            print(f"База спит, ждем... попытка {i+1}")
            time.sleep(3)

init_db()

@app.route('/')
def index():
    user_ip = request.headers.get('X-Real-IP', request.remote_addr)
    session = Session()
    try:
        visit = session.query(Visit).filter_by(ip_address=user_ip).first()
        
        # Обновляем данные: и счетчик, и время
        if visit:
            visit.count += 1
            visit.last_visit = datetime.now()
        else:
            new_visit = Visit(ip_address=user_ip, count=1, last_visit=datetime.now())
            session.add(new_visit)
        
        session.commit()
        
        all_visits = session.query(Visit).all()
        
        # Генерируем таблицу с ТРЕМЯ колонками
        rows = ""
        for v in all_visits:
            # Если время еще не записано (для старых записей), выведем "Ранее"
            v_time = v.last_visit.strftime('%Y-%m-%d %H:%M:%S') if v.last_visit else "Ранее"
            rows += f"<tr><td>{v.ip_address}</td><td>{v.count}</td><td>{v_time}</td></tr>"

        return f"""
            <html>
            <head><title>Богатая база</title></head>
            <body>
                <h1>Журнал посещений (Версия 2.0)</h1>
                <table border='1' cellpadding='10'>
                    <tr style='background-color: #eee;'>
                        <th>IP адрес</th>
                        <th>Количество заходов</th>
                        <th>Последний визит (Новое поле!)</th>
                    </tr>
                    {rows}
                </table>
                <p><i>Это обновление произошло автоматически при деплое.</i></p>
            </body>
            </html>
        """
    except Exception as e:
        return f"Ошибка: {e}"
    finally:
        session.close()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)

