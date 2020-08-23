import cv2
import time
import os
import requests
import json
import urllib.request
import glob


def checkTelegramConnections(host='https://telegram.org/'):
    try:
        urllib.request.urlopen(host)
        return True
    except:
        return False


def getIP():
    url = "https://www.ifconfig.me/"
    resp = requests.get(url)
    if resp.status_code != 200:
        return "NaN"
    else:
        return resp.content.decode("utf-8")


def sendImage(filename, prevFile, sendTime, counter):
    if preference["telegram"]["send"] and checkTelegramConnections():
        if sendTime == "null" or round(int(sendTime)) + int(preference["telegram"]["sendDelay"]) <= round(
                int(time.time())):
            url = f'https://api.telegram.org/bot{preference["telegram"]["TOKEN"]}/sendPhoto'
            os.chdir(dir + "/" + preference["saveFolder"])
            files = {'photo': open(filename, 'rb')}
            if preference["telegram"]["caption"]["use"]:
                cap = str(preference["telegram"]["caption"]["format"])
                cap = cap.replace("%filename%", str(filename))
                cap = cap.replace("%counter%", str(counter))
                try:
                    cap = cap.replace("%host%", str(os.environ["COMPUTERNAME"]))
                except:
                    pass
                try:
                    cap = cap.replace("%user%", str(os.getlogin()))
                except:
                    pass
                try:
                    cap = cap.replace("%ip%", str(getIP()))
                except:
                    pass
                data = {'chat_id': preference["telegram"]["chatID"], 'caption': cap,
                        'disable_notification': preference["telegram"]["silentSend"]}
            else:
                data = {'chat_id': preference["telegram"]["chatID"],
                        'disable_notification': preference["telegram"]["silentSend"]}
            r = requests.post(url, files=files, data=data)
            if r.status_code == 200:
                counter += 1
            if preference["debug"]:
                print(r.status_code, r.reason, r.content)
            sendTime = time.time()
            if r.status_code == 200 and prevFile != "null" and preference["telegram"]["deleteAfterSend"]:
                try:
                    os.remove(prevFile)
                    if preference["debug"]:
                        print(f'{filename} successful removed!')
                except:
                    if preference["debug"]:
                        print(f'Cannot remove {filename}')

    return sendTime, filename, counter


if __name__ == '__main__':
    sendCount = 1
    lastSendTime = "null"
    lastFile = "null"
    with open('config.json') as json_file:
        preference = json.load(json_file)
    cam = cv2.VideoCapture(preference["camera"])
    dir = os.getcwd()
    fgbg = cv2.createBackgroundSubtractorMOG2()
    height = cam.get(cv2.CAP_PROP_FRAME_HEIGHT)
    width = cam.get(cv2.CAP_PROP_FRAME_WIDTH)
    smallHeigth = int(height / preference["resize"]["height"])
    smallWidth = int(width / preference["resize"]["width"])
    fullSum = smallHeigth * smallWidth * 255
    sens = int(fullSum * preference["sense"])
    detect = 0
    while True:
        ret, framefullsize = cam.read()
        frame = cv2.resize(framefullsize, (smallWidth, smallHeigth))
        grayFull = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        grayFull = cv2.GaussianBlur(grayFull, (preference["threshold"]["gauss"], preference["threshold"]["gauss"]), 0)
        fgmask = fgbg.apply(grayFull)
        thresh = \
            cv2.threshold(fgmask, preference["threshold"]["thresh"], preference["threshold"]["maxval"],
                          cv2.THRESH_BINARY)[
                1]
        thresh = cv2.dilate(thresh, None, iterations=preference["threshold"]["dilate"])
        sum = cv2.sumElems(thresh)
        sumElement = round(sum[0])
        if sumElement > sens and detect == 0 or preference["firstRun"]:
            preference["firstRun"] = False
            detect = 1
            if preference["debug"]:
                print("CAM move detect!")
            saveDir = preference["saveFolder"]
            if not os.path.exists(dir + "/" + saveDir):
                os.makedirs(dir + "/" + saveDir)
            os.chdir(dir + "/" + saveDir)
            timestr = time.strftime(preference["strFormat"])
            filename = str(timestr + ".jpg")
            cv2.imwrite(filename, framefullsize)
            lastSendTime, lastFile, sendCount = sendImage(filename, lastFile, lastSendTime, sendCount)
        if sumElement < sens and detect == 1:
            detect = 0

        if preference["showWindows"]:
            cv2.imshow('CAM', frame)
            cv2.imshow('CAMT', thresh)
            cv2.waitKey(int(preference["waitKeyTime"]))
