from django.core.mail import EmailMessage
import threading
from email.mime.image import MIMEImage
from django.contrib.staticfiles import finders
from functools import lru_cache


class EmailThread(threading.Thread):

    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        try:
            print("sending...")
            self.email.send()
        except Exception as e:
            print(e)


@lru_cache()
def img_data_cid(img_path, img_cid):
    with open(finders.find(img_path), 'rb') as f:
        img_data = f.read()
    img = MIMEImage(img_data)
    img.add_header('Content-ID', img_cid)
    return img


class Util:
    @staticmethod
    def send_email(data, html=False, img=None):
        email = EmailMessage(
            subject=data['email_subject'], body=data['email_body'], to=[data['to_email']])
        if html:
            email.content_subtype='html'
        if img:
            email.attach(img_data_cid(img[0], img[1]))
        EmailThread(email).start()
