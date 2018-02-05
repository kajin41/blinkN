from flask import Flask, request, render_template
import multiprocessing
import config
import pigpio
import platform
from random import randint
from flask_socketio import SocketIO, emit
from time import sleep

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
async_mode = None
socketio = SocketIO(app, async_mode=async_mode)


def nullfunc():
    pass

config.MODE_THREAD = multiprocessing.Process(target=nullfunc)

pi = pigpio.pi()
freq = 12000
pi.set_PWM_frequency(config.RED_PIN, freq)
pi.set_PWM_frequency(config.GREEN_PIN, freq)
pi.set_PWM_frequency(config.BLUE_PIN, freq)


def lightupdate():
    if config.RED < 0:
        config.RED = 0
    if config.GREEN < 0:
        config.GREEN = 0
    if config.BLUE < 0:
        config.BLUE = 0
    print("update: ", config.RED, config.GREEN, config.BLUE)
    if platform.system() == 'Windows':
        return
    pi.set_PWM_dutycycle(config.RED_PIN, config.RED)
    pi.set_PWM_dutycycle(config.GREEN_PIN, config.GREEN)
    pi.set_PWM_dutycycle(config.BLUE_PIN, config.BLUE)


def modeSunset(intensity, duration):
    config.RED = intensity
    config.GREEN = intensity
    config.BLUE = intensity

    while config.RED > 0:
        lightupdate()
        sleep(duration*60/intensity)
        config.RED -= 1
        config.GREEN -= 4
        config.BLUE -= 10
    config.MODE_THREAD.terminate()


def modeStrobe(duration):
    while True:
        config.RED = 255
        config.GREEN = 255
        config.BLUE = 255
        lightupdate()
        sleep(duration/1000)
        config.RED = 0
        config.GREEN = 0
        config.BLUE = 0
        lightupdate()
        sleep(duration / 1000)
        

def modeFade(duration):
    config.RED = 255
    while True:
        for i in range(0, 256):
            config.GREEN = i
            lightupdate()
            sleep(duration/1000)
        for i in range(255, -1, -1):
            config.RED = i
            lightupdate()
            sleep(duration/1000)
        for i in range(0, 256):
            config.BLUE = i
            lightupdate()
            sleep(duration/1000)
        for i in range(255, -1, -1):
            config.GREEN = i
            lightupdate()
            sleep(duration/1000)
        for i in range(0, 256):
            config.RED = i
            lightupdate()
            sleep(duration/1000)
        for i in range(255, -1, -1):
            config.BLUE = i
            lightupdate()
            sleep(duration/1000)


def modeParty(duration):
    while True:
        i = randint(1, 9)
        if config.RED == 0 and config.GREEN == 0 and config.BLUE == 0 and i < 4:
            i = randint(4, 9)
        if i == 1:
            config.RED = 0
        elif i == 2:
            config.GREEN = 0
        elif i == 3:
            config.BLUE = 0
        elif i == 4:
            config.RED = 255
        elif i == 5:
            config.GREEN = 255
        elif i == 6:
            config.BLUE = 255
        else:
            j = randint(1, 255)
            if i == 8:
                config.GREEN = j
            elif i == 9:
                config.BLUE = j
            else:
                config.RED = j
        lightupdate()
        sleep(duration/1000)


@app.route('/')
def hello_world():
    print("ok")
    return render_template('Home.html', r=config.RED, g=config.GREEN, b=config.BLUE)


@app.route('/trigger')
def trigger():
    if config.RED > 0 or config.GREEN > 0 or config.BLUE > 0:
        config.RED = 0
        config.GREEN = 0
        config.BLUE = 0
    else:
        config.RED = 255
        config.GREEN = 255
        config.BLUE = 255
    lightupdate()
    return '200'


@app.route('/dim')
def dim():
    if config.RED > 0 or config.GREEN > 0 or config.BLUE > 0:
        config.RED = config.RED - 25
        config.GREEN = config.GREEN -25
        config.BLUE = config.BLUE
    else:
        config.RED = 0
        config.GREEN = 0
        config.BLUE = 0
    lightupdate()
    return '200'


@app.route('/dusk')
def dusk():
    config.RED = 60
    config.GREEN = 50
    config.BLUE = 40
    lightupdate()
    return '200'


@socketio.on('change r', namespace='/bl')
def handle_my_custom_event(json):
    config.RED = int(str(json['data']))
    lightupdate()


@socketio.on('change g', namespace='/bl')
def handle_my_custom_event(json):
    config.GREEN = int(str(json['data']))
    lightupdate()


@socketio.on('change b', namespace='/bl')
def handle_my_custom_event(json):
    config.BLUE = int(str(json['data']))
    lightupdate()


@socketio.on('my event', namespace='/bl')
def handle_my_custom_event(json):
    print('received json: ' + str(json['data']))


@socketio.on('modes', namespace='/bl')
def modes(json):
    if config.MODE_THREAD.is_alive():
        config.MODE_THREAD.terminate()

    if str(json['mode']) == 'stop':
        if config.MODE_THREAD.is_alive():
            config.MODE_THREAD.terminate()
            print('stoped')

    elif str(json['mode']) == 'sunset':
        config.MODE_THREAD = multiprocessing.Process(target=modeSunset, args=(int(str(json['intensity'])), int(str(json['duration'])), ))
        config.MODE_THREAD.start()
    elif str(json['mode']) == 'strobe':
        config.MODE_THREAD = multiprocessing.Process(target=modeStrobe, args=(int(str(json['duration'])), ))
        config.MODE_THREAD.start()
    elif str(json['mode']) == 'fade':
        config.MODE_THREAD = multiprocessing.Process(target=modeFade, args=(int(str(json['duration'])), ))
        config.MODE_THREAD.start()
    elif str(json['mode']) == 'party':
        config.MODE_THREAD = multiprocessing.Process(target=modeParty, args=(int(str(json['duration'])), ))
        config.MODE_THREAD.start()


if __name__ == '__main__':
    socketio.run(app)
