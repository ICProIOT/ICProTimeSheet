from django.conf import settings
import requests
from django.shortcuts import redirect
from django.core.mail import EmailMultiAlternatives
from datetime import datetime

def schedule_api():
    full_url = f"http://127.0.0.1:8001/timeline/emailsend"
    r = requests.get(full_url)
    if r.status_code == 200:
        response = r.json()
        subject = 'Timesheet not yet submitted'
        from_email =  "icproprojects@gmail.com"
        text_content = "This is an important message."
        year,week,fromDate,toDate =  response['year'],response["week"],response["week_start_date"],response["week_end_date"]
        current_dateTime = datetime.now()
        if datetime.today().weekday() ==4:
            for obj in response['result']:
                html_content = reminderMessageBody(obj["first_name"],year,week,fromDate,toDate)
                if current_dateTime.hour == 13:
                    msg = EmailMultiAlternatives(subject, text_content, from_email, [obj["email"]],cc=[obj["_reportingto"]])
                else:
                    msg = EmailMultiAlternatives(subject, text_content, from_email, [obj["email"]])
                msg.attach_alternative(html_content, "text/html")
                msg.send()

# Timesheet submitting reminder 
def reminderMessageBody(name,year,week,fromDate,toDate):
    html="""
            <body>
				<p>Dear %s ,<br><br>
					<h5 style="color: orange;">Timesheet not yet submitted.</h5>
					This email is to inform you that your timesheet for the following week has not yet been submitted.
					<br><br>
					Year:%s , week:%s , Period: %s - %s

					<h5 style="color: orange;">What to do?</h5>
					Please complete and submit these timesheets in TimeEntryBox,at <a href="http://15.207.178.193">http://15.207.178.193</a> 
					
					<h5 style="color: orange;">In case of questions</h5>
					In case this information is not correct,or you have further questions,please contact libinap@icpro.in.
					<br><br>
					Best regards,
                    <br>
					IC Pro solutions Pvt Ltd.
				</p>
      </body>
        """
    return html%(name,year,week,fromDate,toDate)
