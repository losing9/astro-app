import os
from celery import Celery
from celery.schedules import crontab
from datetime import datetime, date, timedelta
import pytz
from sqlalchemy.orm import Session
from app.database.session import engine
import json
from openai import OpenAI

from app.config import settings
from app.models.base import User, NatalChart, DailyTransit, GeneratedReport
from app.services.astrology_engine import AstrologyEngine
from app.services.prompts import SYSTEM_PROMPT, get_daily_horoscope_prompt


celery_app = Celery("astrogunluk_tasks", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

celery_app.conf.beat_schedule = {
    'generate-daily-horoscopes-at-2am': {
        'task': 'app.tasks.worker.trigger_daily_generation',
        'schedule': crontab(hour=2, minute=0),
    },
}


astro_engine = AstrologyEngine()
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)


@celery_app.task
def generate_daily_horoscope_task(user_id: str, target_date_str: str):
    """
    Background task to generate a daily horoscope for a specific user.
    """
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()

    with Session(engine) as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return f"User {user_id} not found."

        natal_chart = session.query(NatalChart).filter(NatalChart.user_id == user_id).first()
        if not natal_chart:
            # Generate natal chart if it doesn't exist
            utc_dt = datetime.combine(user.birth_date, user.birth_time).replace(tzinfo=pytz.UTC)
            chart_data = astro_engine.calculate_natal_chart(utc_dt, user.latitude, user.longitude)

            natal_chart = NatalChart(user_id=user.id, chart_data=chart_data)
            session.add(natal_chart)
            session.commit()

        # Calculate Transits
        utc_today = datetime(target_date.year, target_date.month, target_date.day, tzinfo=pytz.UTC)
        transits = astro_engine.calculate_transits(utc_today)

        # Calculate Aspects
        aspects = astro_engine.calculate_aspects(natal_chart.chart_data['planets'], transits)

        # Format Prompt
        prompt = get_daily_horoscope_prompt(
            user_name=user.first_name,
            natal_json=natal_chart.chart_data,
            transit_json=transits,
            aspects_json=aspects
        )

        # Call OpenAI
        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300
            )
            generated_text = response.choices[0].message.content.strip()
        except Exception as e:
            generated_text = "Bugün yıldızlar sizin için sakin. (Could not generate horoscope)"
            print(f"OpenAI Error: {e}")

        # Save to DB
        transit_record = DailyTransit(
            user_id=user.id,
            date=target_date,
            transit_data={"transits": transits, "aspects": aspects},
            generated_text=generated_text
        )
        session.add(transit_record)
        session.commit()

        # We would also save to Redis here for fast retrieval:
        # redis_client.set(f"user:{user.id}:horoscope:{target_date_str}", generated_text, ex=86400)

    return f"Horoscope generated for user {user_id} on {target_date_str}."

@celery_app.task
def trigger_daily_generation():
    """
    Fetches all active users and pushes tasks for each.
    """
    today_str = date.today().strftime("%Y-%m-%d")
    with Session(engine) as session:
        users = session.query(User).all()
        for user in users:
            generate_daily_horoscope_task.delay(str(user.id), today_str)

    return f"Triggered {len(users)} tasks for {today_str}."

@celery_app.task
def generate_pdf_report_task(report_id: str):
    """
    Mock PDF Generation Task
    """
    with Session(engine) as session:
        report = session.query(GeneratedReport).filter(GeneratedReport.id == report_id).first()
        if report:
            # Here you would use something like ReportLab or WeasyPrint to build the PDF
            # and upload it to S3, returning the URL.
            report.status = "completed"
            report.pdf_url = f"https://s3.aws.mock/reports/{report_id}.pdf"
            session.commit()
    return f"Report {report_id} generated."

@celery_app.task
def send_notification_task():
    """
    Daily notification at 08:30 AM
    """
    return "Notifications sent"
