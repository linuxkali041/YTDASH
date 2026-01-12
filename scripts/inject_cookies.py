
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models.settings import AppSetting

# The cookies provided by the user
COOKIES = """# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file! Do not edit.

.youtube.com	TRUE	/	TRUE	1774807367	__Secure-YENID	10.YTE=BZMVjKnSFrFSm3MVhxEyd8Zb8xx_v1xFE4RFrDEi0DI3pPvwZ5sy9go9w8S6LlD65RCruyx5fw2nrViNKlVxARX46puBn1_lbyI6Ep3Zeiivca1FXCMnqKxCI6WzWO93o-zsp_OqMRii2T2DYLfh3S3TWIl85xZRYk_awjPXMM5UjqHC5IUkVr1WWSeYT_uRZea9kd8hMeRnPN8iQeG8cA9awVOrMhNCNr21rDptMWA64qvwSYsqjEoQcjb6sIYd_UuX0E1zrVxy5MjHIj_uM1MbBAz9n7EQ_wm1lPMY865sk0pkn4qCizhjFovrglVQLhbOV7IbjW-HSWy0dS4aKQ
.youtube.com	TRUE	/	FALSE	1783717639	HSID	AUBvA-kdDT8wIQlin
.youtube.com	TRUE	/	TRUE	1783717639	SSID	A1cFZdtlmxUIwFgjK
.youtube.com	TRUE	/	FALSE	1783717639	APISID	TfWRkIQTGDlpjb8j/AxOR7qOlFoFKP3TS6
.youtube.com	TRUE	/	TRUE	1783717639	SAPISID	aReoBhiPwqn8bTqm/Ag0zed6kh6BdbB6qR
.youtube.com	TRUE	/	TRUE	1783717639	__Secure-1PAPISID	aReoBhiPwqn8bTqm/Ag0zed6kh6BdbB6qR
.youtube.com	TRUE	/	TRUE	1783717639	__Secure-3PAPISID	aReoBhiPwqn8bTqm/Ag0zed6kh6BdbB6qR
www.youtube.com	FALSE	/	FALSE	1780132118	_bl_uid	20mbhi01m6hx6Lf9vxpR6j350gb8
.youtube.com	TRUE	/	TRUE	1781992324	LOGIN_INFO	AFmmF2swRQIhAKzvaK3OlT7u6WEP_2bz2c-hP3Z26bQ5QN6WefUtL4tkAiA64Y9FJi6NVN63uH3n8ocXDD-YnU40rjQhOo4KdoG0-A:QUQ3MjNmd2RoYmNsZzdyV1hIN19hZUtaN3RNTVo1Zk1Jb1hHdl95SjhSOUZBTDJRcV8zWFMxTGFrMlpyR0I1M3VUSkN3NmwzVDc2NURua1NpckNoNk5MbDcxc1Fldl9YYmNjLWRlOFROeTl6andwNHB0ZWpwTi1UaXdSU01YOVd5LWpoeUxxcUJvSWx6X1owNTR5cHl6VFI4Sms2ekxpT193
.youtube.com	TRUE	/	TRUE	1783754542	PREF	tz=Africa.Cairo&f6=40000000&f5=20000&f7=100
.youtube.com	TRUE	/	FALSE	1783717639	SID	g.a0005QhEBB2GOIi4mDVwKyolyibd3VUiHmWdH7vYVkaLWaxAIPDoNsg9li1UvySnLc4VUnylzAACgYKATYSARISFQHGX2MiSDYwCvKamuNO4oZLvBZMBBoVAUF8yKoymYGXS9gcSNXOf8Vv_-e_0076
.youtube.com	TRUE	/	TRUE	1783717639	__Secure-1PSID	g.a0005QhEBB2GOIi4mDVwKyolyibd3VUiHmWdH7vYVkaLWaxAIPDow4L-LCNqPm4E-xENEhCBtAACgYKAdESARISFQHGX2Mibqg1kq8VNdpe95IaRftnqBoVAUF8yKoDB1CiDYosllWrYpz2LVkt0076
.youtube.com	TRUE	/	TRUE	1783717639	__Secure-3PSID	g.a0005QhEBB2GOIi4mDVwKyolyibd3VUiHmWdH7vYVkaLWaxAIPDo317wLYTc3wnyv7y-N34phwACgYKAdMSARISFQHGX2MiuyeHG2gYzcDa5ZTkC96lThoVAUF8yKpR3WSKH-bEse7G6RCBDl580076
.youtube.com	TRUE	/	TRUE	0	wide	1
.youtube.com	TRUE	/	TRUE	1783717639	__Secure-1PSIDTS	sidts-CjUB7I_69GFHv6e-3FX5JJ4eESxBkokL_OIz-Po5wLa2u0sQjYzjBL79a_g_Eo0-bz0XT8uM4hAA
.youtube.com	TRUE	/	TRUE	1783717639	__Secure-3PSIDTS	sidts-CjUB7I_69GFHv6e-3FX5JJ4eESxBkokL_OIz-Po5wLa2u0sQjYzjBL79a_g_Eo0-bz0XT8uM4hAA
.youtube.com	TRUE	/	FALSE	1783754545	SIDCC	AKEyXzVtoc4oGCwRO0JGBJ5egqpGb8Wxfew2DpRHFf5RgbtcB_fQ1wcg7W3WuLzxbFHWNpH7aiw
.youtube.com	TRUE	/	TRUE	1783754545	__Secure-1PSIDCC	AKEyXzUuNoV0rLCdSdps_zgr02br-ULCuNsWEoONcwBRfmlzMpVORzmbu22J3HNKABGMg8da0H0
.youtube.com	TRUE	/	TRUE	1783754545	__Secure-3PSIDCC	AKEyXzXJApLmNNOZU5rfMb0dn3ZWarROvk-LjubeY5m08fvcE2n_XracmPhRggwGCOpqRBnWbA
.youtube.com	TRUE	/	TRUE	1783754540	VISITOR_INFO1_LIVE	ERU1iG1f-pw
.youtube.com	TRUE	/	TRUE	1783754540	VISITOR_PRIVACY_METADATA	CgJJUhIEGgAgEg%3D%3D
.youtube.com	TRUE	/	TRUE	0	YSC	ddut_PEGsHo
.youtube.com	TRUE	/	TRUE	1783708597	__Secure-ROLLOUT_TOKEN	CJfkzYfniumzThCDhLb_iIGQAxjZguLykISSAw%3D%3D"""

def inject_cookies():
    db = SessionLocal()
    try:
        setting = db.query(AppSetting).filter(AppSetting.key == 'youtube_cookies').first()
        if setting:
            print("Found 'youtube_cookies' setting. Updating...")
            setting.value = COOKIES
            setting.value_type = 'text' # Ensure type is text
            db.commit()
            print("Successfully updated cookies.")
        else:
            print("Setting 'youtube_cookies' not found. Creating...")
            new_setting = AppSetting(
                key='youtube_cookies',
                value=COOKIES,
                category='download',
                description='Global YouTube Cookies (Netscape Format)',
                value_type='text'
            )
            db.add(new_setting)
            db.commit()
            print("Successfully created and updated cookies.")
    except Exception as e:
        print(f"Error updating cookies: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    inject_cookies()
