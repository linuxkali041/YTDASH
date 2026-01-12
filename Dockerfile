# Python ثابت ومستقر
FROM python:3.10-slim

# منع Python من عمل .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# مكان الشغل
WORKDIR /app

# نسخ requirements الأول (عشان caching)
COPY requirements.txt .

# تحديث pip وتثبيت المكتبات
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# نسخ باقي المشروع
COPY . .

# البورت (Render بيستخدم 10000 افتراضيًا)
EXPOSE 10000

# تشغيل التطبيق
CMD ["sh", "-c", "gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-10000}"]
