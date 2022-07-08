import email_conf
import math,statistics
import time,json

from boltiot import Email,Bolt,Sms

minimum_limit = 0
maximum_limit = 50

def compute_bounds(history_data,frame_size,factor):
	if len(history_data)<frame_size :
		return None
	if len(history_data) > frame_size :
		del history_data[0: len(history_data)-frame_size]

	Mn = statistics.mean(history_data)

	variance = 0
	for data in history_data:
		variance += math.pow((data-Mn),2)

	Zn = factor * math.sqrt(variance / frame_size)
	High_bound = history_data[frame_size-1]+Zn
	Low_bound =  history_data[frame_size-1] - Zn
	return [High_bound,Low_bound]


mybolt = Bolt(email_conf.API_KEY, email_conf.DEVICE_ID)
mailer = Email(email_conf.MAILGUN_API_KEY,email_conf.SANDBOX_URL, email_conf.SENDER_EMAIL, email_conf.RECIPIENT_EMAIL)
sms = Sms(email_conf.SID, email_conf.AUTH_TOKEN, email_conf.TO_NUMBER, email_conf.FROM_NUMBER)
history_data = []

while True:
# part E and F
#	print("Reading sensor value")
#	response=mybolt.analogRead('A0')
#	data = json.loads(response)
#	sensor_value = (100*int(data['value']))/1024
#	print("Sensor value is :" + str(sensor_value))
#	try:
#		sensor_value= (100*int(data['value']))/1024
#		if(sensor_value > maximum_limit or sensor_value < minimum_limit):
#			print("Making request to Mailgun to send an email")
#			response = mailer.send_email("Alert","The current system temperature is:"+str(sensor_value))
#			response_text = json.loads(response.text)
#			print("Response received from mailgun is:"+str(response_text))
#	except Exception as e:
#		print ("Error occured below are details:")
#		print (e)
#	time.sleep(10) 

    response = mybolt.analogRead('A0')
    data = json.loads(response)
    if data['success'] != 1:
        print("There was an error while retriving the data.")
        print("This is the error:"+data['value'])
        time.sleep(10)
        continue

    print ("This is the value "+str(100*int(data['value'])/1024))
    sensor_value=0
    try:
        sensor_value = (100*int(data['value']))/1024
    except e:
        print("There was an error while parsing the response: ",e)
        continue

    bound = compute_bounds(history_data,email_conf.FRAME_SIZE,email_conf.MUL_FACTOR)
    if not bound:
        required_data_count=email_conf.FRAME_SIZE-len(history_data)
        print("Not enough data to compute Z-score. Need ",required_data_count," more data points")
        history_data.append(int(data['value']))
        time.sleep(10)
        continue

    try:
        if(sensor_value > maximum_limit or sensor_value < minimum_limit):
             print("Alarm On")
             mybolt.digitalWrite('0','HIGH')
             time.sleep(10)
             mybolt.digitalWrite('0','LOW')
             print("Making request to mailgun to send an email")
             response = mailer.send_email("Alert","The current system temeperature is:"+ str(sensor_value))
             response_text = json.loads(response.text)
             print("Response received from mailgun is:",str(response_text))
             print("Making request to twilio to send message")
             response = sms.send_sms("Temperature crossed critical temperature")
             print("Response received from twilio: "+str(response))
             print("Status of SMS at twilio is:"+str(response.status))
    except Exception as e:
          print("Error occured below are details:")
          print(e)

    try:
        if sensor_value > bound[0]:
            print ("The temperature increased suddenly. Sending an Email.")
            response = mailer.send_email("Alert","Someone has opened fridge door"+"The current temperature is :"+str(sensor_value))
            response_text = json.loads(response.text)
            print("Response received from mailgun is: "+str(response_text))
      #  elif sensor_value < bound[1]:
      #      print ("The temperature decreased suddenly. Sending an Email.")
      #      response = mailer.send_email("Alert","Someone has opened fridge door"+"The current temperature is :"+str(sensor_value))
      #      response_text = json.loads(response.text)
        history_data.append(sensor_value);
    except Exception as e:
        print ("Error",e)
    time.sleep(10) 