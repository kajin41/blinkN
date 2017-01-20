from flask import Flask, request, render_template
import asyncio
import config
import pigpio
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

pi = pigpio.pi()


async def lightupdate():
    print("update: ", config.RED, config.GREEN, config.BLUE)
    pi.set_PWM_dutycycle(config.RED_PIN, config.RED)
    pi.set_PWM_dutycycle(config.GREEN_PIN, config.GREEN)
    pi.set_PWM_dutycycle(config.BLUE_PIN, config.BLUE)

@app.route('/')
def hello_world():
    return render_template('Home.html', r=config.RED, g=config.GREEN, b=config.BLUE)

loop = asyncio.get_event_loop()
# Blocking call which returns when the hello_world() coroutine is done


@socketio.on('change r')
def handle_my_custom_event(json):
    config.RED = int(str(json['data']))
    loop.run_until_complete(lightupdate())


@socketio.on('change g')
def handle_my_custom_event(json):
    config.GREEN = int(str(json['data']))
    loop.run_until_complete(lightupdate())


@socketio.on('change b')
def handle_my_custom_event(json):
    config.BLUE = int(str(json['data']))
    loop.run_until_complete(lightupdate())


@socketio.on('my event')
def handle_my_custom_event(json):
    print('received json: ' + str(json['data']))



if __name__ == '__main__':
    socketio.run(app)

